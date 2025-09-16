import logging
from typing import Dict, Any, List, Optional, Type, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database.narrative_models import StoryFragment, NarrativeChoice, FragmentAnalytics

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
        Creates a new story fragment.
        """
        # TODO: Implement fragment creation logic
        logger.info(f"Creating story fragment with data: {fragment_data}")
        return {"status": "not_implemented"}

    async def update_story_fragment(self, fragment_id: str, updates: Dict) -> Result:
        """
        Updates an existing story fragment.
        """
        # TODO: Implement fragment update logic
        logger.info(f"Updating story fragment {fragment_id} with updates: {updates}")
        return {"status": "not_implemented"}

    async def delete_story_fragment(self, fragment_id: str) -> Result:
        """
        Deletes a story fragment.
        """
        # TODO: Implement fragment deletion logic
        logger.info(f"Deleting story fragment {fragment_id}")
        return {"status": "not_implemented"}

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
        Bulk imports narrative content from a file.
        """
        # TODO: Implement bulk import logic
        logger.info("Bulk importing narrative content")
        return {"status": "not_implemented"}
