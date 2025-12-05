"""
Servicio para validación de integridad referencial
Valida que las referencias entre entidades sean válidas antes de crear/actualizar
"""
import sys
from pathlib import Path

# Añadir ruta del bot al PYTHONPATH
BOT_PATH = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BOT_PATH))

from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional, Dict, List, Tuple
import logging

# Importar modelos
from database.models import User, ShopItem
from database.narrative_models import StoryFragment, NarrativeChoice
from database.automation_models import AutomationTrigger, TriggerAction

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Error de validación personalizado"""
    def __init__(self, message: str, field: str = None, code: str = None):
        self.message = message
        self.field = field
        self.code = code
        super().__init__(self.message)
    
    def to_dict(self):
        """Convierte el error a diccionario para respuestas JSON"""
        return {
            'message': self.message,
            'field': self.field,
            'code': self.code
        }


class ValidationService:
    """
    Servicio para validar integridad referencial entre entidades
    
    Uso:
        validator = ValidationService(db_session)
        validator.validate_product_exists(product_id)
        validator.validate_fragment_key_unique("CAP10_INTRO")
    """
    
    def __init__(self, db_session: Session):
        """
        Args:
            db_session: Sesión de SQLAlchemy para queries
        """
        self.db = db_session
    
    # ==================== VALIDACIONES DE PRODUCTOS ====================
    
    def validate_product_exists(self, product_id: int) -> ShopItem:
        """
        Valida que un producto exista en la base de datos
        
        Args:
            product_id: ID del producto a validar
        
        Returns:
            ShopItem si existe
        
        Raises:
            ValidationError si no existe
        """
        if product_id is None:
            raise ValidationError(
                message="Product ID cannot be None",
                field="product_id",
                code="REQUIRED_FIELD"
            )
        
        product = self.db.get(ShopItem, product_id)
        
        if not product:
            raise ValidationError(
                message=f"Product with ID {product_id} does not exist",
                field="product_id",
                code="PRODUCT_NOT_FOUND"
            )
        
        logger.info(f"✓ Product {product_id} exists: {product.name}")
        return product
    
    def validate_product_name_unique(self, name: str, exclude_id: Optional[int] = None) -> bool:
        """
        Valida que el nombre de un producto sea único
        
        Args:
            name: Nombre del producto a validar
            exclude_id: ID a excluir de la validación (para updates)
        
        Returns:
            True si es único
        
        Raises:
            ValidationError si ya existe
        """
        query = select(ShopItem).where(ShopItem.name == name)
        
        if exclude_id:
            query = query.where(ShopItem.id != exclude_id)
        
        existing = self.db.execute(query).scalar_one_or_none()
        
        if existing:
            raise ValidationError(
                message=f"A product with name '{name}' already exists (ID: {existing.id})",
                field="name",
                code="DUPLICATE_NAME"
            )
        
        return True
    
    # ==================== VALIDACIONES DE FRAGMENTOS ====================
    
    def validate_fragment_exists(self, fragment_key: str) -> StoryFragment:
        """
        Valida que un fragmento exista por su key
        
        Args:
            fragment_key: Key del fragmento (ej: "CAP10_INTRO")
        
        Returns:
            StoryFragment si existe
        
        Raises:
            ValidationError si no existe
        """
        if not fragment_key:
            raise ValidationError(
                message="Fragment key cannot be empty",
                field="fragment_key",
                code="REQUIRED_FIELD"
            )
        
        fragment = self.db.execute(
            select(StoryFragment).where(StoryFragment.key == fragment_key)
        ).scalar_one_or_none()
        
        if not fragment:
            raise ValidationError(
                message=f"Fragment with key '{fragment_key}' does not exist",
                field="fragment_key",
                code="FRAGMENT_NOT_FOUND"
            )
        
        logger.info(f"✓ Fragment '{fragment_key}' exists (ID: {fragment.id})")
        return fragment
    
    def validate_fragment_key_unique(self, fragment_key: str, exclude_id: Optional[int] = None) -> bool:
        """
        Valida que la key de un fragmento sea única
        
        Args:
            fragment_key: Key a validar
            exclude_id: ID a excluir de la validación (para updates)
        
        Returns:
            True si es única
        
        Raises:
            ValidationError si ya existe
        """
        if not fragment_key:
            raise ValidationError(
                message="Fragment key cannot be empty",
                field="fragment_key",
                code="REQUIRED_FIELD"
            )
        
        # Validar formato: solo letras, números, guiones y guiones bajos
        import re
        if not re.match(r'^[A-Z0-9_-]+$', fragment_key):
            raise ValidationError(
                message="Fragment key must contain only uppercase letters, numbers, hyphens and underscores",
                field="fragment_key",
                code="INVALID_FORMAT"
            )
        
        query = select(StoryFragment).where(StoryFragment.key == fragment_key)
        
        if exclude_id:
            query = query.where(StoryFragment.id != exclude_id)
        
        existing = self.db.execute(query).scalar_one_or_none()
        
        if existing:
            raise ValidationError(
                message=f"A fragment with key '{fragment_key}' already exists (ID: {existing.id})",
                field="fragment_key",
                code="DUPLICATE_KEY"
            )
        
        return True
    
    def validate_fragment_references(self, data: Dict) -> Dict:
        """
        Valida todas las referencias en los datos de un fragmento
        
        Args:
            data: Diccionario con datos del fragmento
                {
                    "unlock_product_id": 42,
                    "auto_next_fragment_key": "CAP10_NEXT",
                    "choices": [
                        {"destination_fragment_key": "CAP10_CHOICE_A"}
                    ]
                }
        
        Returns:
            Dict con entidades validadas
        
        Raises:
            ValidationError si alguna referencia es inválida
        """
        validated = {}
        
        # Validar producto de desbloqueo
        if data.get('unlock_product_id'):
            validated['unlock_product'] = self.validate_product_exists(
                data['unlock_product_id']
            )
        
        # Validar siguiente fragmento automático
        if data.get('auto_next_fragment_key'):
            validated['auto_next_fragment'] = self.validate_fragment_exists(
                data['auto_next_fragment_key']
            )
        
        # Validar destinos de decisiones
        if data.get('choices'):
            validated['choice_destinations'] = []
            for i, choice in enumerate(data['choices']):
                if choice.get('destination_fragment_key'):
                    try:
                        dest = self.validate_fragment_exists(
                            choice['destination_fragment_key']
                        )
                        validated['choice_destinations'].append(dest)
                    except ValidationError as e:
                        # Añadir índice al error
                        e.field = f"choices[{i}].destination_fragment_key"
                        raise
        
        return validated
    
    # ==================== VALIDACIONES DE TRIGGERS ====================
    
    def validate_trigger_name_unique(self, name: str, exclude_id: Optional[int] = None) -> bool:
        """
        Valida que el nombre de un trigger sea único
        
        Args:
            name: Nombre del trigger
            exclude_id: ID a excluir (para updates)
        
        Returns:
            True si es único
        
        Raises:
            ValidationError si ya existe
        """
        if not name or len(name) < 3:
            raise ValidationError(
                message="Trigger name must be at least 3 characters long",
                field="name",
                code="INVALID_LENGTH"
            )
        
        query = select(AutomationTrigger).where(AutomationTrigger.name == name)
        if exclude_id:
            query = query.where(AutomationTrigger.id != exclude_id)
        
        existing = self.db.execute(query).scalar_one_or_none()
        
        if existing:
            raise ValidationError(
                message=f"A trigger with name '{name}' already exists (ID: {existing.id})",
                field="name",
                code="DUPLICATE_NAME"
            )
        
        return True
    
    def validate_trigger_event_type(self, event_type: str) -> bool:
        """
        Valida que el tipo de evento de trigger sea válido
        
        Args:
            event_type: Tipo de evento (ej: 'FRAGMENT_VIEWED')
        
        Returns:
            True si es válido
        
        Raises:
            ValidationError si es inválido
        """
        VALID_EVENT_TYPES = [
            'FRAGMENT_VIEWED',
            'PRODUCT_PURCHASED',
            'MISSION_COMPLETED',
            'USER_CREATED',
            'POINTS_THRESHOLD',
            'LEVEL_UP'
        ]
        
        if event_type not in VALID_EVENT_TYPES:
            raise ValidationError(
                message=f"Invalid trigger event type. Must be one of: {', '.join(VALID_EVENT_TYPES)}",
                field="trigger_event_type",
                code="INVALID_EVENT_TYPE"
            )
        
        return True
    
    def validate_trigger_references(self, data: Dict) -> Dict:
        """
        Valida referencias en datos de un trigger según su tipo
        
        Args:
            data: Diccionario con datos del trigger
                {
                    "trigger_event_type": "FRAGMENT_VIEWED",
                    "fragment_key": "CAP10_FINAL",
                    "product_id": None,
                    "mission_id": None
                }
        
        Returns:
            Dict con entidades validadas
        
        Raises:
            ValidationError si referencias son inválidas o faltan campos requeridos
        """
        validated = {}
        event_type = data.get('trigger_event_type')
        
        # Validar tipo de evento
        self.validate_trigger_event_type(event_type)
        
        # Validar campos requeridos según tipo de evento
        if event_type == 'FRAGMENT_VIEWED':
            if not data.get('fragment_key'):
                raise ValidationError(
                    message="FRAGMENT_VIEWED trigger requires fragment_key",
                    field="fragment_key",
                    code="REQUIRED_FIELD"
                )
            validated['fragment'] = self.validate_fragment_exists(data['fragment_key'])
        
        elif event_type == 'PRODUCT_PURCHASED':
            if not data.get('product_id'):
                raise ValidationError(
                    message="PRODUCT_PURCHASED trigger requires product_id",
                    field="product_id",
                    code="REQUIRED_FIELD"
                )
            validated['product'] = self.validate_product_exists(data['product_id'])
        
        elif event_type == 'MISSION_COMPLETED':
            if not data.get('mission_id'):
                raise ValidationError(
                    message="MISSION_COMPLETED trigger requires mission_id",
                    field="mission_id",
                    code="REQUIRED_FIELD"
                )
            # TODO: Validar que la misión existe cuando el modelo Mission esté disponible
            # validated['mission'] = self.validate_mission_exists(data['mission_id'])
        
        elif event_type == 'POINTS_THRESHOLD':
            if not data.get('points_threshold') or data['points_threshold'] <= 0:
                raise ValidationError(
                    message="POINTS_THRESHOLD trigger requires positive points_threshold",
                    field="points_threshold",
                    code="INVALID_VALUE"
                )
        
        elif event_type == 'LEVEL_UP':
            if not data.get('level_threshold') or data['level_threshold'] <= 0:
                raise ValidationError(
                    message="LEVEL_UP trigger requires positive level_threshold",
                    field="level_threshold",
                    code="INVALID_VALUE"
                )
        
        return validated
    
    def validate_action_type(self, action_type: str) -> bool:
        """
        Valida que el tipo de acción sea válido
        
        Args:
            action_type: Tipo de acción (ej: 'GIVE_PRODUCT')
        
        Returns:
            True si es válido
        
        Raises:
            ValidationError si es inválido
        """
        VALID_ACTION_TYPES = [
            'GIVE_PRODUCT',
            'GRANT_VIP',
            'UNLOCK_FRAGMENT',
            'UNLOCK_LORE',
            'ADD_POINTS',
            'SUBTRACT_POINTS',
            'SEND_MESSAGE',
            'SET_ROLE',
            'ADD_TO_GROUP',
            'COMPLETE_MISSION'
        ]
        
        if action_type not in VALID_ACTION_TYPES:
            raise ValidationError(
                message=f"Invalid action type. Must be one of: {', '.join(VALID_ACTION_TYPES)}",
                field="action_type",
                code="INVALID_ACTION_TYPE"
            )
        
        return True
    
    def validate_action_references(self, data: Dict) -> Dict:
        """
        Valida referencias en datos de una acción según su tipo
        
        Args:
            data: Diccionario con datos de la acción
                {
                    "action_type": "GIVE_PRODUCT",
                    "product_id": 42,
                    "amount": None
                }
        
        Returns:
            Dict con entidades validadas
        
        Raises:
            ValidationError si referencias son inválidas o faltan campos requeridos
        """
        validated = {}
        action_type = data.get('action_type')
        
        # Validar tipo de acción
        self.validate_action_type(action_type)
        
        # Validar campos requeridos según tipo de acción
        if action_type == 'GIVE_PRODUCT':
            if not data.get('product_id'):
                raise ValidationError(
                    message="GIVE_PRODUCT action requires product_id",
                    field="product_id",
                    code="REQUIRED_FIELD"
                )
            validated['product'] = self.validate_product_exists(data['product_id'])
        
        elif action_type == 'UNLOCK_FRAGMENT':
            if not data.get('fragment_key'):
                raise ValidationError(
                    message="UNLOCK_FRAGMENT action requires fragment_key",
                    field="fragment_key",
                    code="REQUIRED_FIELD"
                )
            validated['fragment'] = self.validate_fragment_exists(data['fragment_key'])
        
        elif action_type == 'UNLOCK_LORE':
            if not data.get('lore_piece_id'):
                raise ValidationError(
                    message="UNLOCK_LORE action requires lore_piece_id",
                    field="lore_piece_id",
                    code="REQUIRED_FIELD"
                )
            # TODO: Validar que el lore existe cuando el modelo esté disponible
            # validated['lore'] = self.validate_lore_exists(data['lore_piece_id'])
        
        elif action_type in ['GRANT_VIP', 'ADD_POINTS', 'SUBTRACT_POINTS']:
            if not data.get('amount') or data['amount'] <= 0:
                raise ValidationError(
                    message=f"{action_type} action requires positive amount",
                    field="amount",
                    code="INVALID_VALUE"
                )
        
        elif action_type == 'SEND_MESSAGE':
            if not data.get('message_template'):
                raise ValidationError(
                    message="SEND_MESSAGE action requires message_template",
                    field="message_template",
                    code="REQUIRED_FIELD"
                )
            # Validar que el template no esté vacío
            if not data['message_template'].strip():
                raise ValidationError(
                    message="message_template cannot be empty",
                    field="message_template",
                    code="INVALID_VALUE"
                )
        
        elif action_type == 'SET_ROLE':
            if not data.get('role_name'):
                raise ValidationError(
                    message="SET_ROLE action requires role_name",
                    field="role_name",
                    code="REQUIRED_FIELD"
                )
            # Validar que el rol sea válido
            VALID_ROLES = ['free', 'vip', 'admin']
            if data['role_name'] not in VALID_ROLES:
                raise ValidationError(
                    message=f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}",
                    field="role_name",
                    code="INVALID_VALUE"
                )
        
        return validated
    
    # ==================== VALIDACIONES DE USUARIOS ====================
    
    def validate_user_exists(self, user_id: int) -> User:
        """
        Valida que un usuario exista
        
        Args:
            user_id: ID del usuario (Telegram ID)
        
        Returns:
            User si existe
        
        Raises:
            ValidationError si no existe
        """
        user = self.db.get(User, user_id)
        
        if not user:
            raise ValidationError(
                message=f"User with ID {user_id} does not exist",
                field="user_id",
                code="USER_NOT_FOUND"
            )
        
        return user
    
    # ==================== VALIDACIONES BATCH ====================
    
    def validate_multiple_products(self, product_ids: List[int]) -> List[ShopItem]:
        """
        Valida que múltiples productos existan
        
        Args:
            product_ids: Lista de IDs de productos
        
        Returns:
            Lista de ShopItem validados
        
        Raises:
            ValidationError si alguno no existe (especifica cuál)
        """
        validated = []
        
        for product_id in product_ids:
            try:
                product = self.validate_product_exists(product_id)
                validated.append(product)
            except ValidationError as e:
                # Re-lanzar con contexto adicional
                e.message = f"Product validation failed at index {len(validated)}: {e.message}"
                raise
        
        return validated
    
    def validate_multiple_fragments(self, fragment_keys: List[str]) -> List[StoryFragment]:
        """
        Valida que múltiples fragmentos existan
        
        Args:
            fragment_keys: Lista de keys de fragmentos
        
        Returns:
            Lista de StoryFragment validados
        
        Raises:
            ValidationError si alguno no existe (especifica cuál)
        """
        validated = []
        
        for fragment_key in fragment_keys:
            try:
                fragment = self.validate_fragment_exists(fragment_key)
                validated.append(fragment)
            except ValidationError as e:
                e.message = f"Fragment validation failed at index {len(validated)}: {e.message}"
                raise
        
        return validated
    
    # ==================== VALIDACIONES COMPLEJAS ====================
    
    def validate_nested_fragment_creation(self, data: Dict) -> Tuple[Dict, List[str]]:
        """
        Valida datos completos para creación nested de fragmento + producto
        
        Args:
            data: Diccionario con todos los datos
                {
                    "key": "CAP10_INTRO",
                    "text": "...",
                    "unlock_product_id": 42,  # O unlock_product: {...}
                    "choices": [...]
                }
        
        Returns:
            Tupla (validated_data, warnings)
            - validated_data: Dict con entidades validadas
            - warnings: Lista de advertencias no críticas
        
        Raises:
            ValidationError si hay errores críticos
        """
        validated = {}
        warnings = []
        
        # 1. Validar key del fragmento
        try:
            self.validate_fragment_key_unique(data['key'])
            validated['fragment_key_valid'] = True
        except ValidationError:
            raise
        
        # 2. Validar producto (si es referencia)
        if data.get('unlock_product_id'):
            try:
                validated['unlock_product'] = self.validate_product_exists(
                    data['unlock_product_id']
                )
            except ValidationError:
                raise
        
        # 3. Validar producto nested (si se crea nuevo)
        if data.get('unlock_product'):
            product_data = data['unlock_product']
            
            # Validar que tenga campos mínimos
            if not product_data.get('name'):
                raise ValidationError(
                    message="Nested product requires name",
                    field="unlock_product.name",
                    code="REQUIRED_FIELD"
                )
            
            if product_data.get('price') is None or product_data['price'] < 0:
                raise ValidationError(
                    message="Nested product requires non-negative price",
                    field="unlock_product.price",
                    code="INVALID_VALUE"
                )
            
            # Validar unicidad del nombre
            try:
                self.validate_product_name_unique(product_data['name'])
                validated['nested_product_valid'] = True
            except ValidationError:
                # Si el nombre está duplicado, es error crítico
                raise
        
        # 4. Validar que no haya ambos (referencia y nested)
        if data.get('unlock_product_id') and data.get('unlock_product'):
            raise ValidationError(
                message="Cannot specify both unlock_product_id and unlock_product",
                field="unlock_product",
                code="CONFLICTING_FIELDS"
            )
        
        # 5. Validar choices
        if data.get('choices'):
            for i, choice in enumerate(data['choices']):
                # Cada choice debe tener destination
                if not choice.get('destination_fragment_key') and not choice.get('destination_fragment'):
                    raise ValidationError(
                        message=f"Choice at index {i} requires destination_fragment_key or destination_fragment",
                        field=f"choices[{i}]",
                        code="REQUIRED_FIELD"
                    )
                
                # Si es referencia, validar que exista
                if choice.get('destination_fragment_key'):
                    try:
                        self.validate_fragment_exists(choice['destination_fragment_key'])
                    except ValidationError as e:
                        e.field = f"choices[{i}].destination_fragment_key"
                        raise
                
                # Si es nested, validar key
                if choice.get('destination_fragment'):
                    dest_key = choice['destination_fragment'].get('key')
                    if not dest_key:
                        raise ValidationError(
                            message="Nested destination fragment requires key",
                            field=f"choices[{i}].destination_fragment.key",
                            code="REQUIRED_FIELD"
                        )
                    
                    try:
                        self.validate_fragment_key_unique(dest_key)
                    except ValidationError as e:
                        e.field = f"choices[{i}].destination_fragment.key"
                        raise
        
        # 6. Advertencias no críticas
        if not data.get('text') or len(data['text'].strip()) < 10:
            warnings.append("Fragment text is very short (less than 10 characters)")
        
        if data.get('choices') and len(data['choices']) > 5:
            warnings.append(f"Fragment has many choices ({len(data['choices'])}). Consider splitting into multiple fragments.")
        
        if data.get('min_besitos', 0) > 1000:
            warnings.append(f"Fragment requires high amount of points ({data['min_besitos']}). Verify this is intentional.")
        
        return validated, warnings
    
    def validate_nested_trigger_creation(self, data: Dict) -> Tuple[Dict, List[str]]:
        """
        Valida datos completos para creación nested de trigger + acciones
        
        Args:
            data: Diccionario con todos los datos
                {
                    "name": "Welcome Gift",
                    "trigger_event_type": "USER_CREATED",
                    "actions": [
                        {"action_type": "GIVE_PRODUCT", "product_id": 42}
                    ]
                }
        
        Returns:
            Tupla (validated_data, warnings)
        
        Raises:
            ValidationError si hay errores críticos
        """
        validated = {}
        warnings = []
        
        # 1. Validar nombre del trigger
        try:
            self.validate_trigger_name_unique(data['name'])
            validated['trigger_name_valid'] = True
        except ValidationError:
            raise
        
        # 2. Validar referencias del trigger
        try:
            trigger_refs = self.validate_trigger_references(data)
            validated.update(trigger_refs)
        except ValidationError:
            raise
        
        # 3. Validar que tenga al menos una acción
        if not data.get('actions') or len(data['actions']) == 0:
            raise ValidationError(
                message="Trigger must have at least one action",
                field="actions",
                code="REQUIRED_FIELD"
            )
        
        # 4. Validar cada acción
        validated['actions'] = []
        for i, action in enumerate(data['actions']):
            try:
                action_refs = self.validate_action_references(action)
                validated['actions'].append(action_refs)
            except ValidationError as e:
                e.field = f"actions[{i}].{e.field}" if e.field else f"actions[{i}]"
                raise
        
        # 5. Advertencias
        if len(data['actions']) > 10:
            warnings.append(f"Trigger has many actions ({len(data['actions'])}). Consider splitting into multiple triggers.")
        
        if data.get('conditions') and data['conditions'].get('max_activations') == 1:
            warnings.append("Trigger is configured for single use (max_activations=1)")
        
        return validated, warnings


# ==================== FUNCIONES HELPER ====================

def handle_validation_error(error: ValidationError) -> Dict:
    """
    Convierte ValidationError en respuesta JSON estándar
    
    Args:
        error: ValidationError capturado
    
    Returns:
        Dict con estructura de error para API
    """
    return {
        'success': False,
        'error': error.message,
        'field': error.field,
        'code': error.code
    }
