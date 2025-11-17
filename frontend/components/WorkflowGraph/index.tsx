"use client";

import { useCallback, useMemo } from "react";
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
} from "reactflow";
import "reactflow/dist/style.css";

import { SymptomNode } from "./nodes/SymptomNode";
import { HPONode } from "./nodes/HPONode";
import { ProcessingNode } from "./nodes/ProcessingNode";
import { DiseaseNode } from "./nodes/DiseaseNode";
import { VariantNode } from "./nodes/VariantNode";
import { TreatmentNode } from "./nodes/TreatmentNode";
import { HPOMappingDetailNode } from "./nodes/HPOMappingDetailNode";
import { MonarchSummaryNode } from "./nodes/MonarchSummaryNode";
import { MonarchDiseaseNode } from "./nodes/MonarchDiseaseNode";
import { ScoringNode } from "./nodes/ScoringNode";
import { FilterNode } from "./nodes/FilterNode";

interface WorkflowGraphProps {
  nodes: Node[];
  edges: Edge[];
}

const nodeTypes = {
  symptomNode: SymptomNode,
  hpoNode: HPONode,
  hpoMappingDetailNode: HPOMappingDetailNode,
  processingNode: ProcessingNode,
  monarchSummaryNode: MonarchSummaryNode,
  monarchDiseaseNode: MonarchDiseaseNode,
  scoringNode: ScoringNode,
  filterNode: FilterNode,
  diseaseNode: DiseaseNode,
  variantNode: VariantNode,
  treatmentNode: TreatmentNode,
};

export function WorkflowGraph({ nodes: initialNodes, edges: initialEdges }: WorkflowGraphProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Update nodes and edges when props change
  useMemo(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  const minimapNodeColor = useCallback((node: Node) => {
    switch (node.type) {
      case "symptomNode":
        return "#93C5FD"; // blue
      case "hpoNode":
      case "hpoMappingDetailNode":
        return "#C4B5FD"; // purple
      case "processingNode":
        return "#D1D5DB"; // gray
      case "monarchSummaryNode":
        return "#60A5FA"; // blue
      case "monarchDiseaseNode":
        return "#5EEAD4"; // teal
      case "scoringNode":
        return "#A5B4FC"; // indigo
      case "filterNode":
        return "#9CA3AF"; // gray
      case "diseaseNode":
        return "#86EFAC"; // green
      case "variantNode":
        return "#A5B4FC"; // indigo
      case "treatmentNode":
        return "#5EEAD4"; // teal
      default:
        return "#E5E7EB";
    }
  }, []);

  return (
    <div className="w-full h-[600px] bg-white rounded-lg border-2 border-gray-200">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-left"
      >
        <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
        <Controls />
        <MiniMap nodeColor={minimapNodeColor} zoomable pannable />

        {/* Legend */}
        <div className="absolute top-4 left-4 bg-white p-3 rounded-lg shadow-lg border border-gray-200 text-xs max-h-[500px] overflow-y-auto">
          <div className="font-bold text-gray-700 mb-2">Workflow Legend</div>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-blue-300 rounded"></div>
              <span>Symptoms</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-purple-300 rounded"></div>
              <span>HPO Mapping</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-gray-300 rounded"></div>
              <span>KG Query</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-blue-400 rounded"></div>
              <span>Monarch Summary</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-teal-300 rounded"></div>
              <span>Monarch Diseases</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-indigo-300 rounded"></div>
              <span>Scoring Factors</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-gray-400 rounded"></div>
              <span>Filter (Include/Exclude)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-300 rounded"></div>
              <span>Final Diagnosis</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-teal-400 rounded"></div>
              <span>Treatment</span>
            </div>
          </div>
        </div>
      </ReactFlow>
    </div>
  );
}
