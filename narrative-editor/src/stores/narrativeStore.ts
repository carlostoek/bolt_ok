/**
 * Zustand store for narrative editor state
 */

import { create } from 'zustand';
import type { NarrativeConfig, StoryFragment, NarrativeChoice, ShopItem, LorePiece, HintCombination } from '../types/narrative';

interface NarrativeStore {
  // Data state
  narrative: NarrativeConfig | null;
  fileHandle: FileSystemFileHandle | null;
  isDirty: boolean;
  selectedNodeId: string | null;

  // Actions
  setNarrative: (narrative: NarrativeConfig, handle?: FileSystemFileHandle) => void;
  setFileHandle: (handle: FileSystemFileHandle) => void;
  markDirty: () => void;
  markClean: () => void;
  setSelectedNode: (nodeId: string | null) => void;

  // Fragment operations
  addFragment: (fragment: StoryFragment) => void;
  updateFragment: (key: string, updates: Partial<StoryFragment>) => void;
  deleteFragment: (key: string) => void;
  getFragment: (key: string) => StoryFragment | undefined;

  // Choice operations
  addChoice: (fragmentKey: string, choice: NarrativeChoice) => void;
  updateChoice: (fragmentKey: string, choiceIndex: number, updates: Partial<NarrativeChoice>) => void;
  deleteChoice: (fragmentKey: string, choiceIndex: number) => void;

  // Shop operations
  addShopItem: (item: ShopItem) => void;
  updateShopItem: (name: string, updates: Partial<ShopItem>) => void;
  deleteShopItem: (name: string) => void;

  // Lore operations
  addLorePiece: (lore: LorePiece) => void;
  updateLorePiece: (codeName: string, updates: Partial<LorePiece>) => void;
  deleteLorePiece: (codeName: string) => void;

  // Hint combination operations
  addHintCombination: (combo: HintCombination) => void;
  updateHintCombination: (code: string, updates: Partial<HintCombination>) => void;
  deleteHintCombination: (code: string) => void;

  // Utility
  reset: () => void;
}

export const useNarrativeStore = create<NarrativeStore>((set, get) => ({
  // Initial state
  narrative: null,
  fileHandle: null,
  isDirty: false,
  selectedNodeId: null,

  // Actions
  setNarrative: (narrative, handle) => {
    set({ narrative, fileHandle: handle || null, isDirty: false });
  },

  setFileHandle: (handle) => {
    set({ fileHandle: handle });
  },

  markDirty: () => {
    set({ isDirty: true });
  },

  markClean: () => {
    set({ isDirty: false });
  },

  setSelectedNode: (nodeId) => {
    set({ selectedNodeId: nodeId });
  },

  // Fragment operations
  addFragment: (fragment) => {
    const { narrative } = get();
    if (!narrative) return;

    set({
      narrative: {
        ...narrative,
        fragments: [...narrative.fragments, fragment],
      },
      isDirty: true,
    });
  },

  updateFragment: (key, updates) => {
    const { narrative } = get();
    if (!narrative) return;

    set({
      narrative: {
        ...narrative,
        fragments: narrative.fragments.map((f) =>
          f.key === key ? { ...f, ...updates } : f
        ),
      },
      isDirty: true,
    });
  },

  deleteFragment: (key) => {
    const { narrative } = get();
    if (!narrative) return;

    set({
      narrative: {
        ...narrative,
        fragments: narrative.fragments.filter((f) => f.key !== key),
      },
      isDirty: true,
    });
  },

  getFragment: (key) => {
    const { narrative } = get();
    return narrative?.fragments.find((f) => f.key === key);
  },

  // Choice operations
  addChoice: (fragmentKey, choice) => {
    const { narrative } = get();
    if (!narrative) return;

    set({
      narrative: {
        ...narrative,
        fragments: narrative.fragments.map((f) =>
          f.key === fragmentKey
            ? { ...f, choices: [...(f.choices || []), choice] }
            : f
        ),
      },
      isDirty: true,
    });
  },

  updateChoice: (fragmentKey, choiceIndex, updates) => {
    const { narrative } = get();
    if (!narrative) return;

    set({
      narrative: {
        ...narrative,
        fragments: narrative.fragments.map((f) =>
          f.key === fragmentKey
            ? {
                ...f,
                choices: f.choices?.map((c, i) =>
                  i === choiceIndex ? { ...c, ...updates } : c
                ),
              }
            : f
        ),
      },
      isDirty: true,
    });
  },

  deleteChoice: (fragmentKey, choiceIndex) => {
    const { narrative } = get();
    if (!narrative) return;

    set({
      narrative: {
        ...narrative,
        fragments: narrative.fragments.map((f) =>
          f.key === fragmentKey
            ? {
                ...f,
                choices: f.choices?.filter((_, i) => i !== choiceIndex),
              }
            : f
        ),
      },
      isDirty: true,
    });
  },

  // Shop operations
  addShopItem: (item) => {
    const { narrative } = get();
    if (!narrative) return;

    set({
      narrative: {
        ...narrative,
        shop_items: [...(narrative.shop_items || []), item],
      },
      isDirty: true,
    });
  },

  updateShopItem: (name, updates) => {
    const { narrative } = get();
    if (!narrative) return;

    set({
      narrative: {
        ...narrative,
        shop_items: narrative.shop_items?.map((item) =>
          item.name === name ? { ...item, ...updates } : item
        ),
      },
      isDirty: true,
    });
  },

  deleteShopItem: (name) => {
    const { narrative } = get();
    if (!narrative) return;

    set({
      narrative: {
        ...narrative,
        shop_items: narrative.shop_items?.filter((item) => item.name !== name),
      },
      isDirty: true,
    });
  },

  // Lore operations
  addLorePiece: (lore) => {
    const { narrative } = get();
    if (!narrative) return;

    set({
      narrative: {
        ...narrative,
        lore_pieces: [...(narrative.lore_pieces || []), lore],
      },
      isDirty: true,
    });
  },

  updateLorePiece: (codeName, updates) => {
    const { narrative } = get();
    if (!narrative) return;

    set({
      narrative: {
        ...narrative,
        lore_pieces: narrative.lore_pieces?.map((lore) =>
          lore.code_name === codeName ? { ...lore, ...updates } : lore
        ),
      },
      isDirty: true,
    });
  },

  deleteLorePiece: (codeName) => {
    const { narrative } = get();
    if (!narrative) return;

    set({
      narrative: {
        ...narrative,
        lore_pieces: narrative.lore_pieces?.filter((lore) => lore.code_name !== codeName),
      },
      isDirty: true,
    });
  },

  // Hint combination operations
  addHintCombination: (combo) => {
    const { narrative } = get();
    if (!narrative) return;

    set({
      narrative: {
        ...narrative,
        hint_combinations: [...(narrative.hint_combinations || []), combo],
      },
      isDirty: true,
    });
  },

  updateHintCombination: (code, updates) => {
    const { narrative } = get();
    if (!narrative) return;

    set({
      narrative: {
        ...narrative,
        hint_combinations: narrative.hint_combinations?.map((combo) =>
          combo.combination_code === code ? { ...combo, ...updates } : combo
        ),
      },
      isDirty: true,
    });
  },

  deleteHintCombination: (code) => {
    const { narrative } = get();
    if (!narrative) return;

    set({
      narrative: {
        ...narrative,
        hint_combinations: narrative.hint_combinations?.filter(
          (combo) => combo.combination_code !== code
        ),
      },
      isDirty: true,
    });
  },

  // Utility
  reset: () => {
    set({
      narrative: null,
      fileHandle: null,
      isDirty: false,
      selectedNodeId: null,
    });
  },
}));
