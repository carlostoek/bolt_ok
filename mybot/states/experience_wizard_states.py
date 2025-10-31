"""
FSM states for the experience creation wizard.
Provides a guided, step-by-step process for creating unified experiences.
"""
from aiogram.fsm.state import State, StatesGroup


class ExperienceWizardStates(StatesGroup):
    """States for the experience creation wizard."""
    
    # Basic Information
    waiting_for_name = State()
    waiting_for_description = State()
    
    # Requirements
    waiting_for_level_requirement = State()
    waiting_for_vip_requirement = State()
    
    # Narrative Elements
    waiting_for_fragments = State()
    waiting_for_fragment_order = State()
    
    # Shop Elements
    waiting_for_shop_items = State()
    waiting_for_item_prices = State()
    
    # Mission Elements
    waiting_for_missions = State()
    waiting_for_mission_requirements = State()
    
    # Dependencies
    waiting_for_dependencies = State()
    
    # Rewards
    waiting_for_points_reward = State()
    waiting_for_vip_days_reward = State()
    waiting_for_achievements_reward = State()
    
    # Final Confirmation
    waiting_for_confirmation = State()
    
    # Advanced Options
    waiting_for_advanced_options = State()
    waiting_for_unlock_requirements = State()
    waiting_for_completion_conditions = State()