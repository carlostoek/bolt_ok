# Refactoring Report: `utils/keyboard_utils.py`

**Date:** September 28, 2025

This document outlines the progress made on refactoring `utils/keyboard_utils.py` and the remaining tasks to complete the process.

## Summary of Progress

The goal of this refactoring is to centralize all keyboard creation logic into the `keyboards/` directory, improving code organization and maintainability.

**Completed Tasks:**

1.  **Archived Obsolete Files:** The following unused files were moved to the `obsolete/` directory:
    *   `handlers/trivia_handler.py`
    *   `keyboards/trivia_keyboards.py`

2.  **Refactored Keyboard Functions:** The following functions have been successfully moved from `utils/keyboard_utils.py` to their own dedicated files within the `keyboards/` directory, and all corresponding imports have been updated:
    *   `get_admin_manage_users_keyboard`
    *   `get_admin_manage_content_keyboard`
    *   `get_admin_content_missions_keyboard`
    *   `get_admin_content_badges_keyboard`
    *   `get_admin_content_levels_keyboard`
    *   `get_main_menu_keyboard`
    *   `get_profile_keyboard`
    *   `get_missions_keyboard`
    *   `get_reward_keyboard`
    *   `get_ranking_keyboard`
    *   `get_reaction_keyboard`
    *   `get_custom_reaction_keyboard`
    *   `get_admin_content_rewards_keyboard`
    *   `get_admin_content_auctions_keyboard`
    *   `get_admin_content_daily_gifts_keyboard`
    *   `get_admin_content_minigames_keyboard`
    *   `get_admin_users_list_keyboard`
    *   `get_badge_selection_keyboard`
    *   `get_post_confirmation_keyboard`
    *   `get_reward_type_keyboard`
    *   `get_mission_completed_keyboard`

3.  **Consolidated `get_back_keyboard`:** The legacy `get_back_keyboard` function was replaced with the preferred `get_back_kb` function from `keyboards/common.py` across the entire project, and the old function was removed from `utils/keyboard_utils.py`.

## Remaining Tasks

All tasks have been completed.

## Final Cleanup

After all keyboard-related functions have been migrated, `utils/keyboard_utils.py` was reviewed. It still contains other non-keyboard-related utility functions, so it will be kept.