"""
Modelos para sistema de automatización configurable
Permite crear triggers y acciones sin modificar código
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.base import Base  # Importar Base existente del bot


class AutomationTrigger(Base):
    """
    Trigger configurable que se ejecuta automáticamente cuando ocurre un evento
    
    Ejemplos:
    - Trigger: Usuario ve fragmento "CAP10_FINAL" → Acción: Dar producto ID 42
    - Trigger: Usuario completa misión ID 5 → Acción: Otorgar 3 días VIP
    - Trigger: Usuario se registra → Acción: Enviar mensaje bienvenida
    """
    __tablename__ = 'automation_triggers'
    
    # Identificación
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    enabled = Column(Boolean, default=True, nullable=False, index=True)
    
    # Tipo de evento que dispara el trigger
    trigger_event_type = Column(String(50), nullable=False, index=True)
    # Valores posibles:
    # - 'FRAGMENT_VIEWED': Cuando usuario ve un fragmento específico
    # - 'PRODUCT_PURCHASED': Cuando usuario compra un producto
    # - 'MISSION_COMPLETED': Cuando usuario completa una misión
    # - 'USER_CREATED': Cuando se registra un nuevo usuario
    # - 'POINTS_THRESHOLD': Cuando usuario alcanza X puntos
    # - 'LEVEL_UP': Cuando usuario sube de nivel
    
    # Referencias opcionales según el tipo de trigger
    # (Solo una será usada dependiendo del trigger_event_type)
    fragment_key = Column(String(50), nullable=True, index=True)
    mission_id = Column(Integer, nullable=True, index=True)
    product_id = Column(Integer, nullable=True, index=True)
    points_threshold = Column(Integer, nullable=True)
    level_threshold = Column(Integer, nullable=True)
    
    # Condiciones adicionales (JSON)
    # Estructura ejemplo:
    # {
    #   "user_role": "free",           # Solo para usuarios con rol específico
    #   "min_points": 100,             # Usuario debe tener al menos X puntos
    #   "first_time_only": true,       # Solo la primera vez que ocurre
    #   "max_activations": 1,          # Máximo de veces que se puede activar por usuario
    #   "cooldown_hours": 24           # Tiempo mínimo entre activaciones
    # }
    conditions = Column(JSON, nullable=True)
    
    # Estadísticas
    total_activations = Column(Integer, default=0, nullable=False)
    last_activated_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relaciones
    actions = relationship(
        "TriggerAction",
        back_populates="trigger",
        cascade="all, delete-orphan",
        order_by="TriggerAction.execution_order"
    )
    
    execution_logs = relationship(
        "TriggerExecutionLog",
        back_populates="trigger",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<AutomationTrigger(id={self.id}, name='{self.name}', enabled={self.enabled})>"
    
    def to_dict(self):
        """Serializa el trigger a diccionario"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'enabled': self.enabled,
            'trigger_event_type': self.trigger_event_type,
            'fragment_key': self.fragment_key,
            'mission_id': self.mission_id,
            'product_id': self.product_id,
            'points_threshold': self.points_threshold,
            'level_threshold': self.level_threshold,
            'conditions': self.conditions,
            'total_activations': self.total_activations,
            'last_activated_at': self.last_activated_at.isoformat() if self.last_activated_at else None,
            'actions_count': len(self.actions),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class TriggerAction(Base):
    """
    Acción a ejecutar cuando se dispara un trigger
    Un trigger puede tener múltiples acciones que se ejecutan en orden
    
    Ejemplos:
    - Acción: GIVE_PRODUCT con product_id=42
    - Acción: GRANT_VIP con amount=7 (días)
    - Acción: ADD_POINTS con amount=100
    - Acción: SEND_MESSAGE con message_template="¡Felicidades!"
    """
    __tablename__ = 'trigger_actions'
    
    # Identificación
    id = Column(Integer, primary_key=True, autoincrement=True)
    trigger_id = Column(Integer, ForeignKey('automation_triggers.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Tipo de acción
    action_type = Column(String(50), nullable=False)
    # Valores posibles:
    # - 'GIVE_PRODUCT': Añadir producto al inventario del usuario
    # - 'GRANT_VIP': Otorgar días de VIP
    # - 'UNLOCK_FRAGMENT': Desbloquear un fragmento narrativo
    # - 'UNLOCK_LORE': Desbloquear una pieza de lore
    # - 'ADD_POINTS': Añadir puntos (besitos)
    # - 'SUBTRACT_POINTS': Restar puntos
    # - 'SEND_MESSAGE': Enviar mensaje de Telegram al usuario
    # - 'SET_ROLE': Cambiar rol del usuario
    # - 'ADD_TO_GROUP': Añadir usuario a un grupo/canal
    # - 'COMPLETE_MISSION': Marcar misión como completada
    
    # Parámetros según el tipo de acción (solo uno será usado)
    product_id = Column(Integer, nullable=True, index=True)
    fragment_key = Column(String(50), nullable=True, index=True)
    lore_piece_id = Column(Integer, nullable=True, index=True)
    mission_id = Column(Integer, nullable=True, index=True)
    amount = Column(Integer, nullable=True)  # Para points, VIP days, etc.
    role_name = Column(String(50), nullable=True)  # Para SET_ROLE
    group_id = Column(String(50), nullable=True)  # Para ADD_TO_GROUP
    
    # Mensaje personalizado (para SEND_MESSAGE)
    # Soporta variables: {user_name}, {user_id}, {points}, etc.
    message_template = Column(Text, nullable=True)
    
    # Orden de ejecución (menor = primero)
    execution_order = Column(Integer, default=0, nullable=False)
    
    # Metadata adicional (JSON) para acciones complejas
    # Estructura flexible para futuros tipos de acciones
    action_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relaciones
    trigger = relationship("AutomationTrigger", back_populates="actions")
    
    def __repr__(self):
        return f"<TriggerAction(id={self.id}, type='{self.action_type}', trigger_id={self.trigger_id})>"
    
    def to_dict(self):
        """Serializa la acción a diccionario"""
        return {
            'id': self.id,
            'trigger_id': self.trigger_id,
            'action_type': self.action_type,
            'product_id': self.product_id,
            'fragment_key': self.fragment_key,
            'lore_piece_id': self.lore_piece_id,
            'mission_id': self.mission_id,
            'amount': self.amount,
            'role_name': self.role_name,
            'group_id': self.group_id,
            'message_template': self.message_template,
            'execution_order': self.execution_order,
            'action_metadata': self.action_metadata,
            'created_at': self.created_at.isoformat()
        }


class TriggerExecutionLog(Base):
    """
    Log de ejecuciones de triggers para auditoría y debugging
    Registra cada vez que un trigger se ejecuta (o falla)
    """
    __tablename__ = 'trigger_execution_logs'
    
    # Identificación
    id = Column(Integer, primary_key=True, autoincrement=True)
    trigger_id = Column(Integer, ForeignKey('automation_triggers.id', ondelete='SET NULL'), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Resultado de la ejecución
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Detalles de ejecución
    actions_executed = Column(Integer, default=0, nullable=False)
    execution_time_ms = Column(Integer, nullable=True)  # Tiempo de ejecución en milisegundos
    
    # Contexto de la ejecución (JSON)
    # Guarda el estado relevante al momento de ejecución
    context = Column(JSON, nullable=True)
    
    # Timestamp
    executed_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    
    # Relaciones
    trigger = relationship("AutomationTrigger", back_populates="execution_logs")
    
    def __repr__(self):
        status = "✓" if self.success else "✗"
        return f"<TriggerExecutionLog(id={self.id}, trigger_id={self.trigger_id}, success={status})>"
    
    def to_dict(self):
        """Serializa el log a diccionario"""
        return {
            'id': self.id,
            'trigger_id': self.trigger_id,
            'user_id': self.user_id,
            'success': self.success,
            'error_message': self.error_message,
            'actions_executed': self.actions_executed,
            'execution_time_ms': self.execution_time_ms,
            'context': self.context,
            'executed_at': self.executed_at.isoformat()
        }
