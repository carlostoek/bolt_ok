"""
Complete Narrative Loader - Loads full narrative configuration from JSON.
Supports fragments, shop items, lore pieces, and hint combinations.
"""
import json
import logging
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from database.narrative_models import StoryFragment, NarrativeChoice
from database.models import ShopItem, LorePiece
from database.hint_combination import HintCombination

logger = logging.getLogger(__name__)


class CompleteNarrativeLoader:
    """Loads complete narrative configuration from a single JSON file."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.stats = {
            "fragments_created": 0,
            "fragments_updated": 0,
            "choices_created": 0,
            "shop_items_created": 0,
            "shop_items_updated": 0,
            "lore_pieces_created": 0,
            "lore_pieces_updated": 0,
            "combinations_created": 0,
            "combinations_updated": 0
        }

    async def load_from_file(self, filepath: str) -> Dict[str, int]:
        """
        Load complete narrative configuration from JSON file.

        :param filepath: Path to JSON file
        :return: Statistics dict with counts of created/updated items
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                data = json.load(file)

            logger.info(f"Loading narrative from {filepath}")

            # Validate JSON structure
            if not self._validate_json(data):
                raise ValueError("Invalid JSON structure")

            # Load in order: fragments -> shop -> lore -> combinations
            await self._load_fragments(data.get("fragments", []))
            await self._load_shop_items(data.get("shop_items", []))
            await self._load_lore_pieces(data.get("lore_pieces", []))
            await self._load_hint_combinations(data.get("hint_combinations", []))

            logger.info(f"Load complete: {self.stats}")
            return self.stats

        except FileNotFoundError:
            logger.error(f"File not found: {filepath}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {filepath}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading narrative from {filepath}: {e}")
            raise

    def _validate_json(self, data: Dict) -> bool:
        """Validate JSON structure."""
        required_keys = ["version", "fragments"]
        for key in required_keys:
            if key not in data:
                logger.error(f"Missing required key: {key}")
                return False
        return True

    async def _load_fragments(self, fragments: list):
        """Load all story fragments and their choices."""
        for fragment_data in fragments:
            await self._upsert_fragment(fragment_data)

    async def _upsert_fragment(self, data: Dict[str, Any]):
        """Insert or update a story fragment."""
        fragment_key = data.get("key")
        if not fragment_key:
            logger.warning("Fragment without key, skipping")
            return

        # Check if fragment exists
        stmt = select(StoryFragment).where(StoryFragment.key == fragment_key)
        result = await self.session.execute(stmt)
        fragment = result.scalar_one_or_none()

        if fragment:
            # Update existing
            fragment.text = data.get("text", fragment.text)
            fragment.character = data.get("character", fragment.character)
            fragment.level = data.get("level", fragment.level)
            fragment.min_besitos = data.get("min_besitos", fragment.min_besitos)
            fragment.reward_besitos = data.get("reward_besitos", fragment.reward_besitos)
            fragment.required_role = data.get("required_role")
            fragment.image_url = data.get("image_url")
            fragment.unlocks_achievement_id = data.get("unlocks_achievement_id")
            fragment.auto_next_fragment_key = data.get("auto_next_fragment_key")
            fragment.archetype_variant = data.get("archetype_variant")

            self.stats["fragments_updated"] += 1
            logger.debug(f"Updated fragment: {fragment_key}")
        else:
            # Create new
            fragment = StoryFragment(
                key=fragment_key,
                text=data.get("text", ""),
                character=data.get("character", "Lucien"),
                level=data.get("level", 1),
                min_besitos=data.get("min_besitos", 0),
                reward_besitos=data.get("reward_besitos", 0),
                required_role=data.get("required_role"),
                image_url=data.get("image_url"),
                unlocks_achievement_id=data.get("unlocks_achievement_id"),
                auto_next_fragment_key=data.get("auto_next_fragment_key"),
                archetype_variant=data.get("archetype_variant")
            )
            self.session.add(fragment)
            await self.session.flush()

            self.stats["fragments_created"] += 1
            logger.debug(f"Created fragment: {fragment_key}")

        await self.session.flush()
        await self.session.refresh(fragment)

        # Process choices
        await self._process_choices(fragment, data.get("choices", []))

        await self.session.commit()

    async def _process_choices(self, fragment: StoryFragment, choices: list):
        """Process choices for a fragment."""
        # Delete existing choices
        stmt = delete(NarrativeChoice).where(NarrativeChoice.source_fragment_id == fragment.id)
        await self.session.execute(stmt)

        # Create new choices
        for choice_data in choices:
            choice = NarrativeChoice(
                source_fragment_id=fragment.id,
                destination_fragment_key=choice_data.get("destination_fragment_key", ""),
                text=choice_data.get("text", ""),
                required_besitos=choice_data.get("required_besitos", 0),
                required_role=choice_data.get("required_role")
            )
            self.session.add(choice)
            self.stats["choices_created"] += 1

    async def _load_shop_items(self, items: list):
        """Load shop items."""
        for item_data in items:
            await self._upsert_shop_item(item_data)

    async def _upsert_shop_item(self, data: Dict[str, Any]):
        """Insert or update a shop item."""
        item_name = data.get("name")
        if not item_name:
            logger.warning("Shop item without name, skipping")
            return

        # Check if item exists by name
        stmt = select(ShopItem).where(ShopItem.name == item_name)
        result = await self.session.execute(stmt)
        item = result.scalar_one_or_none()

        if item:
            # Update existing
            item.description = data.get("description", item.description)
            item.price = data.get("price", item.price)
            item.is_vip_only = data.get("is_vip_only", item.is_vip_only)
            item.unlocks_fragment_key = data.get("unlocks_fragment_key")
            item.image_file_id = data.get("image_file_id")
            item.stock_limit = data.get("stock_limit")
            item.max_purchases_per_user = data.get("max_purchases_per_user", 1)
            item.is_active = data.get("is_active", True)

            # Handle lore piece link
            lore_code = data.get("unlocks_lore_piece_code")
            if lore_code:
                lore_stmt = select(LorePiece).where(LorePiece.code_name == lore_code)
                lore_result = await self.session.execute(lore_stmt)
                lore_piece = lore_result.scalar_one_or_none()
                if lore_piece:
                    item.unlocks_lore_piece_id = lore_piece.id

            self.stats["shop_items_updated"] += 1
            logger.debug(f"Updated shop item: {item_name}")
        else:
            # Create new
            lore_id = None
            lore_code = data.get("unlocks_lore_piece_code")
            if lore_code:
                lore_stmt = select(LorePiece).where(LorePiece.code_name == lore_code)
                lore_result = await self.session.execute(lore_stmt)
                lore_piece = lore_result.scalar_one_or_none()
                if lore_piece:
                    lore_id = lore_piece.id

            item = ShopItem(
                name=item_name,
                description=data.get("description", ""),
                price=data.get("price", 0),
                is_vip_only=data.get("is_vip_only", False),
                unlocks_fragment_key=data.get("unlocks_fragment_key"),
                unlocks_lore_piece_id=lore_id,
                image_file_id=data.get("image_file_id"),
                stock_limit=data.get("stock_limit"),
                max_purchases_per_user=data.get("max_purchases_per_user", 1),
                is_active=data.get("is_active", True)
            )
            self.session.add(item)

            self.stats["shop_items_created"] += 1
            logger.debug(f"Created shop item: {item_name}")

        await self.session.commit()

    async def _load_lore_pieces(self, lore_pieces: list):
        """Load lore pieces."""
        for lore_data in lore_pieces:
            await self._upsert_lore_piece(lore_data)

    async def _upsert_lore_piece(self, data: Dict[str, Any]):
        """Insert or update a lore piece."""
        code_name = data.get("code_name")
        if not code_name:
            logger.warning("Lore piece without code_name, skipping")
            return

        # Check if exists
        stmt = select(LorePiece).where(LorePiece.code_name == code_name)
        result = await self.session.execute(stmt)
        lore = result.scalar_one_or_none()

        if lore:
            # Update
            lore.title = data.get("title", lore.title)
            lore.description = data.get("description", lore.description)
            lore.content = data.get("content", lore.content)
            lore.content_type = data.get("content_type", lore.content_type)
            lore.category = data.get("category", lore.category)
            lore.is_main_story = data.get("is_main_story", lore.is_main_story)

            self.stats["lore_pieces_updated"] += 1
            logger.debug(f"Updated lore piece: {code_name}")
        else:
            # Create
            lore = LorePiece(
                code_name=code_name,
                title=data.get("title", ""),
                description=data.get("description"),
                content=data.get("content", ""),
                content_type=data.get("content_type", "text"),
                category=data.get("category"),
                is_main_story=data.get("is_main_story", False)
            )
            self.session.add(lore)

            self.stats["lore_pieces_created"] += 1
            logger.debug(f"Created lore piece: {code_name}")

        await self.session.commit()

    async def _load_hint_combinations(self, combinations: list):
        """Load hint combinations."""
        for combo_data in combinations:
            await self._upsert_hint_combination(combo_data)

    async def _upsert_hint_combination(self, data: Dict[str, Any]):
        """Insert or update a hint combination."""
        combo_code = data.get("combination_code")
        if not combo_code:
            logger.warning("Hint combination without code, skipping")
            return

        # Check if exists
        stmt = select(HintCombination).where(HintCombination.combination_code == combo_code)
        result = await self.session.execute(stmt)
        combo = result.scalar_one_or_none()

        # Convert required_hints array to comma-separated string
        required_hints = data.get("required_hints", [])
        if isinstance(required_hints, list):
            required_hints_str = ",".join(sorted(required_hints))
        else:
            required_hints_str = required_hints

        if combo:
            # Update
            combo.required_hints = required_hints_str
            combo.reward_code = data.get("reward_code", combo.reward_code)

            self.stats["combinations_updated"] += 1
            logger.debug(f"Updated combination: {combo_code}")
        else:
            # Create
            combo = HintCombination(
                combination_code=combo_code,
                required_hints=required_hints_str,
                reward_code=data.get("reward_code", "")
            )
            self.session.add(combo)

            self.stats["combinations_created"] += 1
            logger.debug(f"Created combination: {combo_code}")

        await self.session.commit()
