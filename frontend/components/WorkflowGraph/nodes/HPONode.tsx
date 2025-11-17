import { Handle, Position, NodeProps } from "reactflow";

export function HPONode({ data }: NodeProps) {
  return (
    <div className="bg-purple-50 border-2 border-purple-300 rounded-lg p-3 shadow-md min-w-[180px]">
      <Handle type="target" position={Position.Left} className="!bg-purple-500" />
      <div className="flex items-center gap-2">
        <div className="text-purple-600 text-lg">🔬</div>
        <div>
          <div className="text-xs font-semibold text-purple-600 uppercase">HPO Mapping</div>
          <div className="text-sm text-gray-800 font-medium">{data.label}</div>
          {data.description && (
            <div className="text-xs text-gray-500 mt-1">{data.description}</div>
          )}
        </div>
      </div>
      <Handle type="source" position={Position.Right} className="!bg-purple-500" />
    </div>
  );
}
