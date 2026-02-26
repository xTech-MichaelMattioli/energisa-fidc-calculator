/**
 * Service: Supabase Storage Upload
 * Uploads files to the 'temp' bucket in Supabase Storage.
 *
 * Folder structure inside the bucket:
 *   temp/
 *     bases/          ← distribuidora/VOLTZ Excel files
 *     indices/        ← IGP-M/IPCA index files
 *     taxas/          ← recovery rate files
 *     di-pre/         ← DI-PRE / CDI files
 *
 * Each upload is namespaced by a session ID (UUID) to avoid collisions.
 */
import { supabase, isSupabaseConfigured } from "@/lib/supabase";

const BUCKET = "temp";

export type StorageFolder = "bases" | "indices" | "taxas" | "di-pre";

export interface StorageUploadResult {
  path: string;
  fullUrl: string;
  fileName: string;
  size: number;
  folder: StorageFolder;
}

/**
 * Generate a unique session prefix for this browser session.
 * Persisted in sessionStorage so it survives page refreshes.
 */
function getSessionId(): string {
  const KEY = "fidc_session_id";
  let id = sessionStorage.getItem(KEY);
  if (!id) {
    id = crypto.randomUUID();
    sessionStorage.setItem(KEY, id);
  }
  return id;
}

/**
 * Build the remote path:  <folder>/<sessionId>/<sanitizedFileName>
 */
function buildPath(folder: StorageFolder, fileName: string): string {
  const sessionId = getSessionId();
  const safe = fileName.replace(/[^a-zA-Z0-9._-]/g, "_");
  return `${folder}/${sessionId}/${safe}`;
}

/**
 * Upload a single file to the temp bucket.
 */
export async function uploadFileToStorage(
  file: File,
  folder: StorageFolder
): Promise<StorageUploadResult> {
  if (!isSupabaseConfigured() || !supabase) {
    throw new Error("Supabase não configurado. Verifique as variáveis VITE_SUPABASE_URL e VITE_SUPABASE_ANON_KEY.");
  }

  const path = buildPath(folder, file.name);

  const { error } = await supabase.storage
    .from(BUCKET)
    .upload(path, file, {
      cacheControl: "3600",
      upsert: true,
    });

  if (error) {
    throw new Error(`Erro ao fazer upload de "${file.name}": ${error.message}`);
  }

  const { data: urlData } = supabase.storage
    .from(BUCKET)
    .getPublicUrl(path);

  return {
    path,
    fullUrl: urlData.publicUrl,
    fileName: file.name,
    size: file.size,
    folder,
  };
}

/**
 * Upload multiple files to the same folder in parallel.
 */
export async function uploadFilesToStorage(
  files: File[],
  folder: StorageFolder
): Promise<StorageUploadResult[]> {
  return Promise.all(files.map((f) => uploadFileToStorage(f, folder)));
}

/**
 * List files in a folder for the current session.
 */
export async function listSessionFiles(
  folder: StorageFolder
): Promise<Array<{ name: string; size: number; createdAt: string }>> {
  if (!isSupabaseConfigured() || !supabase) return [];

  const prefix = `${folder}/${getSessionId()}`;
  const { data, error } = await supabase.storage
    .from(BUCKET)
    .list(prefix, { limit: 100 });

  if (error || !data) return [];

  return data.map((f) => ({
    name: f.name,
    size: f.metadata?.size ?? 0,
    createdAt: f.created_at,
  }));
}

/**
 * Delete a file from the temp bucket.
 */
export async function deleteFileFromStorage(path: string): Promise<void> {
  if (!isSupabaseConfigured() || !supabase) return;

  const { error } = await supabase.storage
    .from(BUCKET)
    .remove([path]);

  if (error) {
    throw new Error(`Erro ao remover arquivo: ${error.message}`);
  }
}

/**
 * Delete all files for the current session in a specific folder.
 */
export async function clearSessionFolder(folder: StorageFolder): Promise<void> {
  if (!isSupabaseConfigured() || !supabase) return;

  const prefix = `${folder}/${getSessionId()}`;
  const { data } = await supabase.storage
    .from(BUCKET)
    .list(prefix, { limit: 1000 });

  if (data && data.length > 0) {
    const paths = data.map((f) => `${prefix}/${f.name}`);
    await supabase.storage.from(BUCKET).remove(paths);
  }
}

/**
 * Get download URL (signed, 1 hour expiry) for a stored file.
 */
export async function getSignedUrl(path: string): Promise<string | null> {
  if (!isSupabaseConfigured() || !supabase) return null;

  const { data, error } = await supabase.storage
    .from(BUCKET)
    .createSignedUrl(path, 3600);

  if (error || !data) return null;
  return data.signedUrl;
}
