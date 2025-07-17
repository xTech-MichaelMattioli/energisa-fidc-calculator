import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { supabaseExcelService } from '../../services/supabaseExcelService';
import { Activity, Clock, Zap, Server } from 'lucide-react';

interface UploadStats {
  latency: number;
  uploadSpeed: number;
  status: 'testing' | 'good' | 'fair' | 'poor' | 'error';
}

export const UploadStatsWidget: React.FC = () => {
  const [stats, setStats] = useState<UploadStats | null>(null);
  const [loading, setLoading] = useState(false);

  const testPerformance = async () => {
    setLoading(true);
    try {
      const result = await supabaseExcelService.testUploadPerformance();
      
      if (result.success) {
        const speed = result.uploadSpeed || 0;
        let status: UploadStats['status'] = 'good';
        
        // Classificar performance baseada na velocidade
        if (speed < 100000) status = 'poor'; // < 100KB/s
        else if (speed < 500000) status = 'fair'; // < 500KB/s
        else status = 'good'; // >= 500KB/s
        
        setStats({
          latency: result.latency,
          uploadSpeed: speed,
          status
        });
      } else {
        setStats({
          latency: 0,
          uploadSpeed: 0,
          status: 'error'
        });
      }
    } catch (error) {
      setStats({
        latency: 0,
        uploadSpeed: 0,
        status: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    testPerformance();
  }, []);

  const formatSpeed = (bytesPerSecond: number) => {
    if (bytesPerSecond < 1024) return `${bytesPerSecond.toFixed(0)} B/s`;
    if (bytesPerSecond < 1024 * 1024) return `${(bytesPerSecond / 1024).toFixed(1)} KB/s`;
    return `${(bytesPerSecond / (1024 * 1024)).toFixed(1)} MB/s`;
  };

  const getStatusConfig = (status: UploadStats['status']) => {
    switch (status) {
      case 'good':
        return { color: 'bg-green-500', label: 'Excelente', variant: 'default' as const };
      case 'fair':
        return { color: 'bg-yellow-500', label: 'Razoável', variant: 'secondary' as const };
      case 'poor':
        return { color: 'bg-red-500', label: 'Ruim', variant: 'destructive' as const };
      case 'error':
        return { color: 'bg-gray-500', label: 'Erro', variant: 'destructive' as const };
      default:
        return { color: 'bg-blue-500', label: 'Testando...', variant: 'secondary' as const };
    }
  };

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm">
          <Activity className="h-4 w-4" />
          Performance de Upload
        </CardTitle>
        <CardDescription className="text-xs">
          Status da conexão com o Supabase Storage
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-3">
        {loading ? (
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            <span className="text-sm text-gray-600">Testando conexão...</span>
          </div>
        ) : stats ? (
          <>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Status:</span>
              <Badge variant={getStatusConfig(stats.status).variant}>
                {getStatusConfig(stats.status).label}
              </Badge>
            </div>
            
            {stats.status !== 'error' && (
              <>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1">
                    <Clock className="h-3 w-3 text-gray-500" />
                    <span className="text-sm">Latência:</span>
                  </div>
                  <span className="text-sm font-mono">{stats.latency}ms</span>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1">
                    <Zap className="h-3 w-3 text-gray-500" />
                    <span className="text-sm">Velocidade:</span>
                  </div>
                  <span className="text-sm font-mono">{formatSpeed(stats.uploadSpeed)}</span>
                </div>
              </>
            )}
            
            <div className="pt-2 border-t">
              <div className="flex items-center gap-1 text-xs text-gray-500">
                <Server className="h-3 w-3" />
                <span>Upload direto para Supabase Storage</span>
              </div>
            </div>
          </>
        ) : (
          <div className="text-sm text-gray-500">
            Não foi possível testar a performance
          </div>
        )}
      </CardContent>
    </Card>
  );
};
