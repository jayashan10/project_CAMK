/**
 * Enhanced Workflow graph builder - converts ScenarioResponse to React Flow graph
 * Now includes detailed reasoning flow with Monarch results, scoring, and filtering
 */
import dagre from "dagre";
import type { Node, Edge } from "reactflow";
import type { ScenarioResponse, MonarchMatch, ScoringBreakdown } from "@/types/clinical";

const NODE_WIDTH = 200;
const NODE_HEIGHT = 80;

interface GraphNode extends Node {
  data: {
    label: string;
    [key: string]: any;
  };
}

interface GraphEdge extends Edge {
  label?: string;
  animated?: boolean;
}

/**
 * Use dagre for automatic graph layout
 */
function getLayoutedElements(
  nodes: GraphNode[],
  edges: GraphEdge[],
  direction = "LR" // Left to right
) {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({ rankdir: direction, ranksep: 180, nodesep: 100 });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - NODE_WIDTH / 2,
        y: nodeWithPosition.y - NODE_HEIGHT / 2,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
}

/**
 * Build enhanced workflow graph from scenario response
 */
export function buildWorkflowGraph(
  response: ScenarioResponse,
  scenario?: any
): { nodes: Node[]; edges: Edge[] } {
  const nodes: GraphNode[] = [];
  const edges: GraphEdge[] = [];
  let nodeId = 0;

  // Extract symptoms from scenario
  const symptoms = scenario?.presenting_symptoms || [];
  const hpoMappings = response.hpo_mappings || [];
  const monarchSummary = response.monarch_search_summary;
  const topMonarch = response.top_monarch_matches || [];
  const scoringDetails = response.scoring_details || [];

  // ═══════════════════════════════════════════════════════════════
  // Layer 1: Symptom nodes
  // ═══════════════════════════════════════════════════════════════
  const symptomNodeIds: string[] = [];
  symptoms.forEach((symptom: string) => {
    const id = `symptom-${nodeId++}`;
    symptomNodeIds.push(id);
    nodes.push({
      id,
      type: "symptomNode",
      position: { x: 0, y: 0 },
      data: {
        label: symptom,
        category: "symptom",
      },
    });
  });

  // ═══════════════════════════════════════════════════════════════
  // Layer 2: HPO Mapping Detail Nodes (if available)
  // ═══════════════════════════════════════════════════════════════
  const hpoDetailNodeIds: string[] = [];
  if (hpoMappings.length > 0) {
    hpoMappings.forEach((mapping) => {
      const id = `hpo-detail-${nodeId++}`;
      hpoDetailNodeIds.push(id);
      nodes.push({
        id,
        type: "hpoMappingDetailNode",
        position: { x: 0, y: 0 },
        data: {
          symptom: mapping.clinical_feature,
          hpoId: mapping.hpo_id,
          hpoTerm: mapping.hpo_term,
          category: "hpo_mapping",
        },
      });

      // Connect symptoms to HPO mappings
      symptomNodeIds.forEach((symptomId) => {
        edges.push({
          id: `e-${symptomId}-${id}`,
          source: symptomId,
          target: id,
          type: "smoothstep",
        });
      });
    });
  } else {
    // Fallback: Single HPO node if no detailed mappings
    const hpoNodeId = `hpo-${nodeId++}`;
    hpoDetailNodeIds.push(hpoNodeId);
    nodes.push({
      id: hpoNodeId,
      type: "hpoNode",
      position: { x: 0, y: 0 },
      data: {
        label: "HPO Term Mapping",
        description: "Clinical features mapped to standardized phenotype ontology",
        category: "processing",
      },
    });

    symptomNodeIds.forEach((symptomId) => {
      edges.push({
        id: `e-${symptomId}-${hpoNodeId}`,
        source: symptomId,
        target: hpoNodeId,
        label: "maps to",
        animated: true,
        type: "smoothstep",
      });
    });
  }

  // ═══════════════════════════════════════════════════════════════
  // Layer 3: Knowledge Graph Query Node
  // ═══════════════════════════════════════════════════════════════
  const kgQueryNodeId = `kg-query-${nodeId++}`;
  nodes.push({
    id: kgQueryNodeId,
    type: "processingNode",
    position: { x: 0, y: 0 },
    data: {
      label: "Monarch Knowledge Graph Query",
      description: "Search for diseases matching phenotypes",
      category: "processing",
    },
  });

  hpoDetailNodeIds.forEach((hpoId) => {
    edges.push({
      id: `e-${hpoId}-${kgQueryNodeId}`,
      source: hpoId,
      target: kgQueryNodeId,
      label: "query",
      animated: true,
      type: "smoothstep",
    });
  });

  // ═══════════════════════════════════════════════════════════════
  // Layer 4: Monarch Search Summary Node
  // ═══════════════════════════════════════════════════════════════
  const monarchSummaryNodeId = `monarch-summary-${nodeId++}`;
  if (monarchSummary) {
    nodes.push({
      id: monarchSummaryNodeId,
      type: "monarchSummaryNode",
      position: { x: 0, y: 0 },
      data: {
        total: monarchSummary.total_diseases_found,
        breakdown: monarchSummary.diseases_by_match_count,
        category: "monarch",
      },
    });

    edges.push({
      id: `e-${kgQueryNodeId}-${monarchSummaryNodeId}`,
      source: kgQueryNodeId,
      target: monarchSummaryNodeId,
      label: `${monarchSummary.total_diseases_found} diseases`,
      animated: true,
      type: "smoothstep",
    });
  }

  // ═══════════════════════════════════════════════════════════════
  // Layer 5: Top Monarch Disease Matches (top 20)
  // ═══════════════════════════════════════════════════════════════
  const monarchDiseaseNodeIds: string[] = [];
  if (topMonarch.length > 0) {
    // Show top 20 diseases from Monarch
    topMonarch.slice(0, 20).forEach((match: MonarchMatch) => {
      const id = `monarch-disease-${nodeId++}`;
      monarchDiseaseNodeIds.push(id);

      nodes.push({
        id,
        type: "monarchDiseaseNode",
        position: { x: 0, y: 0 },
        data: {
          diseaseName: match.disease_name,
          diseaseId: match.disease_id,
          matchCount: match.match_count,
          code: match.code,
          category: "monarch_disease",
        },
      });

      edges.push({
        id: `e-${monarchSummaryNodeId}-${id}`,
        source: monarchSummaryNodeId,
        target: id,
        label: `${match.match_count} HPO`,
        type: "smoothstep",
      });
    });
  }

  // ═══════════════════════════════════════════════════════════════
  // Layer 6: Scoring Components (show key factors)
  // ═══════════════════════════════════════════════════════════════
  const scoringNodeIds: string[] = [];
  if (scoringDetails.length > 0) {
    // Get the top scored disease to show its scoring components
    const topScoredDisease = scoringDetails[0];

    topScoredDisease.scoring_components.forEach((component) => {
      const id = `scoring-${nodeId++}`;
      scoringNodeIds.push(id);

      nodes.push({
        id,
        type: "scoringNode",
        position: { x: 0, y: 0 },
        data: {
          componentName: component.component_name,
          points: component.points_added,
          reasoning: component.reasoning,
          category: "scoring",
        },
      });

      // Connect Monarch diseases to scoring nodes
      monarchDiseaseNodeIds.forEach((mdId) => {
        edges.push({
          id: `e-${mdId}-${id}`,
          source: mdId,
          target: id,
          type: "smoothstep",
        });
      });
    });
  }

  // ═══════════════════════════════════════════════════════════════
  // Layer 7: Filter Split (Included vs Excluded)
  // ═══════════════════════════════════════════════════════════════
  const includedCount = scoringDetails.filter(d => d.included_in_differential).length;
  const excludedCount = scoringDetails.filter(d => !d.included_in_differential).length;

  const includedNodeId = `filter-included-${nodeId++}`;
  const excludedNodeId = `filter-excluded-${nodeId++}`;

  nodes.push({
    id: includedNodeId,
    type: "filterNode",
    position: { x: 0, y: 0 },
    data: {
      filterType: "included",
      count: includedCount,
      threshold: 30,
      category: "filter",
    },
  });

  nodes.push({
    id: excludedNodeId,
    type: "filterNode",
    position: { x: 0, y: 0 },
    data: {
      filterType: "excluded",
      count: excludedCount,
      threshold: 30,
      category: "filter",
    },
  });

  // Connect scoring to filters
  scoringNodeIds.forEach((scoringId) => {
    edges.push({
      id: `e-${scoringId}-${includedNodeId}`,
      source: scoringId,
      target: includedNodeId,
      type: "smoothstep",
    });
    edges.push({
      id: `e-${scoringId}-${excludedNodeId}`,
      source: scoringId,
      target: excludedNodeId,
      type: "smoothstep",
    });
  });

  // ═══════════════════════════════════════════════════════════════
  // Layer 8: Final Differential Diagnosis (Top 5)
  // ═══════════════════════════════════════════════════════════════
  const diseaseNodeIds: { id: string; rank: number }[] = [];
  response.differential_diagnoses.forEach((dx, index) => {
    const id = `disease-${nodeId++}`;
    diseaseNodeIds.push({ id, rank: index + 1 });

    nodes.push({
      id,
      type: "diseaseNode",
      position: { x: 0, y: 0 },
      data: {
        label: dx.disease_name,
        confidence: dx.confidence_score,
        supporting_features: dx.supporting_features,
        recommended_tests: dx.recommended_tests,
        category: "disease",
        rank: index + 1,
      },
    });

    edges.push({
      id: `e-${includedNodeId}-${id}`,
      source: includedNodeId,
      target: id,
      label: `${dx.confidence_score.toFixed(0)}%`,
      type: "smoothstep",
    });
  });

  // ═══════════════════════════════════════════════════════════════
  // Layer 9: Variant Analysis & Treatments (existing logic)
  // ═══════════════════════════════════════════════════════════════
  let variantNodeId: string | null = null;
  if (response.variant_interpretation) {
    variantNodeId = `variant-${nodeId++}`;

    const variantData = response.variant_interpretation;
    const variantLabel = variantData.gene
      ? `${variantData.gene} Variant Analysis`
      : "Variant Interpretation";

    nodes.push({
      id: variantNodeId,
      type: "variantNode",
      position: { x: 0, y: 0 },
      data: {
        label: variantLabel,
        interpretation: variantData,
        category: "variant",
      },
    });

    diseaseNodeIds.slice(0, 2).forEach(({ id }) => {
      edges.push({
        id: `e-${id}-${variantNodeId}`,
        source: id,
        target: variantNodeId!,
        label: "inform",
        animated: true,
        type: "smoothstep",
      });
    });
  }

  // Treatment nodes
  const treatmentRecs = response.recommendations.filter(
    (rec) => rec.category === "treatment"
  );

  const sourceForTreatments = variantNodeId ||
    (diseaseNodeIds.length > 0 ? diseaseNodeIds[0].id : includedNodeId);

  treatmentRecs.forEach((rec) => {
    const id = `treatment-${nodeId++}`;

    const shortLabel =
      rec.recommendation.length > 50
        ? rec.recommendation.substring(0, 47) + "..."
        : rec.recommendation;

    nodes.push({
      id,
      type: "treatmentNode",
      position: { x: 0, y: 0 },
      data: {
        label: shortLabel,
        full_text: rec.recommendation,
        evidence_level: rec.evidence_level,
        urgency: rec.urgency,
        category: "treatment",
      },
    });

    edges.push({
      id: `e-${sourceForTreatments}-${id}`,
      source: sourceForTreatments,
      target: id,
      label: rec.urgency || "routine",
      type: "smoothstep",
    });
  });

  // Apply dagre layout
  return getLayoutedElements(nodes, edges);
}
