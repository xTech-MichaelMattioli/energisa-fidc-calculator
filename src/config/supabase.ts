// Configuração do Supabase
export const supabaseConfig = {
  url: 'https://jlvkyasuvvgjdamhnwlb.supabase.co',
  anonKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Impsdmt5YXN1dnZnamRhbWhud2xiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI3MzMyOTAsImV4cCI6MjA2ODMwOTI5MH0.CVhdtnlSphfZTJD1qibN_jQnpu6hog1E27f-RrLI8us',
  storage: {
    bucket: 'excel-uploads',
    maxFileSize: 100 * 1024 * 1024, // 100MB
    allowedMimeTypes: [
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-excel',
      'text/csv',
      'application/octet-stream'
    ]
  },
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true
  }
};

export default supabaseConfig;
