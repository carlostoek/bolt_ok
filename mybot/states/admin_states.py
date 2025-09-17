from aiogram.fsm.state import StatesGroup, State

class LoreAdminStates(StatesGroup):
    """States for lore piece administration"""
    waiting_for_code = State()
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_content = State()
    waiting_for_category = State()
    waiting_for_search = State()
    waiting_for_unlock_condition = State()

class ShopAdminStates(StatesGroup):
    """States for shop administration"""
    waiting_for_item_name = State()
    waiting_for_item_price = State()
    waiting_for_item_description = State()
    waiting_for_category_selection = State()

class BulkOperationStates(StatesGroup):
    """States for bulk operations"""
    waiting_for_file_upload = State()
    waiting_for_operation_confirmation = State()
    processing_bulk_operation = State()

class NarrativeFragmentStates(StatesGroup):
    """States for narrative fragment management"""
    waiting_for_fragment_key = State()
    waiting_for_fragment_text = State()
    waiting_for_fragment_character = State()
    waiting_for_fragment_level = State()
    waiting_for_fragment_besitos_required = State()
    waiting_for_fragment_besitos_reward = State()
    waiting_for_fragment_decisions = State()
    waiting_for_edit_selection = State()
    waiting_for_edit_field_value = State()
    waiting_for_delete_confirmation = State()
    editing_fragment = State()