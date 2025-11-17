import { Handle, Position, NodeProps } from "reactflow";

export function MonarchDiseaseNode({ data }: NodeProps) {
  const diseaseName = data.diseaseName || "";
  const matchCount = data.matchCount || 0;
  const diseaseId = data.diseaseId || "";

  // Color based on match count
  const getColorClass = () => {
    if (matchCount >= 2) return "bg-teal-50 border-teal-400";
    if (matchCount === 1) return "bg-cyan-50 border-cyan-300";
    return "bg-gray-50 border-gray-300";
  };

  const getTextColorClass = () => {
    if (matchCount >= 2) return "text-teal-700";
    if (matchCount === 1) return "text-cyan-700";
    return "text-gray-700";
  };

  return (
    <div className={`${getColorClass()} border-2 rounded-lg p-2.5 shadow-md min-w-[200px] max-w-[240px]`}>
      <Handle type="target" position={Position.Left} className="!bg-teal-500" />
      <div>
        <div className="flex items-center justify-between mb-1">
          <div className={`text-xs font-semibold ${getTextColorClass()} uppercase`}>
            Monarch Match
          </div>
          <div className={`text-xs font-bold ${getTextColorClass()}`}>
            {matchCount} {matchCount === 1 ? "HPO" : "HPOs"}
          </div>
        </div>
        <div className="text-sm text-gray-900 font-medium mb-1 line-clamp-2">
          {diseaseName}
        </div>
        {diseaseId && (
          <div className="text-xs text-gray-500 font-mono truncate">
            {diseaseId}
          </div>
        )}
      </div>
      <Handle type="source" position={Position.Right} className="!bg-teal-500" />
    </div>
  );
}
