from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from services.narrative_fragment_service import NarrativeFragmentService
import json
import logging

logger = logging.getLogger(__name__)
router = Router()

# FSM States for narrative fragment management
class NarrativeFragmentStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_content = State()
    waiting_for_type = State()
    waiting_for_choices = State()
    waiting_for_triggers = State()
    waiting_for_required_clues = State()
    waiting_for_fragment_id = State()
    waiting_for_update_field = State()
    waiting_for_update_value = State()


@router.message(F.text == "/create_fragment")
async def start_create_fragment(message: Message, state: FSMContext, session: AsyncSession):
    """Start the process of creating a new narrative fragment."""
    user_id = message.from_user.id
    
    # For testing purposes, we'll allow all users to create fragments
    # In a real implementation, you would check if user is admin:
    # if not await is_admin(user_id):
    #     await message.answer("❌ Solo los administradores pueden crear fragmentos narrativos.")
    #     return
    
    await message.answer("📝 Creando un nuevo fragmento narrativo.\n\nPor favor, envíame el título del fragmento:")
    await state.set_state(NarrativeFragmentStates.waiting_for_title)


@router.message(NarrativeFragmentStates.waiting_for_title)
async def process_title(message: Message, state: FSMContext):
    """Process the title of the fragment."""
    title = message.text.strip()
    if not title:
        await message.answer("❌ El título no puede estar vacío. Por favor, envíame un título válido:")
        return
    
    await state.update_data(title=title)
    await message.answer("📄 Ahora envíame el contenido del fragmento:")
    await state.set_state(NarrativeFragmentStates.waiting_for_content)


@router.message(NarrativeFragmentStates.waiting_for_content)
async def process_content(message: Message, state: FSMContext):
    """Process the content of the fragment."""
    content = message.text.strip()
    if not content:
        await message.answer("❌ El contenido no puede estar vacío. Por favor, envíame un contenido válido:")
        return
    
    await state.update_data(content=content)
    type_buttons = {
        "📖 Historia": "STORY",
        "❓ Decisión": "DECISION",
        "ℹ️ Información": "INFO"
    }
    
    type_message = "Tipo de fragmento:\n"
    for i, (label, value) in enumerate(type_buttons.items(), 1):
        type_message += f"{i}. {label}\n"
    
    type_message += "\nPor favor, responde con el número correspondiente al tipo de fragmento:"
    
    await message.answer(type_message)
    await state.set_state(NarrativeFragmentStates.waiting_for_type)


@router.message(NarrativeFragmentStates.waiting_for_type)
async def process_type(message: Message, state: FSMContext):
    """Process the type of the fragment."""
    type_mapping = {
        "1": "STORY",
        "2": "DECISION",
        "3": "INFO"
    }
    
    type_choice = message.text.strip()
    fragment_type = type_mapping.get(type_choice)
    
    if not fragment_type:
        await message.answer("❌ Opción no válida. Por favor, responde con 1, 2 o 3:")
        return
    
    await state.update_data(fragment_type=fragment_type)
    
    # For decision fragments, ask for choices
    if fragment_type == "DECISION":
        await message.answer(
            "🔗 Para fragmentos de decisión, puedes agregar opciones.\n"
            "Envíame las opciones en formato JSON, o escribe 'ninguna' si no hay opciones:\n\n"
            "Ejemplo:\n"
            "[{\"text\": \"Opción 1\", \"next_fragment_id\": \"uuid-aqui\"}, {\"text\": \"Opción 2\", \"next_fragment_id\": \"otro-uuid-aqui\"}]"
        )
        await state.set_state(NarrativeFragmentStates.waiting_for_choices)
    else:
        # Skip choices for non-decision fragments
        await state.update_data(choices=[])
        await message.answer(
            "🎁 Ahora puedes agregar triggers (recompensas/efectos).\n"
            "Envíame los triggers en formato JSON, o escribe 'ninguno' si no hay triggers:\n\n"
            "Ejemplo:\n"
            "{\"reward_points\": 10, \"unlock_lore\": \"codigo-pista\"}"
        )
        await state.set_state(NarrativeFragmentStates.waiting_for_triggers)


