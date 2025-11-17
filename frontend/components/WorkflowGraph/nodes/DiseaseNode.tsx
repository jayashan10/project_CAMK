import { Handle, Position, NodeProps } from "reactflow";

export function DiseaseNode({ data }: NodeProps) {
  const confidence = data.confidence || 0;

  // Color based on rank and confidence
  const getColorClass = () => {
    if (data.rank === 1) return "bg-green-50 border-green-400";
    if (confidence >= 70) return "bg-green-50 border-green-300";
    if (confidence >= 50) return "bg-yellow-50 border-yellow-300";
    return "bg-orange-50 border-orange-300";
  };

  const getTextColorClass = () => {
    if (data.rank === 1) return "text-green-700";
    if (confidence >= 70) return "text-green-600";
    if (confidence >= 50) return "text-yellow-600";
    return "text-orange-600";
  };

  return (
    <div className={`${getColorClass()} border-2 rounded-lg p-3 shadow-md min-w-[200px]`}>
      <Handle type="target" position={Position.Left} className="!bg-green-500" />
      <div>
        <div className="flex items-center justify-between mb-1">
          <div className={`text-xs font-semibold ${getTextColorClass()} uppercase`}>
            {data.rank === 1 ? "Primary Diagnosis" : `Diagnosis #${data.rank}`}
          </div>
          <div className={`text-xs font-bold ${getTextColorClass()}`}>
            {confidence.toFixed(0)}%
          </div>
        </div>
        <div className="text-sm text-gray-900 font-bold mb-2">{data.label}</div>
        {data.supporting_features && data.supporting_features.length > 0 && (
          <div className="text-xs text-gray-600">
            <div className="font-semibold">Supporting:</div>
            <ul className="list-disc list-inside">
              {data.supporting_features.slice(0, 2).map((feature: string, idx: number) => (
                <li key={idx} className="truncate">{feature}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
      <Handle type="source" position={Position.Right} className="!bg-green-500" />
    </div>
  );
}
