/**
 * File System Access API utilities
 * Browser-native file system access
 */

import type { NarrativeConfig } from '../types/narrative';

export interface FileHandle {
  handle: FileSystemFileHandle;
  content: NarrativeConfig;
}

/**
 * Open a JSON file from the user's file system
 */
export async function openNarrativeFile(): Promise<FileHandle> {
  // Check if File System Access API is supported
  if (!('showOpenFilePicker' in window)) {
    throw new Error('File System Access API not supported in this browser');
  }

  try {
    const [fileHandle] = await window.showOpenFilePicker({
      types: [
        {
          description: 'JSON Files',
          accept: {
            'application/json': ['.json'],
          },
        },
      ],
      multiple: false,
    });

    const file = await fileHandle.getFile();
    const text = await file.text();
    const content = JSON.parse(text) as NarrativeConfig;

    return { handle: fileHandle, content };
  } catch (error) {
    if ((error as Error).name === 'AbortError') {
      throw new Error('File selection cancelled');
    }
    throw error;
  }
}

/**
 * Save narrative config to file
 */
export async function saveNarrativeFile(
  handle: FileSystemFileHandle,
  content: NarrativeConfig
): Promise<void> {
  try {
    const writable = await handle.createWritable();
    const jsonString = JSON.stringify(content, null, 2);
    await writable.write(jsonString);
    await writable.close();
  } catch (error) {
    throw new Error(`Failed to save file: ${(error as Error).message}`);
  }
}

/**
 * Create a new narrative file
 */
export async function createNewNarrativeFile(): Promise<FileHandle> {
  if (!('showSaveFilePicker' in window)) {
    throw new Error('File System Access API not supported in this browser');
  }

  try {
    const handle = await window.showSaveFilePicker({
      suggestedName: 'narrative_complete.json',
      types: [
        {
          description: 'JSON Files',
          accept: {
            'application/json': ['.json'],
          },
        },
      ],
    });

    const defaultContent: NarrativeConfig = {
      version: '1.0',
      metadata: {
        last_updated: new Date().toISOString(),
        updated_by: 'admin',
        description: 'Nueva configuración de narrativa',
      },
      fragments: [
        {
          key: 'start',
          text: '🎩 **Lucien:** Bienvenido...',
          character: 'Lucien',
          level: 1,
          min_besitos: 0,
          reward_besitos: 5,
          choices: [],
          visual_position: { x: 250, y: 0 },
        },
      ],
      shop_items: [],
      lore_pieces: [],
      hint_combinations: [],
    };

    await saveNarrativeFile(handle, defaultContent);

    return { handle, content: defaultContent };
  } catch (error) {
    if ((error as Error).name === 'AbortError') {
      throw new Error('File creation cancelled');
    }
    throw error;
  }
}

/**
 * Download narrative as JSON (fallback for unsupported browsers)
 */
export function downloadNarrativeAsJSON(content: NarrativeConfig, filename: string = 'narrative_complete.json'): void {
  const jsonString = JSON.stringify(content, null, 2);
  const blob = new Blob([jsonString], { type: 'application/json' });
  const url = URL.createObjectURL(blob);

  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
