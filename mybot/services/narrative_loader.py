"""
Cargador de contenido narrativo desde archivos JSON.
Permite cargar y actualizar fragmentos narrativos fácilmente.
"""
import json
import os
import logging
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.narrative_models import StoryFragment, NarrativeChoice
from datetime import datetime

logger = logging.getLogger(__name__)

class NarrativeLoader:
    """Cargador de fragmentos narrativos desde archivos JSON."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def load_fragments_from_directory(self, directory_path: str = "mybot/narrative_fragments"):
        """Carga todos los fragmentos JSON de un directorio."""
        if not os.path.exists(directory_path):
            logger.warning(f"Directorio de narrativa no encontrado: {directory_path}")
            return
        
        loaded_count = 0
        for filename in os.listdir(directory_path):
            if filename.endswith('.json'):
                filepath = os.path.join(directory_path, filename)
                try:
                    await self.load_fragment_from_file(filepath)
                    loaded_count += 1
                except Exception as e:
                    logger.error(f"Error cargando {filepath}: {e}")
        
        logger.info(f"Cargados {loaded_count} fragmentos narrativos")
    
    async def load_fragment_from_file(self, filepath: str):
        """Carga fragmentos desde un archivo JSON."""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # Manejar diferentes formatos de archivo
            if isinstance(data, dict):
                if "fragments" in data:
                    # Archivo con múltiples fragmentos
                    for fragment_data in data["fragments"]:
                        await self.upsert_fragment(fragment_data)
                else:
                    # Archivo con un solo fragmento
                    await self.upsert_fragment(data)
            elif isinstance(data, list):
                # Lista de fragmentos
                for fragment_data in data:
                    await self.upsert_fragment(fragment_data)
            else:
                logger.error(f"Formato de archivo no válido en {filepath}")
                
        except Exception as e:
            logger.error(f"Error cargando fragmento desde {filepath}: {e}")
            raise
        
    async def upsert_fragment(self, fragment_data: Dict[str, Any]):
        """Inserta o actualiza un fragmento narrativo."""
        # Mapear campos del JSON a campos de la base de datos
        fragment_key = fragment_data.get('fragment_id') or fragment_data.get('key')
        if not fragment_key:
            logger.error("Fragmento sin fragment_id/key, saltando")
            return

        stmt = select(StoryFragment).where(StoryFragment.key == fragment_key)
        result = await self.session.execute(stmt)
        fragment = result.scalar_one_or_none()
        
        if fragment:
            await self._update_fragment(fragment, fragment_data)
        else:
            fragment = await self._create_fragment(fragment_data)
        
        if fragment:
            await self._process_fragment_decisions(fragment, fragment_data.get('decisions', []))

    async def _create_fragment(self, data: Dict[str, Any]) -> StoryFragment:
        """Crea un nuevo fragmento narrativo."""
        fragment_key = data.get('fragment_id') or data.get('key')
        if not fragment_key:
            logger.error("No se puede crear un fragmento sin fragment_id/key.")
            return None

        fragment = StoryFragment(
            key=fragment_key,
            text=data.get('content') or data.get('text', ''),
            character=data.get('character', 'Lucien'),
            level=data.get('level', 1),
            min_besitos=data.get('required_besitos', 0),
            required_role=data.get('required_role'),
            reward_besitos=data.get('reward_besitos', 0),
            unlocks_achievement_id=data.get('unlocks_achievement_id'),
            auto_next_fragment_key=data.get('auto_next_fragment_key')
        )
        
        self.session.add(fragment)
        await self.session.commit()
        await self.session.refresh(fragment)
        
        logger.info(f"Fragmento creado: {fragment_key}")
        return fragment

    async def _update_fragment(self, fragment: StoryFragment, data: Dict[str, Any]):
        """Actualiza un fragmento existente."""
        fragment.text = data.get('content') or data.get('text', fragment.text)
        fragment.character = data.get('character', fragment.character)
        fragment.level = data.get('level', fragment.level)
        fragment.min_besitos = data.get('required_besitos', fragment.min_besitos)
        fragment.required_role = data.get('required_role', fragment.required_role)
        fragment.reward_besitos = data.get('reward_besitos', fragment.reward_besitos)
        fragment.unlocks_achievement_id = data.get('unlocks_achievement_id', fragment.unlocks_achievement_id)
        fragment.auto_next_fragment_key = data.get('auto_next_fragment_key', fragment.auto_next_fragment_key)
        
        await self.session.commit()
        logger.info(f"Fragmento actualizado: {fragment.key}")

    async def _process_fragment_decisions(self, fragment: StoryFragment, decisions: List[Dict[str, Any]]):
        """Procesa las decisiones de un fragmento."""
        # Eliminar decisiones existentes
        stmt = select(NarrativeChoice).where(NarrativeChoice.source_fragment_id == fragment.id)
        result = await self.session.execute(stmt)
        existing_choices = result.scalars().all()
        
        for choice in existing_choices:
            await self.session.delete(choice)
        
        await self.session.commit()

        # Crear nuevas decisiones
        for decision in decisions:
            next_fragment_key = decision.get('next_fragment') or decision.get('destination_key')
            if not next_fragment_key:
                continue
            
            choice = NarrativeChoice(
                source_fragment_id=fragment.id,
                destination_fragment_key=next_fragment_key,
                text=decision.get('text', ''),
                required_besitos=decision.get('required_besitos', 0),
                required_role=decision.get('required_role')
            )
            self.session.add(choice)
        
        await self.session.commit()
    
    async def load_default_narrative(self):
        """Carga la narrativa por defecto si no existe contenido."""
        stmt = select(StoryFragment).limit(1)
        result = await self.session.execute(stmt)
        existing = result.scalars().first()
        
        if existing:
            logger.info("Ya existen fragmentos narrativos, saltando carga por defecto")
            return
        
        default_fragments = [
            {
                "fragment_id": "start",
                "content": "🎩 **Lucien:** Bienvenido, estimado viajero. Soy Lucien, mayordomo de esta mansión. Diana te esperaba... aunque debo confesar que no esperaba que llegaras tan pronto. ¿Estás preparado para descubrir lo que esta casa guarda?",
                "character": "Lucien",
                "level": 1,
                "required_besitos": 0,
                "reward_besitos": 5,
                "decisions": [
                    {
                        "text": "Estoy listo para comenzar",
                        "next_fragment": "intro_1"
                    },
                    {
                        "text": "Necesito saber más primero",
                        "next_fragment": "info_1"
                    },
                    {
                        "text": "¿Dónde está Diana?",
                        "next_fragment": "diana_question"
                    }
                ]
            },
            {
                "fragment_id": "intro_1",
                "content": "🎩 **Lucien:** Excelente. La primera regla de esta casa es simple: cada acción tiene consecuencias, cada decisión abre o cierra puertas. Tus 'besitos' son la moneda de este lugar. Gánalos, y los secretos se revelarán.",
                "character": "Lucien",
                "level": 1,
                "required_besitos": 0,
                "reward_besitos": 10,
                "decisions": [
                    {
                        "text": "¿Cómo gano besitos?",
                        "next_fragment": "besitos_guide"
                    },
                    {
                        "text": "Entiendo. ¿Qué sigue?",
                        "next_fragment": "mansion_entrance"
                    }
                ]
            },
            {
                "fragment_id": "info_1",
                "content": "🎩 **Lucien:** Prudente. Me gusta eso. Esta mansión no es como otras... aquí cada habitación cuenta una historia, cada objeto guarda un secreto. Y Diana... *sonríe misteriosamente* ...ella es el corazón de todo esto.",
                "character": "Lucien",
                "level": 1,
                "required_besitos": 0,
                "reward_besitos": 3,
                "decisions": [
                    {
                        "text": "Ahora estoy listo",
                        "next_fragment": "intro_1"
                    },
                    {
                        "text": "¿Qué tipo de secretos?",
                        "next_fragment": "secrets_1"
                    }
                ]
            },
            {
                "fragment_id": "diana_question",
                "content": "🎩 **Lucien:** *Ríe suavemente* Directo al grano, ¿eh? Diana está... presente. Siempre lo está. Pero ella prefiere observar antes de revelarse. Demuestra que eres digno de su atención, y ella aparecerá.",
                "character": "Lucien",
                "level": 1,
                "required_besitos": 0,
                "reward_besitos": 5,
                "decisions": [
                    {
                        "text": "¿Cómo puedo demostrar que soy digno?",
                        "next_fragment": "worthy_1"
                    },
                    {
                        "text": "Entiendo. Comencemos.",
                        "next_fragment": "intro_1"
                    }
                ]
            },
            {
                "fragment_id": "besitos_guide",
                "content": "🎩 **Lucien:** Los besitos se ganan de muchas formas: completando misiones, reaccionando a los mensajes de Diana, participando en el juego... Cada gesto de atención es recompensado. La generosidad de Diana no conoce límites para quienes la merecen.",
                "character": "Lucien",
                "level": 1,
                "required_besitos": 0,
                "reward_besitos": 5,
                "decisions": [
                    {
                        "text": "Perfecto. Continuemos.",
                        "next_fragment": "mansion_entrance"
                    }
                ]
            },
            {
                "fragment_id": "mansion_entrance",
                "content": "🎩 **Lucien:** Ahora, permíteme mostrarte la mansión. *Abre una puerta ornamentada* Aquí tienes tres caminos: el salón principal, donde Diana recibe a sus invitados especiales; la biblioteca, llena de secretos escritos; o el jardín, donde ella medita al atardecer.",
                "character": "Lucien",
                "level": 2,
                "required_besitos": 10,
                "reward_besitos": 8,
                "decisions": [
                    {
                        "text": "Ir al salón principal",
                        "next_fragment": "main_salon"
                    },
                    {
                        "text": "Explorar la biblioteca",
                        "next_fragment": "library_1"
                    },
                    {
                        "text": "Caminar por el jardín",
                        "next_fragment": "garden_1"
                    }
                ]
            },
            {
                "fragment_id": "main_salon",
                "content": "🎩 **Lucien:** *Te guía a un elegante salón* Este es el corazón social de la mansión. Aquí Diana ha compartido conversaciones íntimas con sus invitados más... especiales. *Señala un diván de terciopelo* Ese es su lugar favorito.",
                "character": "Lucien",
                "level": 2,
                "required_besitos": 10,
                "reward_besitos": 12,
                "decisions": [
                    {
                        "text": "Sentarme en el diván",
                        "next_fragment": "divan_experience"
                    },
                    {
                        "text": "Preguntar sobre los otros invitados",
                        "next_fragment": "other_guests"
                    },
                    {
                        "text": "Explorar otra habitación",
                        "next_fragment": "mansion_entrance"
                    }
                ]
            },
            {
                "fragment_id": "divan_experience",
                "content": "🌸 **Diana:** *Una voz suave resuena mientras te sientas* Así que has elegido mi lugar favorito... Interesante. Puedo sentir tu presencia, tu curiosidad. Dime, ¿qué es lo que realmente buscas en mi mundo?",
                "character": "Diana",
                "level": 3,
                "required_besitos": 25,
                "reward_besitos": 20,
                "decisions": [
                    {
                        "text": "Te busco a ti",
                        "next_fragment": "diana_response_seek"
                    },
                    {
                        "text": "Busco experiencias nuevas",
                        "next_fragment": "diana_response_experience"
                    },
                    {
                        "text": "Busco entender este lugar",
                        "next_fragment": "diana_response_understand"
                    }
                ]
            },
            {
                "fragment_id": "diana_response_seek",
                "content": "🌸 **Diana:** *Su risa es como música* Me buscas... Muchos lo hacen, pero pocos entienden lo que eso significa. Buscarme no es solo encontrarme, es estar dispuesto a perderte en el proceso. ¿Estás preparado para eso?",
                "character": "Diana",
                "level": 3,
                "required_besitos": 25,
                "reward_besitos": 25,
                "required_role": "vip",
                "decisions": [
                    {
                        "text": "Estoy preparado para todo",
                        "next_fragment": "vip_deep_1"
                    },
                    {
                        "text": "Necesito pensarlo más",
                        "next_fragment": "diana_patience"
                    }
                ]
            },
            {
                "fragment_id": "vip_deep_1",
                "content": "🌸 **Diana:** *Su voz se vuelve más íntima* Entonces sígueme más allá del velo... *El ambiente cambia, se vuelve más cálido, más personal* Aquí, en mi espacio más privado, puedo mostrarte quién soy realmente. Pero esto es solo para quienes han demostrado su devoción.",
                "character": "Diana",
                "level": 4,
                "required_besitos": 50,
                "required_role": "vip",
                "reward_besitos": 30,
                "decisions": [
                    {
                        "text": "Quiero conocerte completamente",
                        "next_fragment": "vip_intimate_1"
                    },
                    {
                        "text": "Cuéntame tus secretos",
                        "next_fragment": "vip_secrets_1"
                    }
                ]
            }
        ]
        
        for fragment_data in default_fragments:
            await self.upsert_fragment(fragment_data)
        
        logger.info("Narrativa por defecto cargada exitosamente")
