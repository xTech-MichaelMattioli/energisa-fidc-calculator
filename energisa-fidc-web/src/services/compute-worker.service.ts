/**
 * Service: FIDC Compute Worker
 * Comunica com o worker Python (Railway) para cálculo vetorizado server-side.
 * O worker lê CSVs diretamente do Supabase Storage, computa tudo e retorna
 * csv_url + summary (FidcSummary-compatible) para os cards do frontend.
 */

import type { FidcSummary } from "./processing-db.service";

const WORKER_URL = import.meta.env.VITE_WORKER_URL as string | undefined;

export interface WorkerJobStatus {
  job_id:     string;
  status:     "pending" | "processing" | "done" | "error";
  rows_total: number | null;
  rows_done:  number | null;
  csv_url:    string | null;
  error:      string | null;
  /** Summary retornado pelo worker quando status === "done" */
  summary:    FidcSummary | null;
}

export function isWorkerConfigured(): boolean {
  return !!WORKER_URL;
}

/**
 * Dispara o cálculo no worker. Retorna job_id imediatamente.
 */
export async function triggerComputeJob(sessionId: string): Promise<string> {
  if (!WORKER_URL) throw new Error("VITE_WORKER_URL não configurado.");

  const res = await fetch(`${WORKER_URL}/compute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Worker erro ${res.status}: ${text}`);
  }

  const data = await res.json();
  return data.job_id as string;
}

/**
 * Consulta o status atual de um job.
 */
export async function getJobStatus(jobId: string): Promise<WorkerJobStatus> {
  if (!WORKER_URL) throw new Error("VITE_WORKER_URL não configurado.");

  const res = await fetch(`${WORKER_URL}/jobs/${jobId}`);
  if (!res.ok) throw new Error(`Job não encontrado: ${jobId}`);
  return res.json() as Promise<WorkerJobStatus>;
}

/**
 * Retorna o job mais recente de uma sessão, ou null se não houver.
 * Permite recuperar csv_url + summary após navegação entre páginas.
 */
export async function getLatestSessionJob(sessionId: string): Promise<WorkerJobStatus | null> {
  if (!WORKER_URL) return null;
  try {
    const res = await fetch(`${WORKER_URL}/sessions/${sessionId}/job`);
    if (!res.ok) return null;
    return res.json() as Promise<WorkerJobStatus | null>;
  } catch {
    return null;
  }
}

/**
 * Faz polling até o job terminar (done ou error).
 * Chama onProgress a cada atualização.
 */
export async function waitForJob(
  jobId: string,
  onProgress: (status: WorkerJobStatus) => void,
  intervalMs = 2000
): Promise<WorkerJobStatus> {
  return new Promise((resolve, reject) => {
    const tick = async () => {
      try {
        const status = await getJobStatus(jobId);
        onProgress(status);

        if (status.status === "done") {
          resolve(status);
        } else if (status.status === "error") {
          reject(new Error(status.error ?? "Erro no worker"));
        } else {
          setTimeout(tick, intervalMs);
        }
      } catch (err) {
        reject(err);
      }
    };
    tick();
  });
}
