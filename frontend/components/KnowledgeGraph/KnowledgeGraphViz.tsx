"use client";

import React, { useEffect, useRef, useState, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import GraphControls from './GraphControls';
import NodeDetailPanel from './NodeDetailPanel';

interface GraphNode {
  id: string;
  label: string;
  type: string;
  group: string;
  [key: string]: any;
}

interface GraphLink {
  source: string;
  target: string;
  relationship: string;
  label: string;
}

interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
  metadata?: {
    disease_code: string;
    disease_name: string;
    node_count: number;
    link_count: number;
  };
}

interface KnowledgeGraphVizProps {
  diseaseCode: string;
  apiBaseUrl?: string;
}

const KnowledgeGraphViz: React.FC<KnowledgeGraphVizProps> = ({
  diseaseCode,
  apiBaseUrl = 'http://localhost:8000/api'
}) => {
  const graphRef = useRef<any>();
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [highlightNodes, setHighlightNodes] = useState<Set<string>>(new Set());
  const [highlightLinks, setHighlightLinks] = useState<Set<string>>(new Set());
  const [zoomLevel, setZoomLevel] = useState<number>(1);

  // Node color mapping by type
  const nodeColors: Record<string, string> = {
    disease: '#ef4444',    // red
    gene: '#3b82f6',       // blue
    phenotype: '#10b981',  // green
    variant: '#f59e0b',    // amber
    treatment: '#8b5cf6',  // purple
  };

  // Fetch graph data from backend
  useEffect(() => {
    const fetchGraphData = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `${apiBaseUrl}/knowledge-graph/${diseaseCode.toUpperCase()}?max_phenotypes=20`
        );

        if (!response.ok) {
          throw new Error(`Failed to fetch graph data: ${response.statusText}`);
        }

        const data = await response.json();
        setGraphData(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load knowledge graph');
        console.error('Error fetching graph data:', err);
      } finally {
        setLoading(false);
      }
    };

    if (diseaseCode) {
      fetchGraphData();
    }
  }, [diseaseCode, apiBaseUrl]);

  // Handle node click
  const handleNodeClick = useCallback((node: GraphNode) => {
    setSelectedNode(node);

    // Highlight connected nodes and links
    if (graphData) {
      const connectedNodeIds = new Set<string>();
      const connectedLinkIds = new Set<string>();

      graphData.links.forEach((link: any) => {
        if (link.source.id === node.id || link.source === node.id) {
          connectedNodeIds.add(typeof link.target === 'object' ? link.target.id : link.target);
          connectedLinkIds.add(`${link.source}-${link.target}`);
        }
        if (link.target.id === node.id || link.target === node.id) {
          connectedNodeIds.add(typeof link.source === 'object' ? link.source.id : link.source);
          connectedLinkIds.add(`${link.source}-${link.target}`);
        }
      });

      connectedNodeIds.add(node.id);
      setHighlightNodes(connectedNodeIds);
      setHighlightLinks(connectedLinkIds);
    }
  }, [graphData]);

  // Handle background click (deselect node)
  const handleBackgroundClick = useCallback(() => {
    setSelectedNode(null);
    setHighlightNodes(new Set());
    setHighlightLinks(new Set());
  }, []);

  // Node canvas rendering
  const paintNode = useCallback((node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const label = node.label || node.id;
    const fontSize = 12 / globalScale;
    const isHighlighted = highlightNodes.size === 0 || highlightNodes.has(node.id);

    // Draw node circle
    ctx.beginPath();
    ctx.arc(node.x, node.y, 5, 0, 2 * Math.PI);
    ctx.fillStyle = nodeColors[node.group] || '#94a3b8';
    ctx.globalAlpha = isHighlighted ? 1 : 0.3;
    ctx.fill();

    // Draw label
    ctx.font = `${fontSize}px Sans-Serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = isHighlighted ? '#000' : '#666';
    ctx.fillText(label, node.x, node.y + 8);
    ctx.globalAlpha = 1;
  }, [highlightNodes, nodeColors]);

  // Link rendering
  const paintLink = useCallback((link: any, ctx: CanvasRenderingContext2D) => {
    const linkId = `${link.source.id || link.source}-${link.target.id || link.target}`;
    const isHighlighted = highlightLinks.size === 0 || highlightLinks.has(linkId);

    ctx.strokeStyle = isHighlighted ? '#94a3b8' : '#e2e8f0';
    ctx.lineWidth = isHighlighted ? 2 : 1;
    ctx.globalAlpha = isHighlighted ? 1 : 0.3;

    ctx.beginPath();
    ctx.moveTo(link.source.x, link.source.y);
    ctx.lineTo(link.target.x, link.target.y);
    ctx.stroke();
    ctx.globalAlpha = 1;
  }, [highlightLinks]);

  // Center graph on load
  useEffect(() => {
    if (graphRef.current && graphData) {
      setTimeout(() => {
        graphRef.current?.zoomToFit(400);
      }, 100);
    }
  }, [graphData]);

  // Handle zoom controls
  const handleZoom = useCallback((delta: number) => {
    if (graphRef.current) {
      const currentZoom = graphRef.current.zoom();
      graphRef.current.zoom(currentZoom + delta, 400);
      setZoomLevel(currentZoom + delta);
    }
  }, []);

  const handleReset = useCallback(() => {
    if (graphRef.current) {
      graphRef.current.zoomToFit(400);
      setSelectedNode(null);
      setHighlightNodes(new Set());
      setHighlightLinks(new Set());
    }
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[600px] bg-gray-50 rounded-lg">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading knowledge graph...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-[600px] bg-red-50 rounded-lg">
        <div className="text-center text-red-600">
          <svg className="mx-auto h-12 w-12 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <p className="font-medium mb-2">Failed to load knowledge graph</p>
          <p className="text-sm">{error}</p>
        </div>
      </div>
    );
  }

  if (!graphData || graphData.nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-[600px] bg-gray-50 rounded-lg">
        <p className="text-gray-600">No graph data available for {diseaseCode}</p>
      </div>
    );
  }

  return (
    <div className="relative border border-gray-200 rounded-lg overflow-hidden">
      {/* Graph Title */}
      <div className="bg-white border-b border-gray-200 px-4 py-3">
        <h3 className="text-lg font-semibold text-gray-900">
          {graphData.metadata?.disease_name || diseaseCode} Knowledge Graph
        </h3>
        <p className="text-sm text-gray-600 mt-1">
          {graphData.metadata?.node_count} nodes, {graphData.metadata?.link_count} connections
        </p>
      </div>

      {/* Graph Canvas */}
      <div className="relative bg-white" style={{ height: '600px' }}>
        <ForceGraph2D
          ref={graphRef}
          graphData={graphData}
          nodeLabel="label"
          nodeCanvasObject={paintNode}
          linkCanvasObject={paintLink}
          onNodeClick={handleNodeClick}
          onBackgroundClick={handleBackgroundClick}
          linkDirectionalArrowLength={0}
          linkDirectionalArrowRelPos={1}
          d3AlphaDecay={0.02}
          d3VelocityDecay={0.3}
          cooldownTime={3000}
          width={undefined}
          height={600}
        />

        {/* Graph Controls */}
        <GraphControls
          onZoomIn={() => handleZoom(0.3)}
          onZoomOut={() => handleZoom(-0.3)}
          onReset={handleReset}
        />

        {/* Legend */}
        <div className="absolute bottom-4 left-4 bg-white/90 backdrop-blur-sm rounded-lg shadow-lg p-3 text-xs">
          <div className="font-semibold mb-2">Node Types</div>
          {Object.entries(nodeColors).map(([type, color]) => (
            <div key={type} className="flex items-center gap-2 mb-1">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }}></div>
              <span className="capitalize">{type}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Node Detail Panel */}
      {selectedNode && (
        <NodeDetailPanel
          node={selectedNode}
          onClose={() => setSelectedNode(null)}
        />
      )}
    </div>
  );
};

export default KnowledgeGraphViz;
