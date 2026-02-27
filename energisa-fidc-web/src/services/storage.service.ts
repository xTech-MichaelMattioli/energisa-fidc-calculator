/**
 * Service: Supabase Storage
 *
 * NEW architecture — "upload first, validate later":
 *
 *   temp/
 *     para_validacao/<sessionId>/   ← raw Excel files land here
 *     validados/<sessionId>/        ← approved files (or CSV conversions)
 *
 * Session ID = deterministic UUID derived from the browser.  Persisted in
 * sessionStorage so it survives page refreshes within the same tab.
 */
import { supabase, isSupabaseConfigured } from "@/lib/supabase";

const BUCKET = "temp";

export type StorageStage = "para_validacao" | "validados";

/** Legacy alias kept for backward compat in other pages */
export type StorageFolder = "bases" | "indices" | "taxas" | "di-pre" | StorageStage;

export interface StorageUploadResult {
  path: string;
  fullUrl: string;
  fileName: string;
  size: number;
  stage: StorageStage;
}

/**
 * Progress callback: (loaded bytes, total bytes, percent 0-100)
 */
export type UploadProgressCallback = (loaded: number, total: number, percent: number) => void;

// ─── Session ID ───────────────────────────────────────────────────

function getSessionId(): string {
  const KEY = "fidc_session_id";
  let id = sessionStorage.getItem(KEY);
  if (!id) {
    id = crypto.randomUUID();
    sessionStorage.setItem(KEY, id);
  }
  return id;
}

export function getCurrentSessionId(): string {
  return getSessionId();
}

// ─── Path builders ────────────────────────────────────────────────

function buildStagePath(stage: StorageStage, fileName: string): string {
  const sessionId = getSessionId();
  const safe = fileName.replace(/[^a-zA-Z0-9._-]/g, "_");
  return `${stage}/${sessionId}/${safe}`;
}

/** @deprecated — kept for indices / taxas / di-pre uploads */
function buildLegacyPath(folder: string, fileName: string): string {
  const sessionId = getSessionId();
  const safe = fileName.replace(/[^a-zA-Z0-9._-]/g, "_");
  return `${folder}/${sessionId}/${safe}`;
}

// ─── Upload ───────────────────────────────────────────────────────

/**
 * Upload a file directly to `para_validacao/<session>/` with progress.
 * No local parsing, no edge function — just raw upload.
 */
export async function uploadFileForValidation(
  file: File,
  onProgress?: UploadProgressCallback
): Promise<StorageUploadResult> {
  if (!isSupabaseConfigured() || !supabase) {
    throw new Error("Supabase não configurado.");
  }

  const path = buildStagePath("para_validacao", file.name);
  const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;
  const apiUrl = import.meta.env.VITE_SUPABASE_URL;
  const uploadUrl = `${apiUrl}/storage/v1/object/${BUCKET}/${path}`;

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener("progress", (evt) => {
      if (evt.lengthComputable && onProgress) {
        onProgress(evt.loaded, evt.total, (evt.loaded / evt.total) * 100);
      }
    });

    xhr.addEventListener("load", () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        const { data: urlData } = supabase!.storage.from(BUCKET).getPublicUrl(path);
        resolve({
          path,
          fullUrl: urlData.publicUrl,
          fileName: file.name,
          size: file.size,
          stage: "para_validacao",
        });
      } else {
        reject(new Error(`Upload falhou — status ${xhr.status}`));
      }
    });

    xhr.addEventListener("error", () =>
      reject(new Error(`Erro de rede ao enviar "${file.name}"`))
    );
    xhr.addEventListener("abort", () =>
      reject(new Error(`Upload cancelado: "${file.name}"`))
    );

    xhr.open("POST", uploadUrl);
    xhr.setRequestHeader("Authorization", `Bearer ${anonKey}`);
    xhr.setRequestHeader("x-upsert", "true");
    xhr.send(file);
  });
}

