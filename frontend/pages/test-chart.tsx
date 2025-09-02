import React from 'react';

const TestChartPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          Teste - Plano de Contas
        </h1>
        
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            Esta é uma página de teste
          </h2>
          
          <p className="text-gray-600 mb-4">
            Se você consegue ver esta página, significa que o Next.js está funcionando corretamente.
          </p>
          
          <div className="bg-blue-50 border border-blue-200 rounded p-4">
            <p className="text-blue-800">
              ✅ Página de teste carregada com sucesso!
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TestChartPage;
