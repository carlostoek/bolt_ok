/**
 * Fragment Node Component for React Flow
 */

import { memo } from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import type { FragmentNodeData } from '../../types/narrative';

function FragmentNode({ data, selected }: NodeProps<FragmentNodeData>) {
  const { fragment } = data;

  const bgColor = fragment.character === 'Lucien' ? 'bg-blue-900' : 'bg-pink-600';
  const borderColor = selected ? 'ring-4 ring-yellow-400' : '';

  return (
    <div className={`${bgColor} ${borderColor} rounded-lg shadow-lg p-3 min-w-[200px] max-w-[250px] text-white`}>
      <Handle type="target" position={Position.Top} className="w-3 h-3" />

      <div className="flex items-center gap-2 mb-2">
        <span className="text-lg">{fragment.character === 'Lucien' ? '🎩' : '🌸'}</span>
        <div className="flex-1">
          <div className="font-bold text-sm">{fragment.key}</div>
          <div className="text-xs opacity-80">Nivel {fragment.level || 1}</div>
        </div>
      </div>

      <div className="text-xs mb-2 line-clamp-3 opacity-90">
        {fragment.text.substring(0, 80)}...
      </div>

      <div className="flex gap-2 text-xs">
        {fragment.min_besitos! > 0 && (
          <span className="bg-white/20 px-2 py-1 rounded">
            💰 {fragment.min_besitos}
          </span>
        )}
        {fragment.reward_besitos! > 0 && (
          <span className="bg-green-500/30 px-2 py-1 rounded">
            +{fragment.reward_besitos}
          </span>
        )}
        {fragment.required_role === 'vip' && (
          <span className="bg-yellow-500/30 px-2 py-1 rounded">
            👑 VIP
          </span>
        )}
      </div>

      {fragment.choices && fragment.choices.length > 0 && (
        <div className="mt-2 text-xs opacity-70">
          {fragment.choices.length} decisión(es)
        </div>
      )}

      <Handle type="source" position={Position.Bottom} className="w-3 h-3" />
    </div>
  );
}

export default memo(FragmentNode);
