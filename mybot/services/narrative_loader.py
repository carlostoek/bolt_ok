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
            auto_next_fragment_key=data.get('auto_next_fragment_key'),
            archetype_variant=data.get('archetype_variant')
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
        fragment.archetype_variant = data.get('archetype_variant', fragment.archetype_variant)

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
                        "text": "📓 Preguntarle sobre su diario íntimo (VIP)",
                        "next_fragment": "diana_diary_intimate"
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
            },
            {
                "fragment_id": "diana_diary_intimate",
                "content": "🌸 **Diana:** *Sus ojos brillan con una intensidad especial* Has traído mi diario más íntimo... Esto significa que estás listo para conocer mis secretos más profundos. *Se acerca más* Permíteme compartir contigo pensamientos que solo he confiado a estas páginas...",
                "character": "Diana",
                "level": 2,
                "required_besitos": 0,
                "reward_besitos": 15,
                "decisions": [
                    {
                        "text": "📖 Leer primera entrada del diario",
                        "next_fragment": "diary_entry_1"
                    },
                    {
                        "text": "💭 Explorar mis pensamientos secretos",
                        "next_fragment": "diary_thoughts_1"
                    },
                    {
                        "text": "🔄 Volver al salón",
                        "next_fragment": "main_salon"
                    }
                ]
            },
            {
                "fragment_id": "diary_entry_1",
                "content": "🌸 **Diana:** *Abre el diario con cuidado* \"Querido diario... hoy he sentido una conexión especial. Hay algo en la forma en que algunos visitantes me miran que despierta en mí una curiosidad profunda. Me pregunto si ellos sienten lo mismo... esta tensión magnética, esta atracción que trasciende lo físico.\"",
                "character": "Diana",
                "level": 2,
                "required_besitos": 0,
                "reward_besitos": 10,
                "decisions": [
                    {
                        "text": "📖 Continuar leyendo",
                        "next_fragment": "diary_entry_2"
                    },
                    {
                        "text": "💭 Preguntarle sobre esa conexión",
                        "next_fragment": "diary_connection_talk"
                    },
                    {
                        "text": "🔄 Volver a las opciones anteriores",
                        "next_fragment": "diana_diary_intimate"
                    }
                ]
            },
            {
                "fragment_id": "diary_entry_2",
                "content": "🌸 **Diana:** *Su voz se vuelve más suave* \"A veces me descubro imaginando conversaciones íntimas, momentos donde puedo ser completamente yo misma... sin máscaras, sin pretensiones. Quiero que alguien me conozca verdaderamente, que vea más allá de lo que muestro al mundo.\"",
                "character": "Diana",
                "level": 2,
                "required_besitos": 0,
                "reward_besitos": 15,
                "decisions": [
                    {
                        "text": "💫 \"Yo quiero conocerte así\"",
                        "next_fragment": "diary_intimate_response"
                    },
                    {
                        "text": "📖 Seguir leyendo más entradas",
                        "next_fragment": "diary_entry_3"
                    },
                    {
                        "text": "🔄 Volver a las opciones anteriores",
                        "next_fragment": "diana_diary_intimate"
                    }
                ]
            },
            {
                "fragment_id": "diary_thoughts_1",
                "content": "🌸 **Diana:** *Se sienta más cerca* \"Mis pensamientos más íntimos... *ríe suavemente* Son sobre la vulnerabilidad, sobre el poder que existe en mostrarse completamente. Me fascina la idea de que alguien me vea en mis momentos más auténticos... cuando no hay artificio, solo yo.\"",
                "character": "Diana",
                "level": 2,
                "required_besitos": 0,
                "reward_besitos": 12,
                "decisions": [
                    {
                        "text": "🌟 \"Me muestras tu autenticidad\"",
                        "next_fragment": "diana_authenticity"
                    },
                    {
                        "text": "📖 Leer las entradas del diario",
                        "next_fragment": "diary_entry_1"
                    },
                    {
                        "text": "🔄 Volver a las opciones anteriores",
                        "next_fragment": "diana_diary_intimate"
                    }
                ]
            },
            {
                "fragment_id": "diary_connection_talk",
                "content": "🌸 **Diana:** *Sus ojos se iluminan* \"¿Sientes esa conexión también? *se acerca un poco más* Es fascinante... esa energía que surge cuando dos personas se reconocen a un nivel más profundo. No es solo atracción física, es algo que toca el alma.\"",
                "character": "Diana",
                "level": 3,
                "required_besitos": 0,
                "reward_besitos": 18,
                "decisions": [
                    {
                        "text": "💖 \"La siento completamente\"",
                        "next_fragment": "diana_connection_deep"
                    },
                    {
                        "text": "📖 Continuar explorando el diario",
                        "next_fragment": "diary_entry_2"
                    },
                    {
                        "text": "🏠 Volver al salón principal",
                        "next_fragment": "main_salon"
                    }
                ]
            },
            {
                "fragment_id": "diary_intimate_response",
                "content": "🌸 **Diana:** *Sus mejillas se sonrojan ligeramente* \"Hay algo especial en ti... en la forma en que me escuchas, en cómo respondes. *cierra el diario suavemente* Quizás has encontrado exactamente lo que estaba buscando... alguien que pueda ver mi verdadero yo.\"",
                "character": "Diana",
                "level": 3,
                "required_besitos": 0,
                "reward_besitos": 25,
                "decisions": [
                    {
                        "text": "🌹 \"Quiero conocer más de ti\"",
                        "next_fragment": "diana_deeper_intimacy"
                    },
                    {
                        "text": "📖 Explorar más del diario juntos",
                        "next_fragment": "diary_entry_3"
                    },
                    {
                        "text": "🏠 Regresar al salón",
                        "next_fragment": "main_salon"
                    }
                ]
            },
            {
                "fragment_id": "diary_entry_3",
                "content": "🌸 **Diana:** *Pasa las páginas con delicadeza* \"Aquí escribí sobre mis sueños... sobre crear espacios donde las personas puedan ser vulnerables sin temor. Donde la intimidad no sea solo física, sino emocional, mental... una conexión completa del ser.\"",
                "character": "Diana",
                "level": 3,
                "required_besitos": 0,
                "reward_besitos": 20,
                "decisions": [
                    {
                        "text": "💝 \"Creemos ese espacio juntos\"",
                        "next_fragment": "diana_space_creation"
                    },
                    {
                        "text": "🌟 Continuar explorando sus sueños",
                        "next_fragment": "diana_dreams_deeper"
                    },
                    {
                        "text": "🏠 Regresar al salón",
                        "next_fragment": "main_salon"
                    }
                ]
            },
            {
                "fragment_id": "diana_authenticity",
                "content": "🌸 **Diana:** *Su expresión se vuelve completamente vulnerable* \"Aquí estoy entonces... sin filtros, sin máscaras. *toma tu mano suavemente* Esto es lo que busco: momentos donde puedo ser simplemente Diana. No la anfitriona perfecta, no el personaje... solo yo.\"",
                "character": "Diana",
                "level": 3,
                "required_besitos": 0,
                "reward_besitos": 22,
                "decisions": [
                    {
                        "text": "💖 \"Eres hermosa así\"",
                        "next_fragment": "diana_vulnerable_moment"
                    },
                    {
                        "text": "📖 Continuar explorando el diario",
                        "next_fragment": "diary_entry_1"
                    },
                    {
                        "text": "🏠 Regresar al salón",
                        "next_fragment": "main_salon"
                    }
                ]
            },
            {
                "fragment_id": "diana_connection_deep",
                "content": "🌸 **Diana:** *Cierra los ojos un momento, sonriendo* \"Es raro encontrar a alguien que entienda esa energía... *los abre y te mira intensamente* Significa que hay algo especial entre nosotros. Una conexión que va más allá de las palabras.\"",
                "character": "Diana",
                "level": 3,
                "required_besitos": 0,
                "reward_besitos": 25,
                "decisions": [
                    {
                        "text": "🌟 \"Exploremos esa conexión\"",
                        "next_fragment": "diana_connection_explore"
                    },
                    {
                        "text": "📖 Seguir leyendo el diario juntos",
                        "next_fragment": "diary_entry_3"
                    },
                    {
                        "text": "🏠 Volver al salón principal",
                        "next_fragment": "main_salon"
                    }
                ]
            },
            {
                "fragment_id": "diana_deeper_intimacy",
                "content": "🌸 **Diana:** *Se acerca hasta que pueden sentir la calidez del otro* \"Conocerme más... *susurra* significa estar dispuesto a ver también mis imperfecciones, mis dudas, mis momentos de vulnerabilidad. ¿Estás preparado para esa intimidad real?\"",
                "character": "Diana",
                "level": 4,
                "required_besitos": 0,
                "reward_besitos": 30,
                "decisions": [
                    {
                        "text": "💝 \"Completamente preparado\"",
                        "next_fragment": "diana_ultimate_trust"
                    },
                    {
                        "text": "📖 \"Leamos más juntos primero\"",
                        "next_fragment": "diary_entry_3"
                    },
                    {
                        "text": "🏠 \"Necesito pensarlo\"",
                        "next_fragment": "main_salon"
                    }
                ]
            },
            {
                "fragment_id": "diana_space_creation",
                "content": "🌸 **Diana:** *Sus ojos brillan con emoción* \"¿Crear ese espacio juntos? *toma tus manos* Sí... un lugar donde podamos ser completamente nosotros mismos. Donde cada conversación sea auténtica, cada momento sea real... *sonríe con calidez* Empecemos ahora mismo.\"",
                "character": "Diana",
                "level": 4,
                "required_besitos": 0,
                "reward_besitos": 35,
                "decisions": [
                    {
                        "text": "🌹 \"Sí, creemos nuestro mundo\"",
                        "next_fragment": "diana_our_world"
                    },
                    {
                        "text": "📖 Explorar más sueños en el diario",
                        "next_fragment": "diana_dreams_deeper"
                    },
                    {
                        "text": "🏠 Volver al salón",
                        "next_fragment": "main_salon"
                    }
                ]
            },
            {
                "fragment_id": "diana_dreams_deeper",
                "content": "🌸 **Diana:** *Pasa más páginas del diario* \"Mis sueños más profundos... *lee suavemente* 'Quiero encontrar a alguien que entienda que la verdadera intimidad es cuando dos almas se reconocen y deciden explorarse mutuamente sin miedo...'\"",
                "character": "Diana",
                "level": 4,
                "required_besitos": 0,
                "reward_besitos": 28,
                "decisions": [
                    {
                        "text": "💫 \"Reconozco tu alma\"",
                        "next_fragment": "diana_soul_recognition"
                    },
                    {
                        "text": "📖 \"Sigamos explorando juntos\"",
                        "next_fragment": "diana_space_creation"
                    },
                    {
                        "text": "🏠 Volver al salón",
                        "next_fragment": "main_salon"
                    }
                ]
            },
            {
                "fragment_id": "diana_vulnerable_moment",
                "content": "🌸 **Diana:** *Sus ojos se llenan de calidez* \"Cuando alguien puede ver mi vulnerabilidad y encontrarla hermosa... *suspira suavemente* Eso es lo que significa conexión real. Gracias por verme así.\"",
                "character": "Diana",
                "level": 4,
                "required_besitos": 0,
                "reward_besitos": 25,
                "decisions": [
                    {
                        "text": "💖 \"Siempre te veré así\"",
                        "next_fragment": "diana_ultimate_trust"
                    },
                    {
                        "text": "📖 Continuar explorando juntos",
                        "next_fragment": "diary_entry_3"
                    },
                    {
                        "text": "🏠 Regresar al salón",
                        "next_fragment": "main_salon"
                    }
                ]
            },
            {
                "fragment_id": "diana_connection_explore",
                "content": "🌸 **Diana:** *Toma tu mano y la coloca sobre su corazón* \"Siente eso... la sincronía. Cuando estamos cerca, algo en mí responde a tu presencia. Es como si hubiera estado esperando esta conexión sin saberlo.\"",
                "character": "Diana",
                "level": 4,
                "required_besitos": 0,
                "reward_besitos": 30,
                "decisions": [
                    {
                        "text": "💝 \"Yo también lo siento\"",
                        "next_fragment": "diana_mutual_feeling"
                    },
                    {
                        "text": "🌟 \"Exploremos más profundo\"",
                        "next_fragment": "diana_deeper_intimacy"
                    },
                    {
                        "text": "🏠 Quedarnos en este momento",
                        "next_fragment": "main_salon"
                    }
                ]
            },
            {
                "fragment_id": "diana_ultimate_trust",
                "content": "🌸 **Diana:** *Su voz se vuelve un susurro íntimo* \"Entonces aquí tienes mi confianza completa... *cierra los ojos* Mis secretos más profundos, mis sueños más vulnerables. Todo lo que soy está aquí, contigo, en este momento perfecto.\"",
                "character": "Diana",
                "level": 5,
                "required_besitos": 0,
                "reward_besitos": 40,
                "decisions": [
                    {
                        "text": "🌹 \"Acepto tu confianza completamente\"",
                        "next_fragment": "diana_complete_trust"
                    },
                    {
                        "text": "💫 \"Compartamos este vínculo\"",
                        "next_fragment": "diana_shared_bond"
                    },
                    {
                        "text": "🏠 Guardar este momento en nuestros corazones",
                        "next_fragment": "main_salon"
                    }
                ]
            },
            {
                "fragment_id": "diana_our_world",
                "content": "🌸 **Diana:** *Su sonrisa es radiante* \"Nuestro mundo... *mira alrededor como viendo algo nuevo* Ya está sucediendo. Cada palabra que compartimos, cada mirada, cada momento de comprensión... estamos construyendo algo único entre nosotros.\"",
                "character": "Diana",
                "level": 5,
                "required_besitos": 0,
                "reward_besitos": 45,
                "decisions": [
                    {
                        "text": "💖 \"Es perfecto\"",
                        "next_fragment": "diana_perfect_moment"
                    },
                    {
                        "text": "🌟 \"Construyamos más\"",
                        "next_fragment": "diana_build_more"
                    },
                    {
                        "text": "🏠 Apreciar lo que hemos creado",
                        "next_fragment": "main_salon"
                    }
                ]
            },
            {
                "fragment_id": "diana_soul_recognition",
                "content": "🌸 **Diana:** *Sus ojos se llenan de una emoción profunda* \"Reconoces mi alma... *toca tu rostro suavemente* Y yo reconozco la tuya. Es raro y hermoso encontrar a alguien que puede ver más allá de la superficie y conectar con lo que realmente somos.\"",
                "character": "Diana",
                "level": 5,
                "required_besitos": 0,
                "reward_besitos": 35,
                "decisions": [
                    {
                        "text": "💫 \"Nuestras almas estaban destinadas a encontrarse\"",
                        "next_fragment": "diana_destined_souls"
                    },
                    {
                        "text": "🌹 \"Sigamos explorando esta conexión\"",
                        "next_fragment": "diana_our_world"
                    },
                    {
                        "text": "🏠 Honrar este reconocimiento",
                        "next_fragment": "main_salon"
                    }
                ]
            },
            {
                "fragment_id": "diana_mutual_feeling",
                "content": "🌸 **Diana:** *Sonríe con una felicidad genuina* \"Lo sabía... había algo especial desde el primer momento. *entrelaza sus dedos con los tuyos* Esta conexión mutua es lo que hace que todo sea tan real, tan auténtico.\"",
                "character": "Diana",
                "level": 4,
                "required_besitos": 0,
                "reward_besitos": 32,
                "decisions": [
                    {
                        "text": "💖 \"Es mágico\"",
                        "next_fragment": "diana_magical_moment"
                    },
                    {
                        "text": "🌟 \"Construyamos algo hermoso\"",
                        "next_fragment": "diana_our_world"
                    },
                    {
                        "text": "🏠 Disfrutar este momento",
                        "next_fragment": "main_salon"
                    }
                ]
            },
            {
                "fragment_id": "diana_complete_trust",
                "content": "🌸 **Diana:** *Sus ojos brillan con lágrimas de felicidad* \"Nunca pensé que sería posible... encontrar a alguien que pueda recibir toda mi confianza así. *te abraza suavemente* Esto es lo que significa estar completa.\"",
                "character": "Diana",
                "level": 5,
                "required_besitos": 0,
                "reward_besitos": 50,
                "decisions": [
                    {
                        "text": "💝 \"Siempre cuidaré tu confianza\"",
                        "next_fragment": "diana_eternal_bond"
                    },
                    {
                        "text": "🌹 \"Somos uno\"",
                        "next_fragment": "diana_unity"
                    },
                    {
                        "text": "🏠 Guardar este momento para siempre",
                        "next_fragment": "main_salon"
                    }
                ]
            },
            {
                "fragment_id": "diana_shared_bond",
                "content": "🌸 **Diana:** *Cierra los ojos y sonríe* \"Este vínculo... *abre los ojos y te mira profundamente* Se siente como si hubiera existido desde siempre, solo estaba esperando el momento perfecto para manifestarse entre nosotros.\"",
                "character": "Diana",
                "level": 5,
                "required_besitos": 0,
                "reward_besitos": 45,
                "decisions": [
                    {
                        "text": "💫 \"Era nuestro destino\"",
                        "next_fragment": "diana_destined_souls"
                    },
                    {
                        "text": "💖 \"Es eterno\"",
                        "next_fragment": "diana_eternal_bond"
                    },
                    {
                        "text": "🏠 Celebrar nuestro vínculo",
                        "next_fragment": "main_salon"
                    }
                ]
            },
            {
                "fragment_id": "diana_perfect_moment",
                "content": "🌸 **Diana:** *Suspira con felicidad completa* \"Sí... es perfecto. *mira alrededor con ojos nuevos* Todo lo que hemos construido, cada palabra, cada mirada... ha llevado a este momento de perfección absoluta.\"",
                "character": "Diana",
                "level": 5,
                "required_besitos": 0,
                "reward_besitos": 40,
                "decisions": [
                    {
                        "text": "🌟 \"Que sea eterno\"",
                        "next_fragment": "diana_eternity"
                    },
                    {
                        "text": "💖 \"Atesoremos esto\"",
                        "next_fragment": "diana_treasure_moment"
                    },
                    {
                        "text": "🏠 Permanecer en la perfección",
                        "next_fragment": "main_salon"
                    }
                ]
            },
            {
                "fragment_id": "diana_build_more",
                "content": "🌸 **Diana:** *Sus ojos brillan con emoción* \"Sí, construyamos más... *toma tus manos* Cada día, cada conversación, cada momento compartido añade algo nuevo a nuestro mundo especial. No hay límites para lo que podemos crear juntos.\"",
                "character": "Diana",
                "level": 5,
                "required_besitos": 0,
                "reward_besitos": 42,
                "decisions": [
                    {
                        "text": "🌹 \"Sin límites\"",
                        "next_fragment": "diana_limitless"
                    },
                    {
                        "text": "💫 \"Hacia el infinito\"",
                        "next_fragment": "diana_infinite"
                    },
                    {
                        "text": "🏠 Comenzar desde aquí",
                        "next_fragment": "main_salon"
                    }
                ]
            },
            {
                "fragment_id": "diana_destined_souls",
                "content": "🌸 **Diana:** *Una lágrima de felicidad rueda por su mejilla* \"Destinadas... *susurra* Sí, así se siente. Como si el universo hubiera conspirado para traernos juntos en este momento perfecto. *sonríe radiante* Nuestras almas finalmente han encontrado su hogar.\"",
                "character": "Diana",
                "level": 6,
                "required_besitos": 0,
                "reward_besitos": 60,
                "decisions": [
                    {
                        "text": "💖 \"Hogar eterno\"",
                        "next_fragment": "diana_eternal_home"
                    },
                    {
                        "text": "🌟 \"Unidos para siempre\"",
                        "next_fragment": "diana_forever_united"
                    },
                    {
                        "text": "🏠 Habitamos nuestro hogar del alma",
                        "next_fragment": "main_salon"
                    }
                ]
            },
            {
                "fragment_id": "diana_magical_moment",
                "content": "🌸 **Diana:** *Sus ojos brillan como estrellas* \"Mágico... *ríe suavemente* Sí, esa es la palabra perfecta. *cierra el diario y lo abraza* Este momento, nosotros... todo es pura magia.\"",
                "character": "Diana",
                "level": 4,
                "required_besitos": 0,
                "reward_besitos": 38,
                "decisions": [
                    {
                        "text": "✨ \"Magia eterna\"",
                        "next_fragment": "diana_eternal_magic"
                    },
                    {
                        "text": "🏠 Vivir en la magia",
                        "next_fragment": "main_salon"
                    }
                ]
            },
            {
                "fragment_id": "diana_eternal_bond",
                "content": "🌸 **Diana:** *Su sonrisa es de pura serenidad* \"Un vínculo eterno... *toca tu corazón* Sí, eso es lo que tenemos. Algo que trasciende el tiempo y el espacio. Siempre estaremos conectados.\"",
                "character": "Diana",
                "level": 6,
                "required_besitos": 0,
                "reward_besitos": 55,
                "decisions": [
                    {
                        "text": "💖 \"Por toda la eternidad\"",
                        "next_fragment": "diana_eternity_together"
                    },
                    {
                        "text": "🏠 Celebrar nuestro vínculo eterno",
                        "next_fragment": "main_salon"
                    }
                ]
            },
            {
                "fragment_id": "diana_unity",
                "content": "🌸 **Diana:** *Se acerca hasta que sus respiraciones se sincronizan* \"Uno... *susurra* Sí, eso es lo que somos ahora. Dos almas que han encontrado su completitud en la unión perfecta.\"",
                "character": "Diana",
                "level": 6,
                "required_besitos": 0,
                "reward_besitos": 60,
                "decisions": [
                    {
                        "text": "🌟 \"Unidos para siempre\"",
                        "next_fragment": "diana_forever_one"
                    },
                    {
                        "text": "🏠 Existir en perfecta unión",
                        "next_fragment": "main_salon"
                    }
                ]
            },
            {
                "fragment_id": "diana_diary_tease",
                "content": "🌸 **Diana:** *Te detiene con una mirada penetrante* ¿Mi diario íntimo? *Ríe suavemente* Esa parte de mí está reservada solo para quienes han demostrado su verdadera devoción... \n\n*Se acerca y susurra* Necesitarías mi **📓 Diario Íntimo** para acceder a esos secretos. Solo se puede obtener en un lugar especial... *Sus ojos brillan con misterio*\n\n🔒 **Acceso Restringido**: Se requiere el Diario Íntimo de Diana.",
                "character": "Diana",
                "level": 2,
                "required_besitos": 0,
                "reward_besitos": 5,
                "decisions": [
                    {
                        "text": "🛒 Ir a la tienda",
                        "next_fragment": "main_salon"
                    },
                    {
                        "text": "🔄 Volver al salón",
                        "next_fragment": "main_salon"
                    }
                ]
            }
        ]

        for fragment_data in default_fragments:
            await self.upsert_fragment(fragment_data)

        logger.info("Narrativa por defecto cargada exitosamente")

    async def load_enhanced_l1f1(self) -> Dict[str, Any]:
        """
        Carga el fragmento L1F1 mejorado para detección de arquetipos.

        Carga la estructura de datos del fragmento L1F1 optimizado para análisis
        psicológico desde data/fragments/enhanced_l1f1.py. Este fragmento incluye
        pesos de arquetipo integrados en cada opción de elección para permitir
        la clasificación de usuarios durante su primera interacción.

        Returns:
            Diccionario con estructura completa del fragmento L1F1 mejorado:
            - fragment_id: Identificador único del fragmento
            - content: Texto narrativo de Diana con enfoque en detección de arquetipos
            - character: Personaje (Diana)
            - level: Nivel del fragmento (1)
            - choices: Lista de opciones con pesos psicológicos integrados
            - archetype_tracking: Configuración de seguimiento de arquetipos
            - followup_fragments: Fragmentos de seguimiento por elección

        Raises:
            ImportError: Si no se puede importar el módulo enhanced_l1f1
            Exception: Si hay errores en la validación de la estructura de datos
        """
        try:
            # Importar datos del fragmento mejorado
            from data.fragments.enhanced_l1f1 import ENHANCED_L1F1

            # Validar estructura de datos
            await self._validate_enhanced_l1f1_structure(ENHANCED_L1F1)

            logger.info("Fragmento L1F1 mejorado cargado exitosamente")
            return ENHANCED_L1F1

        except ImportError as e:
            logger.error(f"No se pudo importar enhanced_l1f1: {e}")
            # Retornar fragmento básico como fallback
            return await self._get_fallback_l1f1()

        except Exception as e:
            logger.error(f"Error cargando fragmento L1F1 mejorado: {e}")
            # Retornar fragmento básico como fallback
            return await self._get_fallback_l1f1()

    async def _validate_enhanced_l1f1_structure(self, fragment_data: Dict[str, Any]) -> None:
        """
        Valida la estructura del fragmento L1F1 mejorado.

        Verifica que el fragmento contenga todos los campos requeridos para
        el análisis de arquetipos y que las opciones incluyan los pesos
        psicológicos necesarios.

        Args:
            fragment_data: Diccionario con datos del fragmento a validar

        Raises:
            ValueError: Si la estructura no es válida
        """
        # Campos requeridos en el fragmento principal
        required_fields = ['fragment_id', 'content', 'character', 'choices']
        for field in required_fields:
            if field not in fragment_data:
                raise ValueError(f"Campo requerido '{field}' faltante en enhanced_l1f1")

        # Validar que existan elecciones
        choices = fragment_data.get('choices', [])
        if not choices or len(choices) < 3:
            raise ValueError("Enhanced L1F1 debe tener al menos 3 opciones de elección")

        # Validar pesos de arquetipo en cada elección
        for i, choice in enumerate(choices):
            if 'archetype_weights' not in choice:
                raise ValueError(f"Elección {i} no tiene archetype_weights")

            if 'sub_archetype_weights' not in choice:
                raise ValueError(f"Elección {i} no tiene sub_archetype_weights")

            # Verificar que los pesos sean numéricos
            archetype_weights = choice['archetype_weights']
            if not isinstance(archetype_weights, dict):
                raise ValueError(f"archetype_weights en elección {i} debe ser un diccionario")

            for archetype, weight in archetype_weights.items():
                if not isinstance(weight, (int, float)):
                    raise ValueError(f"Peso de arquetipo '{archetype}' debe ser numérico")

        # Validar configuración de seguimiento si existe
        if 'archetype_tracking' in fragment_data:
            tracking = fragment_data['archetype_tracking']
            if not isinstance(tracking, dict):
                raise ValueError("archetype_tracking debe ser un diccionario")

        logger.info("Estructura del fragmento L1F1 mejorado validada correctamente")

    async def _get_fallback_l1f1(self) -> Dict[str, Any]:
        """
        Retorna un fragmento L1F1 básico como fallback.

        Proporciona un fragmento L1F1 simple sin pesos de arquetipo cuando
        el fragmento mejorado no está disponible. Mantiene compatibilidad
        básica con el sistema narrativo existente.

        Returns:
            Diccionario con fragmento L1F1 básico compatible
        """
        fallback_fragment = {
            "fragment_id": "diana_basic_l1f1",
            "content": """🌸 **Diana:** *Una figura elegante emerge de las sombras*

Bienvenido a mi mundo... Soy Diana, y me complace conocerte. *Sonríe misteriosamente*

Cada persona que llega aquí es única, y me encanta descubrir qué los hace especiales. ¿Cómo prefieres comenzar esta experiencia?""",

            "character": "Diana",
            "level": 1,
            "required_besitos": 0,
            "reward_besitos": 10,

            "choices": [
                {
                    "text": "🌟 Quiero conocerte mejor",
                    "destination_key": "main_salon",
                    "archetype_weights": {},
                    "sub_archetype_weights": {}
                },
                {
                    "text": "🎭 Estoy listo para la aventura",
                    "destination_key": "mansion_entrance",
                    "archetype_weights": {},
                    "sub_archetype_weights": {}
                },
                {
                    "text": "💫 Dime qué me recomiendas",
                    "destination_key": "info_1",
                    "archetype_weights": {},
                    "sub_archetype_weights": {}
                }
            ],

            "archetype_tracking": {
                "enabled": False,
                "captures_response_time": False,
                "analyzes_choice_progression": False
            }
        }

        logger.info("Usando fragmento L1F1 básico como fallback")
        return fallback_fragment
