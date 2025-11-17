"use client";

import { useState } from "react";
import type { ClinicalScenario, ScenarioResponse } from "@/types/clinical";
import { processScenario } from "@/lib/api";
import { buildWorkflowGraph } from "@/lib/workflowBuilder";
import { WorkflowGraph } from "@/components/WorkflowGraph";
import { ResultsPanel } from "@/components/ResultsPanel";
import { ExampleScenarios } from "@/components/ExampleScenarios";
import { RAGQuery } from "@/components/RAGQuery";

export default function Home() {
  const [currentScenario, setCurrentScenario] = useState<ClinicalScenario | null>(null);
  const [response, setResponse] = useState<ScenarioResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLoadScenario = (scenario: ClinicalScenario) => {
    setCurrentScenario(scenario);
    setResponse(null);
    setError(null);
  };

  const handleProcessScenario = async () => {
    if (!currentScenario) return;

    setLoading(true);
    setError(null);

    try {
      const result = await processScenario(currentScenario);
      setResponse(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to process scenario. Make sure the backend server is running."
      );
      console.error("Error processing scenario:", err);
    } finally {
      setLoading(false);
    }
  };

  const workflowData = response
    ? buildWorkflowGraph(response, currentScenario)
    : null;

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      <div className="max-w-7xl mx-auto p-8">
        {/* Header */}
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Clinical Decision Support System
          </h1>
          <p className="text-gray-600">
            Knowledge graph-driven diagnostic support for rare muscular dystrophies
          </p>
          <div className="mt-2 text-sm text-gray-500">
            Powered by Monarch Initiative + Curated Clinical Guidelines
          </div>
        </header>

        {/* Example Scenarios */}
        <div className="mb-8">
          <ExampleScenarios onLoadScenario={handleLoadScenario} />
        </div>

        {/* RAG Query Interface */}
        <div className="mb-8">
          <RAGQuery />
        </div>

        {/* Current Scenario Display */}
        {currentScenario && (
          <div className="mb-8 bg-white rounded-lg border-2 border-blue-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold text-gray-900">Current Scenario</h2>
              <button
                onClick={handleProcessScenario}
                disabled={loading}
                className={`px-6 py-3 rounded-lg font-bold text-white transition-all ${
                  loading
                    ? "bg-gray-400 cursor-not-allowed"
                    : "bg-blue-600 hover:bg-blue-700 shadow-md hover:shadow-lg"
                }`}
              >
                {loading ? "Processing..." : "Analyze Scenario"}
              </button>
            </div>

            {/* Scenario Summary */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <div className="font-semibold text-gray-700">Patient</div>
                <div className="text-gray-900">
                  {currentScenario.patient.age}, {currentScenario.patient.sex}
                </div>
              </div>
              <div>
                <div className="font-semibold text-gray-700">Chief Complaint</div>
                <div className="text-gray-900">{currentScenario.chief_complaint}</div>
              </div>
              <div>
                <div className="font-semibold text-gray-700">Symptoms</div>
                <div className="text-gray-900">
                  {currentScenario.presenting_symptoms.length} symptoms
                </div>
              </div>
            </div>

            {currentScenario.genetic_findings && currentScenario.genetic_findings.length > 0 && (
              <div className="mt-4 p-3 bg-indigo-50 rounded border border-indigo-200">
                <div className="font-semibold text-indigo-900 mb-1">Genetic Data Available</div>
                {currentScenario.genetic_findings.map((gf, idx) => (
                  <div key={idx} className="text-sm text-indigo-800">
                    {gf.gene} {gf.variant_type}
                    {gf.exons_affected && ` (exons ${gf.exons_affected.join(", ")})`}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="mb-8 bg-red-50 border-2 border-red-300 rounded-lg p-6">
            <h3 className="text-lg font-bold text-red-900 mb-2">Error</h3>
            <p className="text-red-700">{error}</p>
            <div className="mt-4 text-sm text-red-600">
              <strong>Troubleshooting:</strong>
              <ul className="list-disc list-inside mt-2">
                <li>Ensure the backend server is running: <code>uvicorn backend.api.main:app --reload</code></li>
                <li>Check that Neo4j is running (or in-memory fallback is active)</li>
                <li>Verify the API is accessible at <code>http://localhost:8000</code></li>
              </ul>
            </div>
          </div>
        )}

        {/* Results */}
        {response && workflowData && currentScenario && (
          <div className="space-y-8">
            {/* Workflow Visualization */}
            <div className="bg-white rounded-lg border-2 border-gray-200 p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Clinical Reasoning Workflow
              </h2>
              <p className="text-gray-600 mb-4">
                Interactive visualization showing how the system processes your clinical scenario
                through the knowledge graph to generate recommendations.
              </p>
              <WorkflowGraph
                nodes={workflowData.nodes}
                edges={workflowData.edges}
              />
            </div>

            {/* Results Panel */}
            <ResultsPanel response={response} scenario={currentScenario} />
          </div>
        )}

        {/* Footer */}
        <footer className="mt-12 pt-8 border-t border-gray-200 text-center text-sm text-gray-500">
          <p className="mb-2">
            <strong>Disclaimer:</strong> This is a clinical decision support tool, not a
            replacement for clinical judgment. All recommendations should be reviewed by qualified
            healthcare professionals.
          </p>
          <p>
            Data sources: Monarch Initiative Knowledge Graph • Curated Clinical Guidelines (TREAT-NMD, ACMG)
          </p>
        </footer>
      </div>
    </main>
  );
}
