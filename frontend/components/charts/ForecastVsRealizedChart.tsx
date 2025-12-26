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

  // Cores dinâmicas baseadas em positivo/negativo
  const getColorForValue = (value: number) => {
    return value >= 0 ? '#3b82f6' : '#ef4444'; // Azul se positivo, vermelho se negativo
  };

  // Criar arrays de cores para cada ponto
  const realizedPointColors = realizedData.map(v => getColorForValue(v));
  const forecastPointColors = forecastData.map(v => getColorForValue(v));

  // Determinar cor média para a linha (usar cor do último ponto como referência)
  const lastRealizedValue = realizedData[realizedData.length - 1];
  const lastForecastValue = forecastData[forecastData.length - 1];

  const chartData = {
    labels,
    datasets: [
      {
        label: 'Saldo Realizado',
        data: realizedData,
        borderColor: getColorForValue(lastRealizedValue), // Cor baseada no último valor
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 3,
        fill: false,
        tension: 0.4,
        pointBackgroundColor: realizedPointColors,
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        pointRadius: 5,
        pointHoverRadius: 7,
        segment: {
          borderColor: (ctx: any) => {
            // Usar cor do ponto inicial do segmento
            const current = realizedData[ctx.p1DataIndex];
            return getColorForValue(current);
          }
        }
      },
      {
        label: 'Saldo Previsto',
        data: forecastData,
        borderColor: getColorForValue(lastForecastValue), // Cor baseada no último valor
        backgroundColor: 'rgba(99, 102, 241, 0.05)',
        borderWidth: 2,
        borderDash: [8, 4], // Linha tracejada
        fill: false,
        tension: 0.4,
        pointBackgroundColor: forecastPointColors,
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6,
        segment: {
          borderColor: (ctx: any) => {
            // Usar cor do ponto inicial do segmento
            const current = forecastData[ctx.p1DataIndex];
            return getColorForValue(current);
          }
        }
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
        beginAtZero: true, // Sempre começar do zero
        ticks: {
          callback: function(value: any) {
            return formatCurrency(value);
          }
        },
        grid: {
          color: (context: any) => {
            // Linha do zero mais destacada
            if (context.tick.value === 0) {
              return 'rgba(0, 0, 0, 0.3)'; // Linha do zero mais visível
            }
            return 'rgba(0, 0, 0, 0.1)'; // Outras linhas mais suaves
          },
          lineWidth: (context: any) => {
            // Linha do zero mais grossa
            if (context.tick.value === 0) {
              return 2;
            }
            return 1;
          }
        },
        zeroLineColor: 'rgba(0, 0, 0, 0.4)',
        zeroLineWidth: 2
      }
    }
  };

  return (
    <div className="mb-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <div style={{ height: '400px' }}>
          <Line data={chartData} options={options} />
        </div>
        
        {/* Indicadores agrupados abaixo do gráfico */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-sm font-semibold text-gray-700 mb-4">Resumo dos Saldos</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <p className="text-xs text-gray-500 mb-1">Saldo Realizado</p>
                <p className="text-sm text-gray-600 mb-2">até {new Date().toLocaleDateString('pt-BR')}</p>
                <p className={`text-2xl font-bold ${data.totals.realized >= 0 ? 'text-blue-600' : 'text-red-600'}`}>
                  {formatCurrency(data.totals.realized)}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500 mb-1">Saldo Previsto</p>
                <p className="text-sm text-gray-600 mb-2">próximos 30 dias</p>
                <p className={`text-2xl font-bold ${data.totals.forecast >= 0 ? 'text-blue-600' : 'text-red-600'}`}>
                  {formatCurrency(data.totals.forecast)}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500 mb-1">Diferença</p>
                <p className="text-sm text-gray-600 mb-2">previsto - realizado</p>
                <p className={`text-2xl font-bold ${data.totals.difference >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatCurrency(data.totals.difference)}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ForecastVsRealizedChart;