@router.message(NarrativeFragmentStates.waiting_for_choices)
async def process_choices(message: Message, state: FSMContext):
    """Process the choices for decision fragments."""
    choices_text = message.text.strip()
    
    if choices_text.lower() == "ninguna":
        choices = []
    else:
        try:
            choices = json.loads(choices_text)
            if not isinstance(choices, list):
                raise ValueError("Choices must be a list")
        except (json.JSONDecodeError, ValueError) as e:
            await message.answer(
                f"❌ Formato JSON inválido: {str(e)}\n\n"
                "Por favor, envíame las opciones en formato JSON válido:\n"
                "[{\"text\": \"Opción 1\", \"next_fragment_id\": \"uuid-aqui\"}, ...]\n\n"
                "O escribe 'ninguna' si no hay opciones:"
            )
            return
    
    await state.update_data(choices=choices)
    await message.answer(
        "🎁 Ahora puedes agregar triggers (recompensas/efectos).\n"
        "Envíame los triggers en formato JSON, o escribe 'ninguno' si no hay triggers:\n\n"
        "Ejemplo:\n"
        "{\"reward_points\": 10, \"unlock_lore\": \"codigo-pista\"}"
    )
    await state.set_state(NarrativeFragmentStates.waiting_for_triggers)


@router.message(NarrativeFragmentStates.waiting_for_triggers)
async def process_triggers(message: Message, state: FSMContext):
    """Process the triggers for the fragment."""
    triggers_text = message.text.strip()
    
    if triggers_text.lower() == "ninguno":
        triggers = {}
    else:
        try:
            triggers = json.loads(triggers_text)
            if not isinstance(triggers, dict):
                raise ValueError("Triggers must be a dictionary")
        except (json.JSONDecodeError, ValueError) as e:
            await message.answer(
                f"❌ Formato JSON inválido: {str(e)}\n\n"
                "Por favor, envíame los triggers en formato JSON válido:\n"
                "{\"reward_points\": 10, \"unlock_lore\": \"codigo-pista\"}\n\n"
                "O escribe 'ninguno' si no hay triggers:"
            )
            return
    
    await state.update_data(triggers=triggers)
    await message.answer(
        "🗝️ Finalmente, puedes especificar las pistas requeridas.\n"
        "Envíame una lista de códigos de pistas separadas por comas, o escribe 'ninguna' si no hay requisitos:\n\n"
        "Ejemplo:\n"
        "pista-1,pista-2,pista-3"
    )
    await state.set_state(NarrativeFragmentStates.waiting_for_required_clues)


@router.message(NarrativeFragmentStates.waiting_for_required_clues)
async def process_required_clues(message: Message, state: FSMContext, session: AsyncSession):
    """Process the required clues and create the fragment."""
    clues_text = message.text.strip()
    
    if clues_text.lower() == "ninguna":
        required_clues = []
    else:
        required_clues = [clue.strip() for clue in clues_text.split(",") if clue.strip()]
    
    # Get all data from state
    data = await state.get_data()
    
    try:
        # Create the narrative fragment
        service = NarrativeFragmentService(session)
        fragment = await service.create_fragment(
            title=data["title"],
            content=data["content"],
            fragment_type=data["fragment_type"],
            choices=data.get("choices", []),
            triggers=data.get("triggers", {}),
            required_clues=required_clues
        )
        
        # Send confirmation
        response = f"✅ Fragmento narrativo creado exitosamente!\n\n"
        response += f"🆔 ID: {fragment.id}\n"
        response += f"📝 Título: {fragment.title}\n"
        response += f"🏷️ Tipo: {fragment.fragment_type}\n"
        
        await message.answer(response)
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error creating narrative fragment: {e}")
        await message.answer(f"❌ Error al crear el fragmento: {str(e)}")
        await state.clear()


