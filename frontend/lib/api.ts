/**
 * API client for communicating with the backend FastAPI server
 */
import axios from "axios";
import type { ClinicalScenario, ScenarioResponse, WorkflowData } from "@/types/clinical";

// Create axios instance with default configuration
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "/api",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000, // 30 seconds
});

/**
 * Process a clinical scenario and get diagnostic recommendations
 */
export async function processScenario(
  scenario: ClinicalScenario
): Promise<ScenarioResponse> {
  const response = await apiClient.post<ScenarioResponse>(
    "/scenarios/process",
    scenario
  );
  return response.data;
}

/**
 * Get workflow visualization data for a processed scenario
 */
export async function getWorkflowData(scenarioId: string): Promise<WorkflowData> {
  const response = await apiClient.get<WorkflowData>(
    `/workflow-data/${scenarioId}`
  );
  return response.data;
}

/**
 * Get a previously processed scenario by ID
 */
export async function getScenario(scenarioId: string): Promise<ScenarioResponse> {
  const response = await apiClient.get<ScenarioResponse>(
    `/scenarios/${scenarioId}`
  );
  return response.data;
}

/**
 * Health check endpoint
 */
export async function healthCheck(): Promise<any> {
  const response = await apiClient.get("/health");
  return response.data;
}

// Export the configured axios instance for custom requests
export { apiClient };
