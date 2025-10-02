"""
Estados FSM para el Panel de Admin de Misiones V2

Wizard paso a paso para crear misiones configurables sin tocar código.
"""
from aiogram.fsm.state import State, StatesGroup


class AdminMissionWizardStates(StatesGroup):
    """Estados del wizard de creación de misiones"""

    # ===== PASO 1: Selección de tipo de misión =====
    selecting_mission_type = State()
    choosing_from_template = State()

    # ===== PASO 2: Información básica =====
    entering_name = State()
    entering_description = State()
    selecting_emoji = State()
    selecting_category = State()
    selecting_difficulty = State()

    # ===== PASO 3: Configuración específica por tipo =====
    # Narrativa
    configuring_narrative_context = State()
    selecting_lore_unlock = State()
    selecting_prerequisite_mission = State()
    selecting_unlocked_mission = State()
    entering_completion_message = State()

    # Competitiva
    configuring_competitive_metric = State()
    entering_ranking_position = State()
    entering_ranking_rewards = State()

    # Con Timer
    entering_time_limit = State()
    entering_bonus_points = State()
    configuring_penalty = State()

    # Secreta
    configuring_discovery_trigger = State()
    entering_discovery_emoji = State()
    entering_discovery_level = State()

    # Colaborativa
    entering_global_target = State()
    entering_min_contribution = State()
    entering_event_duration = State()
    selecting_reward_distribution = State()

    # Reacción
    entering_required_emoji = State()
    entering_target_reactions = State()

    # ===== PASO 4: Recompensas =====
    entering_reward_points = State()
    entering_xp_reward = State()
    selecting_badge_reward = State()
    selecting_item_reward = State()

    # ===== PASO 5: Restricciones =====
    configuring_vip_requirement = State()
    entering_min_level = State()
    selecting_required_badge = State()
    entering_max_global_completions = State()
    entering_cooldown = State()

    # ===== PASO 6: Visibilidad y activación =====
    selecting_visibility = State()
    selecting_initial_state = State()
    scheduling_start_date = State()
    scheduling_end_date = State()

    # ===== PASO 7: Preview y confirmación =====
    previewing_mission = State()
    confirming_creation = State()

    # ===== Estados de edición =====
    selecting_mission_to_edit = State()
    editing_field = State()


class AdminMissionManagementStates(StatesGroup):
    """Estados para gestión de misiones existentes"""

    viewing_mission_list = State()
    viewing_mission_details = State()
    viewing_mission_stats = State()
    filtering_by_category = State()
    searching_mission = State()
    bulk_actions = State()
