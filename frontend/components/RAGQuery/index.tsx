"use client";

import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";

interface RAGResult {
  recommendation: string;
  source: string;
  evidence_level?: string;
  citation: string;
  confidence: number;
  chunk_id?: string;
  retrieved_text?: string;
}

interface GuidelineInfo {
  name: string;
  id: string;
  create_time?: string;
  size_bytes?: number;
  mime_type?: string;
}

/**
 * Format text with basic markdown-style rendering
 */
function formatText(text: string): JSX.Element[] {
  const lines = text.split("\n");
  const elements: JSX.Element[] = [];
  let key = 0;

  for (let i = 0; i < lines.length; i++) {
    let line = lines[i];

    // Handle horizontal rules
    if (line.trim() === "---") {
      elements.push(<hr key={key++} className="my-4 border-gray-300" />);
      continue;
    }

    // Handle headers (### Header)
    if (line.startsWith("###")) {
      const text = line.replace(/^###\s*/, "");
      elements.push(
        <h3 key={key++} className="text-lg font-bold text-gray-900 mt-4 mb-2">
          {text}
        </h3>
      );
      continue;
    }

    // Handle bold text (**text**)
    const parts = line.split(/(\*\*[^*]+\*\*)/g);
    const formatted = parts.map((part, idx) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return (
          <strong key={idx} className="font-bold text-gray-900">
            {part.slice(2, -2)}
          </strong>
        );
      }
      return <span key={idx}>{part}</span>;
    });

    // Add line with proper spacing
    if (line.trim() === "") {
      elements.push(<br key={key++} />);
    } else {
      elements.push(
        <p key={key++} className="mb-2 leading-relaxed">
          {formatted}
        </p>
      );
    }
  }

  return elements;
}

