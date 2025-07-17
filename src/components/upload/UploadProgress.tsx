import React from 'react';
import { Progress } from '../ui/progress';
import { Card, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import { CheckCircle, Upload, AlertCircle, X } from 'lucide-react';
import { Button } from '../ui/button';

interface UploadProgressProps {
  fileName: string;
  fileSize: number;
  progress: number;
  status: 'uploading' | 'processing' | 'validating' | 'success' | 'error';
  error?: string;
  onCancel?: () => void;
}

export const UploadProgress: React.FC<UploadProgressProps> = ({
  fileName,
  fileSize,
  progress,
  status,
  error,
  onCancel
}) => {
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusConfig = () => {
    switch (status) {
      case 'uploading':
        return {
          icon: <Upload className="h-4 w-4 animate-pulse" />,
          label: 'Enviando...',
          color: 'bg-blue-500',
          variant: 'secondary' as const
        };
      case 'processing':
        return {
          icon: <Upload className="h-4 w-4 animate-spin" />,
          label: 'Processando...',
          color: 'bg-yellow-500',
          variant: 'secondary' as const
        };
      case 'validating':
        return {
          icon: <AlertCircle className="h-4 w-4 animate-pulse" />,
          label: 'Validando...',
          color: 'bg-orange-500',
          variant: 'secondary' as const
        };
      case 'success':
        return {
          icon: <CheckCircle className="h-4 w-4" />,
          label: 'Concluído',
          color: 'bg-green-500',
          variant: 'default' as const
        };
      case 'error':
        return {
          icon: <X className="h-4 w-4" />,
          label: 'Erro',
          color: 'bg-red-500',
          variant: 'destructive' as const
        };
      default:
        return {
          icon: <Upload className="h-4 w-4" />,
          label: 'Preparando...',
          color: 'bg-gray-500',
          variant: 'secondary' as const
        };
    }
  };

  const statusConfig = getStatusConfig();

  return (
    <Card className="w-full">
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            {statusConfig.icon}
            <span className="font-medium text-sm truncate max-w-xs">
              {fileName}
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant={statusConfig.variant} className="text-xs">
              {statusConfig.label}
            </Badge>
            {onCancel && status === 'uploading' && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onCancel}
                className="h-6 w-6 p-0"
              >
                <X className="h-3 w-3" />
              </Button>
            )}
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex justify-between text-xs text-gray-600">
            <span>{formatFileSize(fileSize)}</span>
            <span>{progress}%</span>
          </div>
          
          <Progress 
            value={progress} 
            className="h-2"
          />
          
          {error && (
            <div className="text-xs text-red-600 bg-red-50 p-2 rounded">
              {error}
            </div>
          )}
          
          {status === 'success' && (
            <div className="text-xs text-green-600 bg-green-50 p-2 rounded">
              ✅ Arquivo enviado com sucesso!
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
