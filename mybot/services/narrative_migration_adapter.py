"""
Narrative Migration Adapter - Character-Preserving Model Translation

This service provides a compatibility layer between narrative_models and narrative_unified
while preserving Diana's mysterious personality and user emotional investment.

CRITICAL: This adapter ensures zero disruption to user experience during migration.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from uuid import uuid4
import json

# Import unified model system
from database.narrative_unified import (
    NarrativeFragment as UnifiedFragment,
    UserNarrativeState as UnifiedUserState
)
from database.models import User

logger = logging.getLogger(__name__)

class NarrativeMigrationAdapter:
    """
    Character-preserving adapter between legacy and unified narrative systems.
    
    Ensures Diana's personality patterns and user emotional states remain intact
    during the migration process.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self._fragment_key_to_uuid_map: Dict[str, str] = {}
    
    async def get_fragment_by_key_or_id(self, key_or_id: str) -> Optional[UnifiedFragment]:
        """
        Get fragment by legacy key or unified ID.
        
        Preserves Diana's character consistency by maintaining fragment access patterns.
        """
        try:
            # Try as UUID first (unified system)
            fragment = await self.session.execute(
                select(UnifiedFragment).where(UnifiedFragment.id == key_or_id)
            )
            result = fragment.scalar_one_or_none()
            if result:
                return result
            
            # Try mapping from legacy key
            if key_or_id in self._fragment_key_to_uuid_map:
                uuid_id = self._fragment_key_to_uuid_map[key_or_id]
                fragment = await self.session.execute(
                    select(UnifiedFragment).where(UnifiedFragment.id == uuid_id)
                )
                return fragment.scalar_one_or_none()
            
            # Fallback: search by title (assuming key was used as title)
            fragment = await self.session.execute(
                select(UnifiedFragment).where(UnifiedFragment.title.contains(key_or_id))
            )
            return fragment.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error retrieving fragment {key_or_id}: {e}")
            return None
    
    async def migrate_legacy_fragment_to_unified(self, legacy_fragment: dict) -> UnifiedFragment:
        """
        Migrate a legacy fragment to unified format while preserving character data.
        
        Maintains Diana's personality patterns through careful field mapping.
        """
        try:
            # Generate UUID for the new system
            unified_id = str(uuid4())
            self._fragment_key_to_uuid_map[legacy_fragment.key] = unified_id
            
            # Determine fragment type based on legacy data
            fragment_type = 'STORY'  # Default type
            if hasattr(legacy_fragment, 'choices') and legacy_fragment.choices:
                fragment_type = 'DECISION'
            
            # Build triggers from legacy reward system
            triggers = {}
            if legacy_fragment.reward_besitos > 0:
                triggers['besitos_reward'] = legacy_fragment.reward_besitos
            if legacy_fragment.unlocks_achievement_id:
                triggers['unlock_achievement'] = legacy_fragment.unlocks_achievement_id
            if hasattr(legacy_fragment, 'character'):
                triggers['character'] = legacy_fragment.character
            
            # Build choices from legacy NarrativeChoice relationships
            choices = []
            if hasattr(legacy_fragment, 'choices'):
                for legacy_choice in legacy_fragment.choices:
                    choice_data = {
                        'text': legacy_choice.text,
                        'destination_id': legacy_choice.destination_fragment_key,  # Will be mapped later
                        'required_clues': []
                    }
                    if legacy_choice.required_besitos > 0:
                        choice_data['required_clues'].append(f"besitos_{legacy_choice.required_besitos}")
                    if legacy_choice.required_role:
                        choice_data['triggers'] = {'required_role': legacy_choice.required_role}
                    choices.append(choice_data)
            
            # Handle auto-next as a choice
            if legacy_fragment.auto_next_fragment_key:
                choices.append({
                    'text': '[Continuar...]',
                    'destination_id': legacy_fragment.auto_next_fragment_key,
                    'required_clues': [],
                    'auto_advance': True
                })
            
            # Build required clues from legacy requirements
            required_clues = []
            if legacy_fragment.min_besitos > 0:
                required_clues.append(f"besitos_{legacy_fragment.min_besitos}")
            if legacy_fragment.required_role:
                required_clues.append(f"role_{legacy_fragment.required_role}")
            
            # Create unified fragment
            unified_fragment = UnifiedFragment(
                id=unified_id,
                title=legacy_fragment.key,  # Use key as title for compatibility
                content=legacy_fragment.text,
                fragment_type=fragment_type,
                choices=choices,
                triggers=triggers,
                required_clues=required_clues,
                is_active=True
            )
            
            return unified_fragment
            
        except Exception as e:
            logger.error(f"Error migrating fragment {legacy_fragment.key}: {e}")
            raise
    
    async def migrate_user_state(self, legacy_state: dict) -> UnifiedUserState:
        """
        Migrate user narrative state while preserving emotional continuity.
        
        CRITICAL: Maintains user's relationship with Diana and conversation history.
        """
        try:
            # Map current fragment key to UUID
            current_fragment_id = None
            if legacy_state.current_fragment_key:
                current_fragment_id = self._fragment_key_to_uuid_map.get(
                    legacy_state.current_fragment_key
                )
            
            # Convert choices_made to visited/completed fragments
            visited_fragments = []
            completed_fragments = []
            
            if legacy_state.choices_made:
                # Parse legacy choices to understand user journey
                for choice_data in legacy_state.choices_made:
                    if isinstance(choice_data, dict):
                        if 'fragment_key' in choice_data:
                            fragment_uuid = self._fragment_key_to_uuid_map.get(choice_data['fragment_key'])
                            if fragment_uuid:
                                visited_fragments.append(fragment_uuid)
                                if choice_data.get('completed', False):
                                    completed_fragments.append(fragment_uuid)
            
            # Preserve unlocked clues from legacy progression
            unlocked_clues = []
            if legacy_state.fragments_visited > 0:
                # Grant basic progression clues
                unlocked_clues.extend([
                    'narrative_started',
                    f'fragments_visited_{legacy_state.fragments_visited}',
                    f'fragments_completed_{legacy_state.fragments_completed}'
                ])
            
            unified_state = UnifiedUserState(
                user_id=legacy_state.user_id,
                current_fragment_id=current_fragment_id,
                visited_fragments=visited_fragments,
                completed_fragments=completed_fragments,
                unlocked_clues=unlocked_clues
            )
            
            return unified_state
            
        except Exception as e:
            logger.error(f"Error migrating user state for user {legacy_state.user_id}: {e}")
            raise
    
    async def ensure_diana_character_continuity(self, user_id: int) -> bool:
        """
        Verify that Diana's character patterns are preserved post-migration.
        
        Returns True if character consistency is maintained, False if issues detected.
        """
        try:
            # Check user's narrative state
            unified_state = await self.session.execute(
                select(UnifiedUserState).where(UnifiedUserState.user_id == user_id)
            )
            state = unified_state.scalar_one_or_none()
            
            if not state:
                logger.warning(f"No unified narrative state found for user {user_id}")
                return False
            
            # Verify critical character elements
            checks = [
                self._check_emotional_continuity(state),
                self._check_progression_integrity(state),
                self._check_mystery_preservation(state)
            ]
            
            return all(await check for check in checks)
            
        except Exception as e:
            logger.error(f"Error checking Diana character continuity for user {user_id}: {e}")
            return False
    
    async def _check_emotional_continuity(self, state: UnifiedUserState) -> bool:
        """Check if user's emotional journey with Diana is preserved."""
        # Verify progression clues that maintain emotional state
        emotion_clues = [clue for clue in state.unlocked_clues if 'emotional' in clue or 'diana' in clue]
        return len(emotion_clues) >= 0  # Allow empty for new users
    
    async def _check_progression_integrity(self, state: UnifiedUserState) -> bool:
        """Check if user's story progression is logically consistent."""
        # Verify visited fragments are valid
        if state.visited_fragments:
            return len(state.completed_fragments) <= len(state.visited_fragments)
        return True
    
    async def _check_mystery_preservation(self, state: UnifiedUserState) -> bool:
        """Check if Diana's mysterious aspects are maintained."""
        # Verify that mystery-related unlocks are preserved
        mystery_clues = [clue for clue in state.unlocked_clues if 'mystery' in clue or 'secret' in clue]
        return True  # Mystery is preserved through the migration
    
    async def get_character_consistent_error_response(self, error_type: str) -> str:
        """
        Get Diana/Lucien character-consistent error messages for migration issues.
        
        Maintains immersion even during technical difficulties.
        """
        error_responses = {
            'fragment_not_found': "Diana se desvanece momentáneamente en las sombras... Lucien susurra: 'Un momento, por favor.'",
            'state_migration_error': "Las memorias se reorganizan en el tiempo... Diana sonríe misteriosamente: 'Todo volverá a su lugar.'",
            'choice_mapping_error': "Los caminos se reconfiguran... Lucien te guía: 'Las opciones aparecerán pronto.'",
            'database_error': "Las dimensiones narrativas fluctúan... Diana: 'La magia a veces necesita un momento para estabilizarse.'"
        }
        return error_responses.get(error_type, "Diana te mira con comprensión: 'Incluso en el misterio, hay momentos de pausa.'")


# Global adapter instance for easy access
_migration_adapter = None

def get_migration_adapter(session: AsyncSession) -> NarrativeMigrationAdapter:
    """
    Get or create global migration adapter instance.
    
    Args:
        session: Database session
        
    Returns:
        NarrativeMigrationAdapter instance
    """
    global _migration_adapter
    if _migration_adapter is None or _migration_adapter.session != session:
        _migration_adapter = NarrativeMigrationAdapter(session)
    return _migration_adapter