export function RAGQuery() {
  const [query, setQuery] = useState("");
  const [diseaseFilter, setDiseaseFilter] = useState("");
  const [results, setResults] = useState<RAGResult[]>([]);
  const [guidelines, setGuidelines] = useState<GuidelineInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showGuidelines, setShowGuidelines] = useState(false);

  // Load guidelines on mount
  useEffect(() => {
    loadGuidelines();
  }, []);

  const loadGuidelines = async () => {
    try {
      const response = await apiClient.get("/rag/guidelines");
      setGuidelines(response.data.guidelines || []);
    } catch (err) {
      console.error("Failed to load guidelines:", err);
    }
  };

  const handleQuery = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.post("/rag/query", {
        query: query.trim(),
        disease_code: diseaseFilter || null,
        max_results: 5,
      });

      setResults(response.data.results || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to query RAG system");
      console.error("RAG query error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleQuery();
    }
  };

  const formatFileSize = (bytes?: number): string => {
    if (!bytes) return "";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-50 to-teal-50 rounded-lg border-2 border-green-200 p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          📚 Ask Clinical Guidelines (RAG)
        </h2>
        <p className="text-gray-600 text-sm">
          Ask questions and retrieve evidence-based answers from {guidelines.length} uploaded clinical guidelines
        </p>
      </div>

      {/* Guidelines Browser */}
      <div className="bg-white rounded-lg border-2 border-gray-200 p-6">
        <button
          onClick={() => setShowGuidelines(!showGuidelines)}
          className="flex items-center justify-between w-full text-left"
        >
          <h3 className="text-lg font-semibold text-gray-900">
            📖 Uploaded Guidelines ({guidelines.length})
          </h3>
          <span className="text-gray-500">{showGuidelines ? "▼" : "▶"}</span>
        </button>

        {showGuidelines && (
          <div className="mt-4 space-y-2 max-h-60 overflow-y-auto">
            {guidelines.length === 0 ? (
              <p className="text-gray-500 text-sm italic">No guidelines uploaded yet</p>
            ) : (
              guidelines.map((guideline, idx) => (
                <div
                  key={idx}
                  className="p-3 bg-gray-50 rounded-lg border border-gray-200 hover:border-green-300 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="font-medium text-gray-900 text-sm">{guideline.name}</div>
                      <div className="text-xs text-gray-500 font-mono mt-1">{guideline.id}</div>
                    </div>
                    {guideline.size_bytes && (
                      <div className="ml-3 px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-semibold">
                        {formatFileSize(guideline.size_bytes)}
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-3 mt-2 text-xs">
                    {guideline.mime_type && (
                      <div className="text-gray-500">
                        📄 {guideline.mime_type.split('/')[1]?.toUpperCase() || 'PDF'}
                      </div>
                    )}
                    {guideline.create_time && (
                      <div className="text-gray-400">
                        📅 {new Date(guideline.create_time).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Query Interface */}
      <div className="bg-white rounded-lg border-2 border-green-200 p-6">
        <label className="block text-sm font-semibold text-gray-700 mb-2">
          Your Question
        </label>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="e.g., What are the cardiac surveillance recommendations for DMD?"
          className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none"
          rows={3}
        />

        <div className="mt-4 flex items-end gap-4">
          <div className="flex-1">
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Disease Filter (Optional)
            </label>
            <input
              type="text"
              value={diseaseFilter}
              onChange={(e) => setDiseaseFilter(e.target.value)}
              placeholder="e.g., DMD, BMD, LGMDR1"
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
            />
          </div>

          <button
            onClick={handleQuery}
            disabled={loading || !query.trim()}
            className={`px-6 py-2 rounded-lg font-bold text-white transition-all ${
              loading || !query.trim()
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-green-600 hover:bg-green-700 shadow-md hover:shadow-lg"
            }`}
          >
            {loading ? "Searching..." : "Ask Guidelines"}
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border-2 border-red-300 rounded-lg p-4">
          <div className="font-semibold text-red-900 mb-1">Error</div>
          <div className="text-red-700">{error}</div>
        </div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div className="bg-white rounded-lg border-2 border-green-200 p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4">
            Results ({results.length})
          </h3>

          <div className="space-y-6">
            {results.map((result, idx) => (
              <div
                key={idx}
                className="p-4 bg-green-50 border-2 border-green-300 rounded-lg"
              >
                {/* Result Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="text-sm font-semibold text-green-700 uppercase mb-3">
                      Gemini Clinical Synthesis
                    </div>
                    <div className="text-gray-900">
                      {formatText(result.recommendation)}
                    </div>
                  </div>
                  <div className="ml-4 flex flex-col gap-2">
                    {result.evidence_level && (
                      <span className="px-2 py-1 bg-white rounded text-xs font-bold border border-gray-300 whitespace-nowrap">
                        {result.evidence_level}
                      </span>
                    )}
                    <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs font-bold border border-purple-300 whitespace-nowrap">
                      {(result.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>

                {/* Citation */}
                <div className="mt-3 p-3 bg-white rounded border border-green-200">
                  <div className="flex items-start gap-2 mb-2">
                    <span className="font-bold text-green-700 text-sm">📄 Source:</span>
                    <span className="text-gray-700 flex-1 text-sm">
                      {result.citation}
                    </span>
                  </div>

                  {/* Retrieved Text */}
                  {result.retrieved_text && (
                    <div className="mt-3 pt-3 border-t border-green-200">
                      <div className="font-semibold text-green-800 text-xs uppercase mb-2">
                        📖 Supporting Evidence from Guidelines:
                      </div>
                      <div className="bg-gray-50 p-4 rounded border border-gray-200 text-sm text-gray-800 max-h-96 overflow-y-auto">
                        {formatText(result.retrieved_text)}
                      </div>
                    </div>
                  )}

                  {result.chunk_id && (
                    <div className="text-gray-500 mt-2 text-xs">
                      Chunk ID:{" "}
                      <code className="font-mono bg-gray-100 px-1 py-0.5 rounded">
                        {result.chunk_id}
                      </code>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
