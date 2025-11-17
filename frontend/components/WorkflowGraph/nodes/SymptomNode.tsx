import { Handle, Position, NodeProps } from "reactflow";

export function SymptomNode({ data }: NodeProps) {
  return (
    <div className="bg-blue-50 border-2 border-blue-300 rounded-lg p-3 shadow-md min-w-[180px]">
      <div className="flex items-center gap-2">
        <div className="text-blue-600 text-lg">🔍</div>
        <div>
          <div className="text-xs font-semibold text-blue-600 uppercase">Symptom</div>
          <div className="text-sm text-gray-800 font-medium">{data.label}</div>
        </div>
      </div>
      <Handle type="source" position={Position.Right} className="!bg-blue-500" />
    </div>
  );
}
