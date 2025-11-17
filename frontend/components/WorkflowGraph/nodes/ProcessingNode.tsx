import { Handle, Position, NodeProps } from "reactflow";

export function ProcessingNode({ data }: NodeProps) {
  return (
    <div className="bg-gray-50 border-2 border-gray-300 rounded-lg p-3 shadow-md min-w-[180px]">
      <Handle type="target" position={Position.Left} className="!bg-gray-500" />
      <div className="flex items-center gap-2">
        <div className="text-gray-600 text-lg">⚙️</div>
        <div>
          <div className="text-xs font-semibold text-gray-600 uppercase">Processing</div>
          <div className="text-sm text-gray-800 font-medium">{data.label}</div>
          {data.description && (
            <div className="text-xs text-gray-500 mt-1">{data.description}</div>
          )}
        </div>
      </div>
      <Handle type="source" position={Position.Right} className="!bg-gray-500" />
    </div>
  );
}
