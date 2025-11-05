/**
 * Main Canvas Component with React Flow
 */

import { useCallback, useMemo, useEffect } from 'react';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  BackgroundVariant,
  ConnectionMode,
  useNodesState,
  useEdgesState,
  addEdge,
  type Node,
  type Edge,
  type Connection,
} from 'reactflow';
import 'reactflow/dist/style.css';

import FragmentNode from './nodes/FragmentNode';
import ShopNode from './nodes/ShopNode';
import LoreNode from './nodes/LoreNode';
import { useNarrativeStore } from '../stores/narrativeStore';
import type { FragmentNodeData, ShopNodeData, LoreNodeData } from '../types/narrative';

const nodeTypes = {
  fragment: FragmentNode,
  shop: ShopNode,
  lore: LoreNode,
};

export default function NarrativeCanvas() {
  const narrative = useNarrativeStore((state) => state.narrative);
  const selectedNodeId = useNarrativeStore((state) => state.selectedNodeId);
  const setSelectedNode = useNarrativeStore((state) => state.setSelectedNode);
  const addChoice = useNarrativeStore((state) => state.addChoice);
  const updateFragment = useNarrativeStore((state) => state.updateFragment);

  // Convert narrative data to React Flow nodes
  const initialNodes = useMemo((): Node[] => {
    if (!narrative) return [];

    const nodes: Node[] = [];

    // Fragment nodes
    narrative.fragments.forEach((fragment, index) => {
      nodes.push({
        id: `fragment-${fragment.key}`,
        type: 'fragment',
        position: fragment.visual_position || { x: 250, y: index * 200 },
        data: { fragment } as FragmentNodeData,
      });
    });

    // Shop nodes
    narrative.shop_items?.forEach((item, index) => {
      nodes.push({
        id: `shop-${item.name}`,
        type: 'shop',
        position: { x: 600, y: index * 180 },
        data: { item } as ShopNodeData,
      });
    });

    // Lore nodes
    narrative.lore_pieces?.forEach((lore, index) => {
      nodes.push({
        id: `lore-${lore.code_name}`,
        type: 'lore',
        position: { x: 900, y: index * 160 },
        data: { lore } as LoreNodeData,
      });
    });

    return nodes;
  }, [narrative]);

  // Convert choices to React Flow edges
  const initialEdges = useMemo((): Edge[] => {
    if (!narrative) return [];

    const edges: Edge[] = [];

    // Fragment to fragment edges (choices)
    narrative.fragments.forEach((fragment) => {
      fragment.choices?.forEach((choice, index) => {
        edges.push({
          id: `edge-${fragment.key}-${choice.destination_fragment_key}-${index}`,
          source: `fragment-${fragment.key}`,
          target: `fragment-${choice.destination_fragment_key}`,
          label: choice.text.substring(0, 30) + (choice.text.length > 30 ? '...' : ''),
          type: 'smoothstep',
          animated: false,
          style: { stroke: '#64748b', strokeWidth: 2 },
        });
      });
    });

    // Shop to fragment edges
    narrative.shop_items?.forEach((item) => {
      if (item.unlocks_fragment_key) {
        edges.push({
          id: `edge-shop-${item.name}-${item.unlocks_fragment_key}`,
          source: `shop-${item.name}`,
          target: `fragment-${item.unlocks_fragment_key}`,
          label: '🔓 Desbloquea',
          type: 'smoothstep',
          animated: true,
          style: { stroke: '#10b981', strokeWidth: 2, strokeDasharray: '5,5' },
        });
      }
    });

    return edges;
  }, [narrative]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Update nodes and edges when narrative changes
  useEffect(() => {
    setNodes(initialNodes);
  }, [initialNodes, setNodes]);

  useEffect(() => {
    setEdges(initialEdges);
  }, [initialEdges, setEdges]);

  const onConnect = useCallback(
    (connection: Connection) => {
      // Handle new connection (create choice)
      if (connection.source && connection.target) {
        const sourceKey = connection.source.replace('fragment-', '');
        const targetKey = connection.target.replace('fragment-', '');

        if (connection.source.startsWith('fragment-') && connection.target.startsWith('fragment-')) {
          // Create a new choice
          addChoice(sourceKey, {
            text: 'Nueva decisión',
            destination_fragment_key: targetKey,
            required_besitos: 0,
          });
        }
      }

      setEdges((eds) => addEdge(connection, eds));
    },
    [addChoice, setEdges]
  );

  const onNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      setSelectedNode(node.id);
    },
    [setSelectedNode]
  );

  const onNodeDragStop = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      // Update fragment position when node is dragged
      if (node.id.startsWith('fragment-')) {
        const key = node.id.replace('fragment-', '');
        updateFragment(key, {
          visual_position: { x: node.position.x, y: node.position.y },
        });
      }
    },
    [updateFragment]
  );

  if (!narrative) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-100">
        <div className="text-center p-8">
          <h2 className="text-2xl font-bold text-gray-700 mb-2">
            No hay narrativa cargada
          </h2>
          <p className="text-gray-600">
            Abre un archivo JSON para comenzar a editar
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onNodeDragStop={onNodeDragStop}
        nodeTypes={nodeTypes}
        connectionMode={ConnectionMode.Loose}
        fitView
      >
        <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
        <Controls />
        <MiniMap
          nodeColor={(node) => {
            if (node.id === selectedNodeId) return '#fbbf24';
            if (node.type === 'fragment') return node.data.fragment.character === 'Lucien' ? '#1e3a8a' : '#ec4899';
            if (node.type === 'shop') return '#10b981';
            if (node.type === 'lore') return '#f59e0b';
            return '#64748b';
          }}
          maskColor="rgba(0, 0, 0, 0.1)"
        />
      </ReactFlow>
    </div>
  );
}
