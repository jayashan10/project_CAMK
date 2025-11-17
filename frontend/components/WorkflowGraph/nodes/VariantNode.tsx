import { Handle, Position, NodeProps } from "reactflow";

export function VariantNode({ data }: NodeProps) {
  const interpretation = data.interpretation || {};

  return (
    <div className="bg-indigo-50 border-2 border-indigo-300 rounded-lg p-3 shadow-md min-w-[200px]">
      <Handle type="target" position={Position.Left} className="!bg-indigo-500" />
      <div>
        <div className="text-xs font-semibold text-indigo-600 uppercase mb-1">
          Genetic Analysis
        </div>
        <div className="text-sm text-gray-900 font-bold mb-2">{data.label}</div>
        {interpretation.reading_frame && (
          <div className="text-xs text-gray-700 mb-1">
            <span className="font-semibold">Frame:</span> {interpretation.reading_frame}
          </div>
        )}
        {interpretation.predicted_phenotype && (
          <div className="text-xs text-gray-700">
            <span className="font-semibold">Phenotype:</span> {interpretation.predicted_phenotype}
          </div>
        )}
      </div>
      <Handle type="source" position={Position.Right} className="!bg-indigo-500" />
    </div>
  );
}
