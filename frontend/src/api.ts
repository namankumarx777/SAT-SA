import {
  EntityRisk,
  RiskContribution,
  ReviewQueueItem,
  FindingDetailResponse,
  ManifestData,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

export async function apiFetch<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options?.headers ?? {}),
      },
    });

    if (!response.ok) {
      throw new Error(
        `API request failed: ${response.status} ${response.statusText}`,
      );
    }

    return (await response.json()) as T;
  } catch (err: any) {
    console.error(`Fetch error for ${url}:`, err);
    throw err;
  }
}

export const api = {
  getEntities: () => apiFetch<EntityRisk[]>("/analytics/supervisory-risk/entities"),
  getEntity: (entityId: string) =>
    apiFetch<EntityRisk>(`/analytics/supervisory-risk/entities/${encodeURIComponent(entityId)}`),
  getContributions: (entityId: string) =>
    apiFetch<RiskContribution[]>(
      `/analytics/supervisory-risk/contributions/${encodeURIComponent(entityId)}`,
    ),
  getReviewQueue: () =>
    apiFetch<ReviewQueueItem[]>("/analytics/supervisory-risk/review-queue"),
  getReviewQueueItem: (recordId: string) =>
    apiFetch<ReviewQueueItem>(
      `/analytics/supervisory-risk/review-queue/${encodeURIComponent(recordId)}`,
    ),
  getManifest: () =>
    apiFetch<ManifestData>("/analytics/supervisory-risk/manifest"),
  getFindingDetail: (findingId: string) =>
    apiFetch<FindingDetailResponse>(
      `/analytics/supervisory-risk/findings/${encodeURIComponent(findingId)}`,
    ),
  getEntityDossier: (entityId: string) =>
    apiFetch<any>(`/analytics/supervisory-risk/entities/${encodeURIComponent(entityId)}/dossier`),
  getDossierHtmlUrl: (entityId: string) =>
    `${API_BASE_URL}/analytics/supervisory-risk/entities/${encodeURIComponent(entityId)}/dossier/html`,
};