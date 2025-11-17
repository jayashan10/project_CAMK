import { Handle, Position, NodeProps } from "reactflow";

export function TreatmentNode({ data }: NodeProps) {
  const urgencyColor = {
    immediate: "bg-red-50 border-red-400 text-red-700",
    urgent: "bg-yellow-50 border-yellow-400 text-yellow-700",
    routine: "bg-teal-50 border-teal-300 text-teal-600",
  };

  const colorClass = urgencyColor[data.urgency as keyof typeof urgencyColor] || urgencyColor.routine;

  return (
    <div className={`${colorClass} border-2 rounded-lg p-3 shadow-md min-w-[200px]`}>
      <Handle type="target" position={Position.Left} className="!bg-teal-500" />
      <div>
        <div className="flex items-center justify-between mb-1">
          <div className="text-xs font-semibold uppercase">
            Treatment
          </div>
          {data.evidence_level && (
            <span className="text-xs font-bold px-2 py-0.5 bg-white rounded">
              {data.evidence_level}
            </span>
          )}
        </div>
        <div className="text-sm text-gray-900 font-medium mb-1">{data.label}</div>
        {data.urgency && (
          <div className="text-xs font-semibold uppercase">
            {data.urgency}
          </div>
        )}
      </div>
    </div>
  );
}
