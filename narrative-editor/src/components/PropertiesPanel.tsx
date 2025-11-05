/**
 * Properties Panel - Edit selected node
 */

import { useState, useEffect } from 'react';
import { useNarrativeStore } from '../stores/narrativeStore';
import type { StoryFragment, NarrativeChoice } from '../types/narrative';

export default function PropertiesPanel() {
  const narrative = useNarrativeStore((state) => state.narrative);
  const selectedNodeId = useNarrativeStore((state) => state.selectedNodeId);
  const setSelectedNode = useNarrativeStore((state) => state.setSelectedNode);
  const updateFragment = useNarrativeStore((state) => state.updateFragment);
  const addChoice = useNarrativeStore((state) => state.addChoice);
  const updateChoice = useNarrativeStore((state) => state.updateChoice);
  const deleteChoice = useNarrativeStore((state) => state.deleteChoice);

  const [editingFragment, setEditingFragment] = useState<StoryFragment | null>(null);

  useEffect(() => {
    if (selectedNodeId?.startsWith('fragment-')) {
      const key = selectedNodeId.replace('fragment-', '');
      const fragment = narrative?.fragments.find((f) => f.key === key);
      setEditingFragment(fragment || null);
    } else {
      setEditingFragment(null);
    }
  }, [selectedNodeId, narrative]);

  if (!selectedNodeId || !editingFragment) {
    return (
      <div className="w-80 bg-gray-50 border-l border-gray-300 p-4 overflow-y-auto">
        <div className="text-center text-gray-500 mt-20">
          <p className="text-lg mb-2">📋</p>
          <p>Selecciona un nodo para editar sus propiedades</p>
        </div>
      </div>
    );
  }

  const handleFieldChange = (field: keyof StoryFragment, value: any) => {
    updateFragment(editingFragment.key, { [field]: value });
    setEditingFragment({ ...editingFragment, [field]: value });
  };

  const handleAddChoice = () => {
    const newChoice: NarrativeChoice = {
      text: 'Nueva decisión',
      destination_fragment_key: 'start',
      required_besitos: 0,
    };
    addChoice(editingFragment.key, newChoice);
  };

  const handleUpdateChoice = (index: number, field: keyof NarrativeChoice, value: any) => {
    updateChoice(editingFragment.key, index, { [field]: value });
  };

  const handleDeleteChoice = (index: number) => {
    if (confirm('¿Eliminar esta decisión?')) {
      deleteChoice(editingFragment.key, index);
    }
  };

  return (
    <div className="w-96 bg-white border-l border-gray-300 overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 bg-gray-900 text-white p-4 flex justify-between items-center">
        <h2 className="text-lg font-bold">Propiedades</h2>
        <button
          onClick={() => setSelectedNode(null)}
          className="text-gray-300 hover:text-white text-xl"
        >
          ×
        </button>
      </div>

      <div className="p-4 space-y-4">
        {/* Key (read-only) */}
        <div>
          <label className="block text-sm font-bold text-gray-700 mb-1">
            🔑 Key (ID único)
          </label>
          <input
            type="text"
            value={editingFragment.key}
            disabled
            className="w-full p-2 border rounded bg-gray-100 text-gray-600 font-mono text-sm"
          />
        </div>

        {/* Character */}
        <div>
          <label className="block text-sm font-bold text-gray-700 mb-1">
            👤 Personaje
          </label>
          <select
            value={editingFragment.character}
            onChange={(e) => handleFieldChange('character', e.target.value as 'Lucien' | 'Diana')}
            className="w-full p-2 border rounded"
          >
            <option value="Lucien">🎩 Lucien</option>
            <option value="Diana">🌸 Diana</option>
          </select>
        </div>

        {/* Text */}
        <div>
          <label className="block text-sm font-bold text-gray-700 mb-1">
            📝 Texto
          </label>
          <textarea
            value={editingFragment.text}
            onChange={(e) => handleFieldChange('text', e.target.value)}
            rows={6}
            className="w-full p-2 border rounded text-sm"
            placeholder="Escribe el contenido del fragmento..."
          />
          <p className="text-xs text-gray-500 mt-1">
            {editingFragment.text.length} caracteres
          </p>
        </div>

        {/* Level */}
        <div>
          <label className="block text-sm font-bold text-gray-700 mb-1">
            📊 Nivel
          </label>
          <input
            type="number"
            value={editingFragment.level || 1}
            onChange={(e) => handleFieldChange('level', parseInt(e.target.value))}
            min={1}
            className="w-full p-2 border rounded"
          />
        </div>

        {/* Min Besitos */}
        <div>
          <label className="block text-sm font-bold text-gray-700 mb-1">
            💰 Besitos Requeridos
          </label>
          <input
            type="number"
            value={editingFragment.min_besitos || 0}
            onChange={(e) => handleFieldChange('min_besitos', parseInt(e.target.value))}
            min={0}
            className="w-full p-2 border rounded"
          />
        </div>

        {/* Reward Besitos */}
        <div>
          <label className="block text-sm font-bold text-gray-700 mb-1">
            🎁 Recompensa (Besitos)
          </label>
          <input
            type="number"
            value={editingFragment.reward_besitos || 0}
            onChange={(e) => handleFieldChange('reward_besitos', parseInt(e.target.value))}
            min={0}
            className="w-full p-2 border rounded"
          />
        </div>

        {/* Required Role */}
        <div>
          <label className="block text-sm font-bold text-gray-700 mb-1">
            👑 Rol Requerido
          </label>
          <select
            value={editingFragment.required_role || ''}
            onChange={(e) => handleFieldChange('required_role', e.target.value || null)}
            className="w-full p-2 border rounded"
          >
            <option value="">Ninguno</option>
            <option value="free">Free</option>
            <option value="vip">VIP</option>
          </select>
        </div>

        {/* Divider */}
        <hr className="my-6 border-gray-300" />

        {/* Choices Section */}
        <div>
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-lg font-bold text-gray-900">
              🔀 Decisiones ({editingFragment.choices?.length || 0})
            </h3>
            <button
              onClick={handleAddChoice}
              className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
            >
              + Agregar
            </button>
          </div>

          <div className="space-y-3">
            {editingFragment.choices?.map((choice, index) => (
              <div key={index} className="border border-gray-300 rounded p-3 bg-gray-50">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-sm font-bold text-gray-700">
                    Decisión {index + 1}
                  </span>
                  <button
                    onClick={() => handleDeleteChoice(index)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    🗑️
                  </button>
                </div>

                {/* Choice Text */}
                <div className="mb-2">
                  <label className="block text-xs text-gray-600 mb-1">Texto:</label>
                  <input
                    type="text"
                    value={choice.text}
                    onChange={(e) => handleUpdateChoice(index, 'text', e.target.value)}
                    className="w-full p-2 border rounded text-sm"
                    placeholder="Texto de la decisión"
                  />
                </div>

                {/* Destination */}
                <div className="mb-2">
                  <label className="block text-xs text-gray-600 mb-1">Destino:</label>
                  <select
                    value={choice.destination_fragment_key}
                    onChange={(e) => handleUpdateChoice(index, 'destination_fragment_key', e.target.value)}
                    className="w-full p-2 border rounded text-sm font-mono"
                  >
                    {narrative?.fragments.map((f) => (
                      <option key={f.key} value={f.key}>
                        {f.key}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Required Besitos */}
                <div className="mb-2">
                  <label className="block text-xs text-gray-600 mb-1">
                    💰 Besitos requeridos:
                  </label>
                  <input
                    type="number"
                    value={choice.required_besitos || 0}
                    onChange={(e) =>
                      handleUpdateChoice(index, 'required_besitos', parseInt(e.target.value))
                    }
                    min={0}
                    className="w-full p-2 border rounded text-sm"
                  />
                </div>

                {/* Required Role */}
                <div>
                  <label className="block text-xs text-gray-600 mb-1">👑 Rol:</label>
                  <select
                    value={choice.required_role || ''}
                    onChange={(e) =>
                      handleUpdateChoice(index, 'required_role', e.target.value || null)
                    }
                    className="w-full p-2 border rounded text-sm"
                  >
                    <option value="">Ninguno</option>
                    <option value="free">Free</option>
                    <option value="vip">VIP</option>
                  </select>
                </div>
              </div>
            ))}
          </div>

          {(!editingFragment.choices || editingFragment.choices.length === 0) && (
            <p className="text-sm text-gray-500 text-center py-4">
              No hay decisiones. Click en "Agregar" para crear una.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
