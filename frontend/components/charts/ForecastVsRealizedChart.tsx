import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import type { ForecastVsRealized } from '../../lib/api/finance';

// Registrar componentes do Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface ForecastVsRealizedChartProps {
  data: ForecastVsRealized;
}

const ForecastVsRealizedChart: React.FC<ForecastVsRealizedChartProps> = ({ data }) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(value);
  };

  const labels = data.months.map(m => m.label);
  const realizedData = data.months.map(m => m.realized);
  const forecastData = data.months.map(m => m.forecast);

  // Calcular áreas sombreadas (onde previsto < realizado ou previsto < 0)
  const backgroundColors = data.months.map((month, index) => {
    if (month.forecast < month.realized || month.forecast < 0) {
      return 'rgba(239, 68, 68, 0.1)'; // Vermelho claro
    }
    return 'transparent';
  });

  const chartData = {
    labels,
    datasets: [
      {
        label: 'Realizado',
        data: realizedData,
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        borderWidth: 3,
        fill: false,
        tension: 0.4,
        pointBackgroundColor: '#10b981',
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        pointRadius: 5,
        pointHoverRadius: 7,
      },
      {
        label: 'Previsto',
        data: forecastData,
        borderColor: '#6366f1',
        backgroundColor: 'rgba(99, 102, 241, 0.1)',
        borderWidth: 2,
        borderDash: [5, 5],
        fill: false,
        tension: 0.4,
        pointBackgroundColor: '#6366f1',
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        pointRadius: 5,
        pointHoverRadius: 7,
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Previsto × Realizado',
        font: {
          size: 16,
          weight: 'bold' as const,
        },
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            return `${context.dataset.label}: ${formatCurrency(context.parsed.y)}`;
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: false,
        ticks: {
          callback: function(value: any) {
            return formatCurrency(value);
          }
        }
      }
    }
  };

  return (
    <div className="mb-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <div style={{ height: '400px' }}>
          <Line data={chartData} options={options} />
        </div>
        
        {/* Totais abaixo do gráfico */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t">
          <div>
            <p className="text-sm text-gray-600 mb-1">Saldo Realizado</p>
            <p className="text-xl font-bold text-gray-800">{formatCurrency(data.totals.realized)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">Saldo Previsto</p>
            <p className="text-xl font-bold text-gray-800">{formatCurrency(data.totals.forecast)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">Diferença</p>
            <p className={`text-xl font-bold ${data.totals.difference >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(data.totals.difference)}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ForecastVsRealizedChart;

