import { Handle, Position, NodeProps } from "reactflow";

export function FilterNode({ data }: NodeProps) {
  const filterType = data.filterType || "included"; // "included" or "excluded"
  const count = data.count || 0;
  const threshold = data.threshold || 30;

  const isIncluded = filterType === "included";

  const bgColor = isIncluded ? "bg-green-50" : "bg-gray-50";
  const borderColor = isIncluded ? "border-green-400" : "border-gray-400";
  const textColor = isIncluded ? "text-green-700" : "text-gray-700";
  const handleColor = isIncluded ? "!bg-green-500" : "!bg-gray-500";
  const icon = isIncluded ? "✅" : "❌";

  return (
    <div className={`${bgColor} border-2 ${borderColor} rounded-lg p-3 shadow-md min-w-[180px]`}>
      <Handle type="target" position={Position.Left} className={handleColor} />
      <div>
        <div className={`text-xs font-semibold ${textColor} uppercase mb-1 flex items-center gap-1`}>
          <span>{icon}</span>
          <span>{isIncluded ? "Included" : "Excluded"}</span>
        </div>
        <div className={`text-base font-bold ${textColor} mb-1`}>
          {count} {count === 1 ? "disease" : "diseases"}
        </div>
        <div className="text-xs text-gray-600">
          Score {isIncluded ? ">" : "≤"} {threshold}
        </div>
      </div>
      <Handle type="source" position={Position.Right} className={handleColor} />
    </div>
  );
}