/**
 * Upload a raw CSV buffer (from the Worker conversion) to
 * `para_validacao/<session>/file.csv` with XHR progress.
 *
 * The original Excel name is used with .csv extension.
 */
export async function uploadCsvBlob(
  csvBuffer: ArrayBuffer,
  originalFileName: string,
  onProgress?: UploadProgressCallback,
): Promise<StorageUploadResult> {
  if (!isSupabaseConfigured() || !supabase) {
    throw new Error("Supabase não configurado.");
  }

  // file.xlsx → file.csv
  const csvName = originalFileName.replace(/\.xlsx?$/i, ".csv");
  const path = buildStagePath("para_validacao", csvName);
  const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;
  const apiUrl = import.meta.env.VITE_SUPABASE_URL;
  const uploadUrl = `${apiUrl}/storage/v1/object/${BUCKET}/${path}`;

  const blob = new Blob([csvBuffer], { type: "text/csv;charset=utf-8" });

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener("progress", (evt) => {
      if (evt.lengthComputable && onProgress) {
        onProgress(evt.loaded, evt.total, (evt.loaded / evt.total) * 100);
      }
    });

    xhr.addEventListener("load", () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        const { data: urlData } = supabase!.storage.from(BUCKET).getPublicUrl(path);
        resolve({
          path,
          fullUrl: urlData.publicUrl,
          fileName: csvName,
          size: blob.size,
          stage: "para_validacao",
        });
      } else {
        reject(new Error(`Upload CSV falhou — status ${xhr.status}`));
      }
    });

    xhr.addEventListener("error", () =>
      reject(new Error(`Erro de rede ao enviar CSV "${csvName}"`)),
    );
    xhr.addEventListener("abort", () =>
      reject(new Error(`Upload cancelado: "${csvName}"`)),
    );

    xhr.open("POST", uploadUrl);
    xhr.setRequestHeader("Authorization", `Bearer ${anonKey}`);
    xhr.setRequestHeader("Content-Type", "text/csv");
    xhr.setRequestHeader("x-upsert", "true");
    xhr.send(blob);
  });
}

/**
 * Upload a file to the legacy folder structure (for indices, taxas, etc.)
 */
export async function uploadFileToStorage(
  file: File,
  folder: StorageFolder,
  onProgress?: UploadProgressCallback
): Promise<StorageUploadResult> {
  if (!isSupabaseConfigured() || !supabase) {
    throw new Error("Supabase não configurado.");
  }

  const path = buildLegacyPath(folder, file.name);
  const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;
  const apiUrl = import.meta.env.VITE_SUPABASE_URL;
  const uploadUrl = `${apiUrl}/storage/v1/object/${BUCKET}/${path}`;

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener("progress", (evt) => {
      if (evt.lengthComputable && onProgress) {
        onProgress(evt.loaded, evt.total, (evt.loaded / evt.total) * 100);
      }
    });

    xhr.addEventListener("load", () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        const { data: urlData } = supabase!.storage.from(BUCKET).getPublicUrl(path);
        resolve({
          path,
          fullUrl: urlData.publicUrl,
          fileName: file.name,
          size: file.size,
          stage: "para_validacao",
        });
      } else {
        reject(new Error(`Upload falhou — status ${xhr.status}`));
      }
    });

    xhr.addEventListener("error", () =>
      reject(new Error(`Erro de rede ao enviar "${file.name}"`))
    );
    xhr.addEventListener("abort", () =>
      reject(new Error(`Upload cancelado: "${file.name}"`))
    );

    xhr.open("POST", uploadUrl);
    xhr.setRequestHeader("Authorization", `Bearer ${anonKey}`);
    xhr.setRequestHeader("x-upsert", "true");
    xhr.send(file);
  });
}

/**
 * Upload multiple files in parallel (legacy compat).
 */
