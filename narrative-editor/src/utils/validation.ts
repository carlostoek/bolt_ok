/**
 * Narrative validation utilities
 */

import type { NarrativeConfig, ValidationResult, ValidationError } from '../types/narrative';

export function validateNarrative(data: NarrativeConfig): ValidationResult {
  const errors: ValidationError[] = [];

  // Create sets for quick lookup
  const fragmentKeys = new Set(data.fragments.map((f) => f.key));
  const loreCodeNames = new Set(data.lore_pieces?.map((l) => l.code_name) || []);

  // Track referenced fragments
  const referencedFragments = new Set<string>();
  let totalChoices = 0;

  // Validate fragments
  const fragmentKeysSeen = new Set<string>();
  data.fragments.forEach((fragment, index) => {
    // Check for duplicate keys
    if (fragmentKeysSeen.has(fragment.key)) {
      errors.push({
        type: 'duplicate_key',
        message: `Duplicate fragment key: "${fragment.key}"`,
        location: `fragments[${index}]`,
        severity: 'error',
      });
    }
    fragmentKeysSeen.add(fragment.key);

    // Validate choices
    fragment.choices?.forEach((choice, choiceIndex) => {
      totalChoices++;
      const dest = choice.destination_fragment_key;

      if (!dest) {
        errors.push({
          type: 'invalid_data',
          message: `Choice missing destination_fragment_key`,
          location: `fragments[${index}].choices[${choiceIndex}]`,
          severity: 'error',
        });
      } else {
        referencedFragments.add(dest);

        if (!fragmentKeys.has(dest)) {
          errors.push({
            type: 'missing_fragment',
            message: `Choice references non-existent fragment: "${dest}"`,
            location: `fragments[${index}].choices[${choiceIndex}]`,
            severity: 'error',
          });
        }
      }
    });

    // Validate auto_next
    if (fragment.auto_next_fragment_key) {
      referencedFragments.add(fragment.auto_next_fragment_key);
      if (!fragmentKeys.has(fragment.auto_next_fragment_key)) {
        errors.push({
          type: 'missing_fragment',
          message: `auto_next references non-existent fragment: "${fragment.auto_next_fragment_key}"`,
          location: `fragments[${index}]`,
          severity: 'error',
        });
      }
    }
  });

  // Validate shop items
  data.shop_items?.forEach((item, index) => {
    if (item.unlocks_fragment_key && !fragmentKeys.has(item.unlocks_fragment_key)) {
      errors.push({
        type: 'broken_reference',
        message: `Shop item "${item.name}" references non-existent fragment: "${item.unlocks_fragment_key}"`,
        location: `shop_items[${index}]`,
        severity: 'error',
      });
    }

    if (item.unlocks_lore_piece_code && !loreCodeNames.has(item.unlocks_lore_piece_code)) {
      errors.push({
        type: 'broken_reference',
        message: `Shop item "${item.name}" references non-existent lore piece: "${item.unlocks_lore_piece_code}"`,
        location: `shop_items[${index}]`,
        severity: 'warning',
      });
    }
  });

  // Validate hint combinations
  data.hint_combinations?.forEach((combo, index) => {
    combo.required_hints.forEach((hint) => {
      if (!loreCodeNames.has(hint)) {
        errors.push({
          type: 'broken_reference',
          message: `Combination "${combo.combination_code}" references non-existent hint: "${hint}"`,
          location: `hint_combinations[${index}]`,
          severity: 'error',
        });
      }
    });

    if (!loreCodeNames.has(combo.reward_code)) {
      errors.push({
        type: 'broken_reference',
        message: `Combination "${combo.combination_code}" has non-existent reward: "${combo.reward_code}"`,
        location: `hint_combinations[${index}]`,
        severity: 'error',
      });
    }
  });

  // Find orphaned fragments (no incoming references, except "start")
  const orphanedFragments = data.fragments.filter(
    (f) => f.key !== 'start' && !referencedFragments.has(f.key)
  );

  orphanedFragments.forEach((fragment) => {
    errors.push({
      type: 'broken_reference',
      message: `Fragment "${fragment.key}" is orphaned (no incoming connections)`,
      location: `fragments`,
      severity: 'warning',
    });
  });

  // Calculate stats
  const stats = {
    totalFragments: data.fragments.length,
    totalChoices,
    totalShopItems: data.shop_items?.length || 0,
    totalLorePieces: data.lore_pieces?.length || 0,
    totalCombinations: data.hint_combinations?.length || 0,
    orphanedFragments: orphanedFragments.length,
    brokenReferences: errors.filter((e) => e.type === 'broken_reference' || e.type === 'missing_fragment').length,
  };

  return {
    isValid: errors.filter((e) => e.severity === 'error').length === 0,
    errors,
    stats,
  };
}
