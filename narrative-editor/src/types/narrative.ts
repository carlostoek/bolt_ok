/**
 * TypeScript types for narrative configuration
 */

export interface NarrativeConfig {
  version: string;
  metadata?: {
    last_updated?: string;
    updated_by?: string;
    description?: string;
  };
  fragments: StoryFragment[];
  shop_items?: ShopItem[];
  lore_pieces?: LorePiece[];
  hint_combinations?: HintCombination[];
}

export interface StoryFragment {
  key: string;
  text: string;
  character: "Lucien" | "Diana";
  level?: number;
  min_besitos?: number;
  reward_besitos?: number;
  required_role?: "free" | "vip" | null;
  image_url?: string | null;
  unlocks_achievement_id?: string | null;
  auto_next_fragment_key?: string | null;
  archetype_variant?: "adventurer" | "romantic" | "explorer" | "balanced" | null;
  choices?: NarrativeChoice[];
  visual_position?: {
    x: number;
    y: number;
  };
}

export interface NarrativeChoice {
  text: string;
  destination_fragment_key: string;
  required_besitos?: number;
  required_role?: "free" | "vip" | null;
}

export interface ShopItem {
  name: string;
  description?: string;
  price: number;
  is_vip_only?: boolean;
  unlocks_fragment_key?: string | null;
  unlocks_lore_piece_code?: string | null;
  image_file_id?: string | null;
  stock_limit?: number | null;
  max_purchases_per_user?: number;
  is_active?: boolean;
}

export interface LorePiece {
  code_name: string;
  title: string;
  description?: string;
  content: string;
  content_type?: "text" | "image" | "video";
  category?: string;
  is_main_story?: boolean;
}

export interface HintCombination {
  combination_code: string;
  required_hints: string[];
  reward_code: string;
}

// React Flow node data types
export interface FragmentNodeData {
  fragment: StoryFragment;
}

export interface ShopNodeData {
  item: ShopItem;
}

export interface LoreNodeData {
  lore: LorePiece;
}

// Validation types
export interface ValidationError {
  type: "missing_fragment" | "broken_reference" | "duplicate_key" | "invalid_data";
  message: string;
  location: string;
  severity: "error" | "warning";
}

export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  stats: {
    totalFragments: number;
    totalChoices: number;
    totalShopItems: number;
    totalLorePieces: number;
    totalCombinations: number;
    orphanedFragments: number;
    brokenReferences: number;
  };
}