export async function uploadFilesToStorage(
  files: File[],
  folder: StorageFolder,
  onProgress?: (fileIndex: number, loaded: number, total: number, percent: number) => void
): Promise<StorageUploadResult[]> {
  return Promise.all(
    files.map((f, idx) =>
      uploadFileToStorage(f, folder, (loaded, total, percent) => {
        onProgress?.(idx, loaded, total, percent);
      })
    )
  );
}

// ─── List / Query ─────────────────────────────────────────────────

export interface StoredFileInfo {
  name: string;
  path: string;
  size: number;
  createdAt: string;
}

/**
 * List files in a stage folder for the current session.
 */
export async function listSessionStageFiles(
  stage: StorageStage
): Promise<StoredFileInfo[]> {
  if (!isSupabaseConfigured() || !supabase) return [];

  const prefix = `${stage}/${getSessionId()}`;
  const { data, error } = await supabase.storage
    .from(BUCKET)
    .list(prefix, { limit: 100 });

  if (error || !data) return [];

  return data
    .filter((f) => f.name && !f.name.startsWith("."))
    .map((f) => ({
      name: f.name,
      path: `${prefix}/${f.name}`,
      size: f.metadata?.size ?? 0,
      createdAt: f.created_at,
    }));
}

/** @deprecated — use listSessionStageFiles */
export async function listSessionFiles(
  folder: StorageFolder
): Promise<Array<{ name: string; size: number; createdAt: string }>> {
  if (!isSupabaseConfigured() || !supabase) return [];
  const prefix = `${folder}/${getSessionId()}`;
  const { data, error } = await supabase.storage.from(BUCKET).list(prefix, { limit: 100 });
  if (error || !data) return [];
  return data.map((f) => ({ name: f.name, size: f.metadata?.size ?? 0, createdAt: f.created_at }));
}

// ─── Move / Copy ──────────────────────────────────────────────────

/**
 * Move a file from para_validacao → validados (by copy + delete).
 * Supabase storage doesn't have rename/move, so we download + re-upload.
 */
export async function moveToValidados(storagePath: string): Promise<string> {
  if (!isSupabaseConfigured() || !supabase) {
    throw new Error("Supabase não configurado.");
  }

  const fileName = storagePath.split("/").pop()!;
  const destPath = buildStagePath("validados", fileName);

  // Download
  const { data: blob, error: dlErr } = await supabase.storage
    .from(BUCKET)
    .download(storagePath);

  if (dlErr || !blob) throw new Error(`Download falhou: ${dlErr?.message}`);

  // Upload to new location
  const { error: upErr } = await supabase.storage
    .from(BUCKET)
    .upload(destPath, blob, { cacheControl: "3600", upsert: true });

  if (upErr) throw new Error(`Re-upload falhou: ${upErr.message}`);

  // Delete original
  await supabase.storage.from(BUCKET).remove([storagePath]);

  return destPath;
}

// ─── Delete ───────────────────────────────────────────────────────

export async function deleteFileFromStorage(path: string): Promise<void> {
  if (!isSupabaseConfigured() || !supabase) return;
  const { error } = await supabase.storage.from(BUCKET).remove([path]);
  if (error) throw new Error(`Erro ao remover arquivo: ${error.message}`);
}

export async function clearSessionFolder(folder: StorageFolder | StorageStage): Promise<void> {
  if (!isSupabaseConfigured() || !supabase) return;
  const prefix = `${folder}/${getSessionId()}`;
  const { data } = await supabase.storage.from(BUCKET).list(prefix, { limit: 1000 });
  if (data && data.length > 0) {
    const paths = data.map((f) => `${prefix}/${f.name}`);
    await supabase.storage.from(BUCKET).remove(paths);
  }
}

// ─── Signed URL ───────────────────────────────────────────────────

export async function getSignedUrl(path: string): Promise<string | null> {
  if (!isSupabaseConfigured() || !supabase) return null;
  const { data, error } = await supabase.storage.from(BUCKET).createSignedUrl(path, 3600);
  if (error || !data) return null;
  return data.signedUrl;
}
