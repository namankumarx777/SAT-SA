import {
  EntityRisk,
  RiskContribution,
  ReviewQueueItem,
  FindingDetailResponse,
  ManifestData,
  BlockchainStatus,
  VerificationResult,
  LedgerRecord,
  LedgerHistoryEntry,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

export async function apiFetch<T>(
  path: string,
  options?: RequestInit & { timeoutMs?: number },
): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const timeoutMs = options?.timeoutMs ?? 30000;
  
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  
  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...(options?.headers ?? {}),
      },
    });
    
    clearTimeout(timeoutId);

    if (!response.ok) {
      const errBody = await response.text().catch(() => "");
      throw new Error(
        `API request failed: ${response.status} ${response.statusText} - ${errBody}`,
      );
    }

    return (await response.json()) as T;
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      console.error(`Request to ${url} timed out after ${timeoutMs}ms`);
      throw new Error(`API Request Timed Out (${timeoutMs}ms)`);
    }
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
  getBlockchainStatus: () =>
    apiFetch<BlockchainStatus>("/blockchain/status"),
  verifyRecord: (recordId: string, expectedHash?: string) =>
    apiFetch<VerificationResult>(`/blockchain/records/${encodeURIComponent(recordId)}/verify`, {
      method: "POST",
      body: JSON.stringify(expectedHash ? { expected_hash: expectedHash } : {}),
    }),
  getLedgerRecords: () =>
    apiFetch<LedgerRecord[]>("/blockchain/records"),
  getAllLedgerHistory: () =>
    apiFetch<LedgerHistoryEntry[]>("/blockchain/history"),
  seedLedger: () =>
    apiFetch<{ status: string; seeded_count: number; total_records: number }>("/blockchain/seed", {
      method: "POST",
      body: JSON.stringify({}),
    }),
  getLedgerRecord: (recordId: string) =>
    apiFetch<LedgerRecord>(`/blockchain/records/${encodeURIComponent(recordId)}`),
  getLedgerHistory: (recordId: string) =>
    apiFetch<LedgerHistoryEntry[]>(`/blockchain/records/${encodeURIComponent(recordId)}/history`),
  registerFinding: (findingId: string) =>
    apiFetch<any>(`/blockchain/findings/${encodeURIComponent(findingId)}/register`, {
      method: "POST",
      body: JSON.stringify({}),
    }),
};