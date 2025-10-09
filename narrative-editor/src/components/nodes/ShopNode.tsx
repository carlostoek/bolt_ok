/**
 * Shop Node Component for React Flow
 */

import { memo } from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import type { ShopNodeData } from '../../types/narrative';

function ShopNode({ data, selected }: NodeProps<ShopNodeData>) {
  const { item } = data;

  const borderColor = selected ? 'ring-4 ring-yellow-400' : '';

  return (
    <div className={`bg-green-600 ${borderColor} rounded-lg shadow-lg p-3 min-w-[180px] max-w-[220px] text-white`}>
      <Handle type="target" position={Position.Top} className="w-3 h-3" />

      <div className="flex items-center gap-2 mb-2">
        <span className="text-lg">🛒</span>
        <div className="flex-1">
          <div className="font-bold text-sm">{item.name}</div>
          <div className="text-xs opacity-80">{item.price} besitos</div>
        </div>
      </div>

      {item.description && (
        <div className="text-xs mb-2 line-clamp-2 opacity-90">
          {item.description}
        </div>
      )}

      <div className="flex flex-col gap-1 text-xs">
        {item.unlocks_fragment_key && (
          <span className="bg-blue-500/30 px-2 py-1 rounded">
            🔓 → {item.unlocks_fragment_key}
          </span>
        )}
        {item.unlocks_lore_piece_code && (
          <span className="bg-orange-500/30 px-2 py-1 rounded">
            📜 → {item.unlocks_lore_piece_code}
          </span>
        )}
        {item.is_vip_only && (
          <span className="bg-yellow-500/30 px-2 py-1 rounded">
            👑 Solo VIP
          </span>
        )}
      </div>

      <Handle type="source" position={Position.Bottom} className="w-3 h-3" />
    </div>
  );
}

export default memo(ShopNode);
