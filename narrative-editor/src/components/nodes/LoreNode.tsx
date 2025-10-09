/**
 * Lore Piece Node Component for React Flow
 */

import { memo } from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import type { LoreNodeData } from '../../types/narrative';

function LoreNode({ data, selected }: NodeProps<LoreNodeData>) {
  const { lore } = data;

  const borderColor = selected ? 'ring-4 ring-yellow-400' : '';

  return (
    <div className={`bg-orange-500 ${borderColor} rounded-lg shadow-lg p-3 min-w-[180px] max-w-[220px] text-white`}>
      <Handle type="target" position={Position.Top} className="w-3 h-3" />

      <div className="flex items-center gap-2 mb-2">
        <span className="text-lg">📜</span>
        <div className="flex-1">
          <div className="font-bold text-sm">{lore.title}</div>
          <div className="text-xs opacity-80 font-mono">{lore.code_name}</div>
        </div>
      </div>

      {lore.description && (
        <div className="text-xs mb-2 line-clamp-2 opacity-90">
          {lore.description}
        </div>
      )}

      <div className="flex gap-1 text-xs flex-wrap">
        {lore.category && (
          <span className="bg-white/20 px-2 py-1 rounded">
            {lore.category}
          </span>
        )}
        {lore.is_main_story && (
          <span className="bg-purple-500/30 px-2 py-1 rounded">
            ⭐ Historia Principal
          </span>
        )}
        {lore.content_type && lore.content_type !== 'text' && (
          <span className="bg-blue-500/30 px-2 py-1 rounded">
            {lore.content_type === 'image' ? '🖼️' : '🎥'} {lore.content_type}
          </span>
        )}
      </div>

      <Handle type="source" position={Position.Bottom} className="w-3 h-3" />
    </div>
  );
}

export default memo(LoreNode);
