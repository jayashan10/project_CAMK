import { Handle, Position, NodeProps } from "reactflow";

export function HPOMappingDetailNode({ data }: NodeProps) {
  const symptom = data.symptom || "";
  const hpoId = data.hpoId || "";
  const hpoTerm = data.hpoTerm || "";

  return (
    <div className="bg-purple-50 border-2 border-purple-300 rounded-lg p-2.5 shadow-md min-w-[180px]">
      <Handle type="target" position={Position.Left} className="!bg-purple-500" />
      <div>
        <div className="text-xs font-semibold text-purple-700 uppercase mb-1">
          HPO Mapping
        </div>
        <div className="text-xs text-gray-800 mb-1">
          <span className="font-medium">"{symptom}"</span>
        </div>
        <div className="text-xs text-purple-600 flex items-center gap-1">
          <span>→</span>
          <span className="font-mono font-semibold">{hpoId}</span>
        </div>
        {hpoTerm && hpoTerm !== symptom && (
          <div className="text-xs text-gray-600 mt-1 italic">
            {hpoTerm}
          </div>
        )}
      </div>
      <Handle type="source" position={Position.Right} className="!bg-purple-500" />
    </div>
  );
}
