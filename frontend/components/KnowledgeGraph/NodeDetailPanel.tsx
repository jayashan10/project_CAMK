"use client";

import React from 'react';

interface GraphNode {
  id: string;
  label: string;
  type: string;
  group: string;
  [key: string]: any;
}

interface NodeDetailPanelProps {
  node: GraphNode;
  onClose: () => void;
}

const NodeDetailPanel: React.FC<NodeDetailPanelProps> = ({ node, onClose }) => {
  // Render different content based on node type
  const renderNodeDetails = () => {
    switch (node.type) {
      case 'Disease':
        return (
          <>
            <DetailRow label="Code" value={node.code} />
            <DetailRow label="Inheritance" value={node.inheritance} />
            {node.onset && (
              <DetailRow
                label="Typical Onset"
                value={`${node.onset[0]}-${node.onset[1]} years`}
              />
            )}
          </>
        );

      case 'Gene':
        return (
          <>
            <DetailRow label="Gene ID" value={node.gene_id} />
          </>
        );

      case 'Phenotype':
        return (
          <>
            <DetailRow label="HPO ID" value={node.hpo_id} />
            {node.specificity !== null && node.specificity !== undefined && (
              <DetailRow
                label="Specificity"
                value={`${(node.specificity * 100).toFixed(0)}%`}
              />
            )}
          </>
        );

      case 'Variant':
        return (
          <>
            {node.exons && node.exons.length > 0 && (
              <DetailRow label="Exons" value={node.exons.join(', ')} />
            )}
            {node.reading_frame && (
              <DetailRow label="Reading Frame" value={node.reading_frame} />
            )}
            {node.severity && (
              <DetailRow label="Severity" value={node.severity} />
            )}
          </>
        );

      case 'Treatment':
        return (
          <>
            {node.recommendation && (
              <div className="mb-3">
                <div className="text-xs font-semibold text-gray-500 uppercase mb-1">
                  Recommendation
                </div>
                <div className="text-sm text-gray-900">{node.recommendation}</div>
              </div>
            )}
            {node.evidence_level && (
              <DetailRow label="Evidence Level" value={node.evidence_level} />
            )}
            {node.urgency && (
              <DetailRow label="Urgency" value={node.urgency} />
            )}
          </>
        );

      default:
        return <p className="text-sm text-gray-600">No additional details available.</p>;
    }
  };

  return (
    <div className="absolute top-4 left-4 bg-white rounded-lg shadow-xl border border-gray-200 p-4 max-w-sm z-10">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: getNodeColor(node.group) }}
            ></div>
            <h4 className="font-semibold text-gray-900">{node.label}</h4>
          </div>
          <p className="text-xs text-gray-500 uppercase tracking-wide">{node.type}</p>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 transition-colors"
          aria-label="Close panel"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Details */}
      <div className="border-t border-gray-200 pt-3">
        {renderNodeDetails()}
      </div>

      {/* Node ID (for debugging/reference) */}
      <div className="border-t border-gray-200 mt-3 pt-3">
        <div className="text-xs text-gray-400 break-all">ID: {node.id}</div>
      </div>
    </div>
  );
};

// Helper component for detail rows
const DetailRow: React.FC<{ label: string; value: string | number }> = ({ label, value }) => {
  return (
    <div className="mb-2">
      <div className="text-xs font-semibold text-gray-500 uppercase">{label}</div>
      <div className="text-sm text-gray-900">{value}</div>
    </div>
  );
};

// Node color mapping (should match KnowledgeGraphViz)
const getNodeColor = (group: string): string => {
  const colors: Record<string, string> = {
    disease: '#ef4444',
    gene: '#3b82f6',
    phenotype: '#10b981',
    variant: '#f59e0b',
    treatment: '#8b5cf6',
  };
  return colors[group] || '#94a3b8';
};

export default NodeDetailPanel;
