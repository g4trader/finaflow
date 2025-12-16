import React, { useState, useEffect } from 'react';
import { CheckCircle, XCircle, Clock, AlertCircle } from 'lucide-react';

interface ValidationStatus {
  status: 'SUCCESS' | 'FAILED' | 'PENDING';
  last_validation_at: string | null;
  year: number;
  message?: string;
}

interface ValidationBadgeProps {
  year: number;
}

const ValidationBadge: React.FC<ValidationBadgeProps> = ({ year }) => {
  const [validationStatus, setValidationStatus] = useState<ValidationStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchValidationStatus = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          setLoading(false);
          return;
        }

        const response = await fetch(`/api/v1/system/validation-status?year=${year}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const data = await response.json();
          setValidationStatus(data);
        }
      } catch (error) {
        console.error('Erro ao buscar status de validação:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchValidationStatus();
  }, [year]);

  if (loading || !validationStatus) {
    return null;
  }

  const getStatusConfig = () => {
    switch (validationStatus.status) {
      case 'SUCCESS':
        return {
          icon: CheckCircle,
          text: 'Dados validados com planilha',
          bgColor: 'bg-green-50',
          textColor: 'text-green-700',
          iconColor: 'text-green-600',
          borderColor: 'border-green-200'
        };
      case 'FAILED':
        return {
          icon: XCircle,
          text: 'Validação encontrou inconsistências',
          bgColor: 'bg-red-50',
          textColor: 'text-red-700',
          iconColor: 'text-red-600',
          borderColor: 'border-red-200'
        };
      case 'PENDING':
        return {
          icon: Clock,
          text: 'Validação pendente',
          bgColor: 'bg-gray-50',
          textColor: 'text-gray-700',
          iconColor: 'text-gray-600',
          borderColor: 'border-gray-200'
        };
      default:
        return null;
    }
  };

  const config = getStatusConfig();
  if (!config) return null;

  const Icon = config.icon;

  const formatDate = (dateString: string | null) => {
    if (!dateString) return null;
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return null;
    }
  };

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border ${config.bgColor} ${config.borderColor} ${config.textColor}`}>
      <Icon className={`w-4 h-4 ${config.iconColor}`} />
      <div className="flex flex-col">
        <span className="text-xs font-medium">{config.text}</span>
        {validationStatus.last_validation_at && (
          <span className="text-xs opacity-75">
            {formatDate(validationStatus.last_validation_at)}
          </span>
        )}
      </div>
    </div>
  );
};

export default ValidationBadge;

