import { Handle, Position, NodeProps } from "reactflow";

export function ScoringNode({ data }: NodeProps) {
  const componentName = data.componentName || "";
  const points = data.points || 0;
  const reasoning = data.reasoning || "";

  return (
    <div className="bg-indigo-50 border-2 border-indigo-300 rounded-lg p-2.5 shadow-md min-w-[200px]">
      <Handle type="target" position={Position.Left} className="!bg-indigo-500" />
      <div>
        <div className="text-xs font-semibold text-indigo-700 uppercase mb-1">
          {componentName}
        </div>
        <div className="flex items-baseline gap-2 mb-1">
          <span className="text-lg font-bold text-indigo-900">+{points}</span>
          <span className="text-xs text-gray-600">points</span>
        </div>
        {reasoning && (
          <div className="text-xs text-gray-700 italic">
            {reasoning}
          </div>
        )}
      </div>
      <Handle type="source" position={Position.Right} className="!bg-indigo-500" />
    </div>
  );
}
