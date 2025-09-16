import logging
import json
from typing import Dict, Any, List, Optional, Type, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database.narrative_models import StoryFragment, NarrativeChoice, FragmentAnalytics
from utils.narrative_validation import (
    validate_story_fragment_data, 
    sanitize_fragment_content,
    validate_json_structure
)

# Placeholder types for return values
Result = Dict[str, Any]
GraphData = Dict[str, Any]
ValidationReport = Dict[str, Any]
ImportResult = Dict[str, Any]

logger = logging.getLogger(__name__)

class NarrativeAdminService:
    """Service for narrative administration and content management."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_story_fragment(self, fragment_data: Dict) -> Result:
        """
        Creates a new story fragment with validation and security measures.
        
        Args:
            fragment_data: Dictionary containing fragment data
            
        Returns:
            Result dictionary with status and any error messages
        """
        try:
            # Sanitize input data
            sanitized_data = sanitize_fragment_content(fragment_data)
            
            # Validate fragment data
            is_valid, errors = validate_story_fragment_data(sanitized_data)
            if not is_valid:
                return {
                    "status": "validation_error",
                    "errors": errors
                }
            
            # Check if fragment with this key already exists
            existing_fragment = await self.session.execute(
                select(StoryFragment).where(StoryFragment.key == sanitized_data['key'])
            )
            if existing_fragment.scalar_one_or_none():
                return {
                    "status": "error",
                    "message": f"Fragment with key '{sanitized_data['key']}' already exists"
                }
            
            # Create new fragment
            fragment = StoryFragment(
                key=sanitized_data['key'],
                text=sanitized_data.get('text', ''),
                character=sanitized_data.get('character', 'Lucien'),
                level=sanitized_data.get('level', 1),
                min_besitos=sanitized_data.get('min_besitos', 0),
                required_role=sanitized_data.get('required_role'),
                reward_besitos=sanitized_data.get('reward_besitos', 0),
                unlocks_achievement_id=sanitized_data.get('unlocks_achievement_id'),
                auto_next_fragment_key=sanitized_data.get('auto_next_fragment_key')
            )
            
            self.session.add(fragment)
            await self.session.commit()
            await self.session.refresh(fragment)
            
            # Process decisions if provided
            if 'decisions' in sanitized_data:
                await self._process_fragment_decisions(fragment, sanitized_data['decisions'])
            
            logger.info(f"Successfully created story fragment: {fragment.key}")
            return {
                "status": "success",
                "fragment_id": fragment.id,
                "fragment_key": fragment.key
            }
            
        except Exception as e:
            logger.error(f"Error creating story fragment: {str(e)}")
            await self.session.rollback()
            return {
                "status": "error",
                "message": f"Failed to create fragment: {str(e)}"
            }

    async def update_story_fragment(self, fragment_id: str, updates: Dict) -> Result:
        """
        Updates an existing story fragment with validation and security measures.
        
        Args:
            fragment_id: Key of the fragment to update
            updates: Dictionary containing update data
            
        Returns:
            Result dictionary with status and any error messages
        """
        try:
            # Sanitize update data
            sanitized_updates = sanitize_fragment_content(updates)
            
            # Validate fragment data if we're updating content
            if any(field in sanitized_updates for field in ['text', 'key', 'character', 'decisions']):
                # Create a temporary fragment data dict for validation
                temp_fragment_data = sanitized_updates.copy()
                temp_fragment_data['key'] = fragment_id  # Add key for validation
                is_valid, errors = validate_story_fragment_data(temp_fragment_data)
                if not is_valid:
                    return {
                        "status": "validation_error",
                        "errors": errors
                    }
            
            # Find existing fragment
            stmt = select(StoryFragment).where(StoryFragment.key == fragment_id)
            result = await self.session.execute(stmt)
            fragment = result.scalar_one_or_none()
            
            if not fragment:
                return {
                    "status": "error",
                    "message": f"Fragment with key '{fragment_id}' not found"
                }
            
            # Apply updates
            if 'text' in sanitized_updates:
                fragment.text = sanitized_updates['text']
            if 'character' in sanitized_updates:
                fragment.character = sanitized_updates['character']
            if 'level' in sanitized_updates:
                fragment.level = sanitized_updates['level']
            if 'min_besitos' in sanitized_updates:
                fragment.min_besitos = sanitized_updates['min_besitos']
            if 'required_role' in sanitized_updates:
                fragment.required_role = sanitized_updates['required_role']
            if 'reward_besitos' in sanitized_updates:
                fragment.reward_besitos = sanitized_updates['reward_besitos']
            if 'unlocks_achievement_id' in sanitized_updates:
                fragment.unlocks_achievement_id = sanitized_updates['unlocks_achievement_id']
            if 'auto_next_fragment_key' in sanitized_updates:
                fragment.auto_next_fragment_key = sanitized_updates['auto_next_fragment_key']
            
            await self.session.commit()
            
            # Process decisions if provided
            if 'decisions' in sanitized_updates:
                await self._process_fragment_decisions(fragment, sanitized_updates['decisions'])
            
            logger.info(f"Successfully updated story fragment: {fragment.key}")
            return {
                "status": "success",
                "fragment_key": fragment.key
            }
            
        except Exception as e:
            logger.error(f"Error updating story fragment {fragment_id}: {str(e)}")
            await self.session.rollback()
            return {
                "status": "error",
                "message": f"Failed to update fragment: {str(e)}"
            }

    async def delete_story_fragment(self, fragment_id: str) -> Result:
        """
        Deletes a story fragment with security validation.
        
        Args:
            fragment_id: Key of the fragment to delete
            
        Returns:
            Result dictionary with status and any error messages
        """
        try:
            # Find existing fragment
            stmt = select(StoryFragment).where(StoryFragment.key == fragment_id)
            result = await self.session.execute(stmt)
            fragment = result.scalar_one_or_none()
            
            if not fragment:
                return {
                    "status": "error",
                    "message": f"Fragment with key '{fragment_id}' not found"
                }
            
            # Prevent deletion of 'start' fragment
            if fragment.key == "start":
                return {
                    "status": "error",
                    "message": "Cannot delete the 'start' fragment"
                }
            
            # Delete associated choices first (handled by cascade in model)
            await self.session.delete(fragment)
            await self.session.commit()
            
            logger.info(f"Successfully deleted story fragment: {fragment_id}")
            return {
                "status": "success",
                "fragment_key": fragment_id
            }
            
        except Exception as e:
            logger.error(f"Error deleting story fragment {fragment_id}: {str(e)}")
            await self.session.rollback()
            return {
                "status": "error",
                "message": f"Failed to delete fragment: {str(e)}"
            }

    async def get_fragment_with_analytics(self, fragment_id: str) -> Optional[FragmentAnalytics]:
        """
        Retrieves a fragment along with its analytics data.
        """
        # TODO: Implement fragment and analytics retrieval
        logger.info(f"Getting fragment with analytics for {fragment_id}")
        return None

    async def visualize_narrative_graph(self) -> GraphData:
        """
        Generates a representation of the narrative graph.
        """
        # TODO: Implement narrative graph visualization
        logger.info("Visualizing narrative graph")
        return {"graph": "not_implemented"}

    async def validate_narrative_consistency(self) -> ValidationReport:
        """
        Validates the consistency of the narrative graph.
        Checks for:
        - Orphaned fragments (unreachable from 'start').
        - Dead-end fragments (no outgoing choices or auto_next, not a designated end).
        - Broken links (choices pointing to non-existent fragments).
        """
        logger.info("Starting narrative consistency validation...")
        
        all_fragments_stmt = select(StoryFragment).options(selectinload(StoryFragment.choices))
        result = await self.session.execute(all_fragments_stmt)
        all_fragments = result.scalars().all()

        if not all_fragments:
            return {"status": "empty", "issues": ["No story fragments found in the database."]}

        fragment_map = {f.key: f for f in all_fragments}
        all_fragment_keys = set(fragment_map.keys())
        
        # --- Graph Traversal for Orphaned Fragments ---
        reachable_keys: Set[str] = set()
        q: List[str] = ["start"]
        
        if "start" not in fragment_map:
            return {"status": "error", "issues": ["'start' fragment not found."]}

        visited: Set[str] = set()
        while q:
            current_key = q.pop(0)
            if current_key in visited:
                continue
            
            visited.add(current_key)
            
            if current_key not in fragment_map:
                # This is a broken link, will be caught later
                continue

            reachable_keys.add(current_key)
            current_fragment = fragment_map[current_key]

            # Add destinations from choices
            for choice in current_fragment.choices:
                q.append(choice.destination_fragment_key)
            
            # Add destination from auto_next
            if current_fragment.auto_next_fragment_key:
                q.append(current_fragment.auto_next_fragment_key)

        orphaned_fragments = list(all_fragment_keys - reachable_keys)

        # --- Check for Dead Ends and Broken Links ---
        dead_end_fragments: List[str] = []
        broken_links: List[Dict[str, str]] = []

        for fragment in all_fragments:
            # Check for dead ends
            has_outgoing_edge = fragment.choices or fragment.auto_next_fragment_key
            if not has_outgoing_edge:
                # Assuming fragments without outgoing links are dead ends unless marked otherwise.
                # A more advanced implementation could have an `is_ending` flag.
                dead_end_fragments.append(fragment.key)

            # Check for broken links in choices
            for choice in fragment.choices:
                if choice.destination_fragment_key not in fragment_map:
                    broken_links.append({
                        "source": fragment.key,
                        "destination": choice.destination_fragment_key,
                        "choice_text": choice.text
                    })
            
            # Check for broken links in auto_next
            if fragment.auto_next_fragment_key and fragment.auto_next_fragment_key not in fragment_map:
                broken_links.append({
                    "source": fragment.key,
                    "destination": fragment.auto_next_fragment_key,
                    "choice_text": "auto_next"
                })

        report = {
            "orphaned_fragments": orphaned_fragments,
            "dead_end_fragments": dead_end_fragments,
            "broken_links": broken_links,
            "summary": {
                "total_fragments": len(all_fragment_keys),
                "reachable_fragments": len(reachable_keys),
                "orphaned_count": len(orphaned_fragments),
                "dead_end_count": len(dead_end_fragments),
                "broken_link_count": len(broken_links),
            }
        }
        
        if not orphaned_fragments and not dead_end_fragments and not broken_links:
            report["status"] = "ok"
            logger.info("Narrative consistency validation finished. No issues found.")
        else:
            report["status"] = "issues_found"
            logger.warning(f"Narrative consistency validation finished. Issues found: {report['summary']}")

        return report

    async def bulk_import_narrative_content(self, file_data: bytes) -> ImportResult:
        """
        Bulk imports narrative content from a file with validation and security measures.
        
        Args:
            file_data: JSON file data as bytes
            
        Returns:
            ImportResult dictionary with status and import statistics
        """
        try:
            # Parse JSON data
            json_data = json.loads(file_data.decode('utf-8'))
            
            # Validate JSON structure
            is_valid, errors = validate_json_structure(json_data)
            if not is_valid:
                return {
                    "status": "validation_error",
                    "errors": errors,
                    "imported_count": 0
                }
            
            imported_count = 0
            failed_count = 0
            failed_fragments = []
            
            # Process fragments
            fragments_to_process = []
            if 'fragments' in json_data:
                fragments_to_process = json_data['fragments']
            else:
                fragments_to_process = [json_data]
            
            for i, fragment_data in enumerate(fragments_to_process):
                try:
                    # Sanitize and validate each fragment
                    sanitized_data = sanitize_fragment_content(fragment_data)
                    is_valid, validation_errors = validate_story_fragment_data(sanitized_data)
                    
                    if not is_valid:
                        failed_count += 1
                        failed_fragments.append({
                            "index": i,
                            "key": sanitized_data.get('key', 'unknown'),
                            "errors": validation_errors
                        })
                        continue
                    
                    # Check if fragment exists
                    existing_fragment = await self.session.execute(
                        select(StoryFragment).where(StoryFragment.key == sanitized_data['key'])
                    )
                    
                    if existing_fragment.scalar_one_or_none():
                        # Update existing fragment
                        fragment = existing_fragment.scalar_one_or_none()
                        fragment.text = sanitized_data.get('text', fragment.text)
                        fragment.character = sanitized_data.get('character', fragment.character)
                        fragment.level = sanitized_data.get('level', fragment.level)
                        fragment.min_besitos = sanitized_data.get('min_besitos', fragment.min_besitos)
                        fragment.required_role = sanitized_data.get('required_role', fragment.required_role)
                        fragment.reward_besitos = sanitized_data.get('reward_besitos', fragment.reward_besitos)
                        fragment.unlocks_achievement_id = sanitized_data.get('unlocks_achievement_id', fragment.unlocks_achievement_id)
                        fragment.auto_next_fragment_key = sanitized_data.get('auto_next_fragment_key', fragment.auto_next_fragment_key)
                        
                        # Process decisions if provided
                        if 'decisions' in sanitized_data:
                            await self._process_fragment_decisions(fragment, sanitized_data['decisions'])
                    else:
                        # Create new fragment
                        fragment = StoryFragment(
                            key=sanitized_data['key'],
                            text=sanitized_data.get('text', ''),
                            character=sanitized_data.get('character', 'Lucien'),
                            level=sanitized_data.get('level', 1),
                            min_besitos=sanitized_data.get('min_besitos', 0),
                            required_role=sanitized_data.get('required_role'),
                            reward_besitos=sanitized_data.get('reward_besitos', 0),
                            unlocks_achievement_id=sanitized_data.get('unlocks_achievement_id'),
                            auto_next_fragment_key=sanitized_data.get('auto_next_fragment_key')
                        )
                        
                        self.session.add(fragment)
                        await self.session.flush()  # Get the ID without committing yet
                        
                        # Process decisions if provided
                        if 'decisions' in sanitized_data:
                            await self._process_fragment_decisions(fragment, sanitized_data['decisions'])
                    
                    imported_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    failed_fragments.append({
                        "index": i,
                        "key": fragment_data.get('key', 'unknown'),
                        "errors": [str(e)]
                    })
            
            # Commit all changes
            await self.session.commit()
            
            logger.info(f"Bulk import completed: {imported_count} imported, {failed_count} failed")
            return {
                "status": "success" if failed_count == 0 else "partial_success",
                "imported_count": imported_count,
                "failed_count": failed_count,
                "failed_fragments": failed_fragments
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in bulk import: {str(e)}")
            return {
                "status": "error",
                "message": f"Invalid JSON format: {str(e)}",
                "imported_count": 0
            }
        except Exception as e:
            logger.error(f"Error during bulk import: {str(e)}")
            await self.session.rollback()
            return {
                "status": "error",
                "message": f"Failed to import content: {str(e)}",
                "imported_count": 0
            }

    async def _process_fragment_decisions(self, fragment: StoryFragment, decisions: List[Dict[str, Any]]):
        """
        Processes the decisions for a fragment with validation.
        
        Args:
            fragment: StoryFragment to process decisions for
            decisions: List of decision dictionaries
        """
        # Delete existing decisions
        stmt = select(NarrativeChoice).where(NarrativeChoice.source_fragment_id == fragment.id)
        result = await self.session.execute(stmt)
        existing_choices = result.scalars().all()
        
        for choice in existing_choices:
            await self.session.delete(choice)
        
        await self.session.commit()

        # Create new decisions with validation
        for decision in decisions:
            next_fragment_key = decision.get('next_fragment') or decision.get('destination_key')
            if not next_fragment_key:
                continue
            
            # Validate decision data
            if 'text' not in decision or not decision['text']:
                logger.warning(f"Skipping decision with empty text for fragment {fragment.key}")
                continue
            
            if not isinstance(decision.get('text', ''), str) or len(decision['text']) > 500:
                logger.warning(f"Skipping decision with invalid text for fragment {fragment.key}")
                continue
            
            # Validate required_besitos
            required_besitos = decision.get('required_besitos', 0)
            if not isinstance(required_besitos, int) or required_besitos < 0:
                required_besitos = 0
            
            # Validate required_role
            required_role = decision.get('required_role')
            if required_role is not None and required_role not in ['free', 'vip', 'admin']:
                required_role = None
            
            choice = NarrativeChoice(
                source_fragment_id=fragment.id,
                destination_fragment_key=next_fragment_key,
                text=decision.get('text', ''),
                required_besitos=required_besitos,
                required_role=required_role
            )
            self.session.add(choice)
        
        await self.session.commit()