@router.message(F.text == "/list_fragments")
async def list_fragments(message: Message, session: AsyncSession):
    """List all narrative fragments."""
    user_id = message.from_user.id
    
    # For testing purposes, we'll allow all users to list fragments
    # In a real implementation, you would check if user is admin:
    # if not await is_admin(user_id):
    #     await message.answer("❌ Solo los administradores pueden listar fragmentos narrativos.")
    #     return
    
    service = NarrativeFragmentService(session)
    
    # Get all fragments
    story_fragments = await service.get_story_fragments()
    decision_fragments = await service.get_decision_fragments()
    info_fragments = await service.get_info_fragments()
    
    response = "📖 Fragmentos Narrativos:\n\n"
    
    # Story fragments
    response += "🏷️ Historia:\n"
    if story_fragments:
        for fragment in story_fragments:
            response += f"  • {fragment.title} ({fragment.id[:8]}...)\n"
    else:
        response += "  (No hay fragmentos de historia)\n"
    
    response += "\n❓ Decisión:\n"
    if decision_fragments:
        for fragment in decision_fragments:
            response += f"  • {fragment.title} ({fragment.id[:8]}...)\n"
    else:
        response += "  (No hay fragmentos de decisión)\n"
    
    response += "\nℹ️ Información:\n"
    if info_fragments:
        for fragment in info_fragments:
            response += f"  • {fragment.title} ({fragment.id[:8]}...)\n"
    else:
        response += "  (No hay fragmentos informativos)\n"
    
    await message.answer(response)


@router.message(F.text == "/get_fragment")
async def start_get_fragment(message: Message, state: FSMContext):
    """Start the process of getting a narrative fragment by ID."""
    user_id = message.from_user.id
    
    # For testing purposes, we'll allow all users to get fragments
    # In a real implementation, you would check if user is admin:
    # if not await is_admin(user_id):
    #     await message.answer("❌ Solo los administradores pueden obtener fragmentos narrativos.")
    #     return
    
    await message.answer("🆔 Por favor, envíame el ID del fragmento que deseas obtener:")
    await state.set_state(NarrativeFragmentStates.waiting_for_fragment_id)


@router.message(NarrativeFragmentStates.waiting_for_fragment_id)
async def process_fragment_id(message: Message, state: FSMContext, session: AsyncSession):
    """Process the fragment ID and retrieve the fragment."""
    fragment_id = message.text.strip()
    
    service = NarrativeFragmentService(session)
    fragment = await service.get_fragment(fragment_id)
    
    if not fragment:
        await message.answer("❌ No se encontró un fragmento con ese ID.")
        await state.clear()
        return
    
    # Format fragment details
    response = f"📄 Detalles del Fragmento:\n\n"
    response += f"🆔 ID: {fragment.id}\n"
    response += f"📝 Título: {fragment.title}\n"
    response += f"🏷️ Tipo: {fragment.fragment_type}\n"
    response += f"📅 Creado: {fragment.created_at}\n"
    response += f"🔄 Actualizado: {fragment.updated_at}\n"
    response += f"✅ Activo: {'Sí' if fragment.is_active else 'No'}\n\n"
    response += f"📄 Contenido:\n{fragment.content}\n\n"
    
    if fragment.choices:
        response += f"🔗 Opciones: {json.dumps(fragment.choices, indent=2, ensure_ascii=False)}\n\n"
    
    if fragment.triggers:
        response += f"🎁 Triggers: {json.dumps(fragment.triggers, indent=2, ensure_ascii=False)}\n\n"
    
    if fragment.required_clues:
        response += f"🗝️ Pistas requeridas: {', '.join(fragment.required_clues)}\n"
    
    await message.answer(response)
    await state.clear()


# Register the router
def register_narrative_fragment_handlers(dp):
    """Register narrative fragment handlers with the dispatcher."""
    dp.include_router(router)