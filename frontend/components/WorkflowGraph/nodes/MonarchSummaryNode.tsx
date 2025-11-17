import { Handle, Position, NodeProps } from "reactflow";

export function MonarchSummaryNode({ data }: NodeProps) {
  const total = data.total || 0;
  const breakdown = data.breakdown || {};

  return (
    <div className="bg-blue-50 border-2 border-blue-400 rounded-lg p-3 shadow-md min-w-[240px]">
      <Handle type="target" position={Position.Left} className="!bg-blue-500" />
      <div>
        <div className="text-xs font-semibold text-blue-700 uppercase mb-1">
          Monarch Knowledge Graph
        </div>
        <div className="text-lg font-bold text-blue-900 mb-2">
          {total} diseases found
        </div>

        {Object.keys(breakdown).length > 0 && (
          <div className="text-xs text-gray-700 space-y-1">
            <div className="font-semibold">Match distribution:</div>
            {Object.entries(breakdown)
              .sort(([a], [b]) => parseInt(b) - parseInt(a))
              .slice(0, 3)
              .map(([matchCount, diseaseCount]) => (
                <div key={matchCount} className="flex justify-between">
                  <span>{matchCount} HPO {matchCount === "1" ? "match" : "matches"}:</span>
                  <span className="font-semibold">{diseaseCount} diseases</span>
                </div>
              ))}
          </div>
        )}
      </div>
      <Handle type="source" position={Position.Right} className="!bg-blue-500" />
    </div>
  );
}
