/**
 * Header Component with file operations and actions
 */

import { useState } from 'react';
import { useNarrativeStore } from '../stores/narrativeStore';
import { openNarrativeFile, saveNarrativeFile, createNewNarrativeFile } from '../utils/fileSystem';
import { validateNarrative } from '../utils/validation';

export default function Header() {
  const narrative = useNarrativeStore((state) => state.narrative);
  const fileHandle = useNarrativeStore((state) => state.fileHandle);
  const isDirty = useNarrativeStore((state) => state.isDirty);
  const setNarrative = useNarrativeStore((state) => state.setNarrative);
  const markClean = useNarrativeStore((state) => state.markClean);

  const [isLoading, setIsLoading] = useState(false);
  const [showValidation, setShowValidation] = useState(false);
  const [validationResult, setValidationResult] = useState<ReturnType<typeof validateNarrative> | null>(null);

  const handleOpenFile = async () => {
    try {
      setIsLoading(true);
      const { handle, content } = await openNarrativeFile();
      setNarrative(content, handle);
    } catch (error) {
      if ((error as Error).message !== 'File selection cancelled') {
        alert(`Error al abrir archivo: ${(error as Error).message}`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveFile = async () => {
    if (!narrative || !fileHandle) return;

    try {
      setIsLoading(true);
      await saveNarrativeFile(fileHandle, narrative);
      markClean();
      alert('✅ Archivo guardado exitosamente');
    } catch (error) {
      alert(`Error al guardar: ${(error as Error).message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewFile = async () => {
    try {
      setIsLoading(true);
      const { handle, content } = await createNewNarrativeFile();
      setNarrative(content, handle);
    } catch (error) {
      if ((error as Error).message !== 'File creation cancelled') {
        alert(`Error al crear archivo: ${(error as Error).message}`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleValidate = () => {
    if (!narrative) return;

    const result = validateNarrative(narrative);
    setValidationResult(result);
    setShowValidation(true);
  };

  return (
    <>
      <header className="bg-gray-900 text-white p-4 flex items-center justify-between shadow-lg">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold">📖 Editor de Narrativa</h1>
          {isDirty && <span className="text-yellow-400 text-sm">● Sin guardar</span>}
        </div>

        <div className="flex gap-2">
          <button
            onClick={handleNewFile}
            disabled={isLoading}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded disabled:opacity-50"
          >
            📄 Nuevo
          </button>

          <button
            onClick={handleOpenFile}
            disabled={isLoading}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded disabled:opacity-50"
          >
            📂 Abrir JSON
          </button>

          <button
            onClick={handleSaveFile}
            disabled={isLoading || !narrative || !fileHandle || !isDirty}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded disabled:opacity-50"
          >
            💾 Guardar
          </button>

          <button
            onClick={handleValidate}
            disabled={!narrative}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded disabled:opacity-50"
          >
            ✅ Validar
          </button>
        </div>
      </header>

      {/* Validation Modal */}
      {showValidation && validationResult && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold">
                {validationResult.isValid ? '✅ Narrativa Válida' : '❌ Errores Encontrados'}
              </h2>
              <button
                onClick={() => setShowValidation(false)}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ×
              </button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4 mb-4 p-4 bg-gray-100 rounded">
              <div>
                <div className="text-sm text-gray-600">Fragmentos</div>
                <div className="text-xl font-bold">{validationResult.stats.totalFragments}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Decisiones</div>
                <div className="text-xl font-bold">{validationResult.stats.totalChoices}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Productos</div>
                <div className="text-xl font-bold">{validationResult.stats.totalShopItems}</div>
              </div>
            </div>

            {/* Errors */}
            {validationResult.errors.length > 0 && (
              <div className="space-y-2">
                <h3 className="font-bold text-lg">Problemas:</h3>
                {validationResult.errors.map((error, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded ${
                      error.severity === 'error' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                    }`}
                  >
                    <div className="font-bold">{error.type}</div>
                    <div className="text-sm">{error.message}</div>
                    <div className="text-xs opacity-70">{error.location}</div>
                  </div>
                ))}
              </div>
            )}

            <button
              onClick={() => setShowValidation(false)}
              className="mt-4 w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Cerrar
            </button>
          </div>
        </div>
      )}
    </>
  );
}
