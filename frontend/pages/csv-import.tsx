import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useRouter } from 'next/router';
import ProtectedRoute from '../components/ProtectedRoute';

const CSVImportContent = () => {
  const { token } = useAuth();
  const router = useRouter();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [importType, setImportType] = useState('accounts');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  // Verificar autenticação apenas no lado do cliente
  useEffect(() => {
    if (isClient && !token) {
      router.push('/login');
    }
  }, [isClient, token, router]);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.name.endsWith('.csv')) {
      setSelectedFile(file);
      setError('');
    } else {
      setError('Por favor, selecione um arquivo CSV válido');
      setSelectedFile(null);
    }
  };

  const handleImport = async () => {
    if (!selectedFile) {
      setError('Por favor, selecione um arquivo CSV');
      return;
    }

    setLoading(true);
    setError('');
    setMessage('');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      // Garantir HTTPS
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://finaflow-backend-609095880025.us-central1.run.app';
      const secureUrl = apiUrl.startsWith('http://') ? apiUrl.replace('http://', 'https://') : apiUrl;
      const response = await fetch(`${secureUrl.replace(/\/$/, '')}/csv/import/${importType}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setMessage(`Importação realizada com sucesso! ${data.imported_count || data.accounts_imported || 0} registros importados.`);
        setSelectedFile(null);
        // Limpar o input de arquivo
        const fileInput = document.getElementById('file-input') as HTMLInputElement;
        if (fileInput) fileInput.value = '';
      } else {
        setError(data.detail || data.message || 'Erro na importação');
      }
    } catch (err) {
      setError('Erro ao conectar com o servidor');
    } finally {
      setLoading(false);
    }
  };

  const downloadTemplate = async (type: string) => {
    try {
      // Garantir HTTPS
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://finaflow-backend-609095880025.us-central1.run.app';
      const secureUrl = apiUrl.startsWith('http://') ? apiUrl.replace('http://', 'https://') : apiUrl;
      const response = await fetch(`${secureUrl.replace(/\/$/, '')}/csv/template/${type}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        const blob = new Blob([data.template], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = data.filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        setError('Erro ao baixar template');
      }
    } catch (err) {
      setError('Erro ao baixar template');
    }
  };

  if (!isClient) {
    return <div>Carregando...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">Importar CSV</h1>
          
          <div className="space-y-6">
            {/* Tipo de Importação */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tipo de Importação
              </label>
              <select
                value={importType}
                onChange={(e) => setImportType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="accounts">Contas</option>
                <option value="transactions">Transações</option>
                <option value="groups">Grupos</option>
                <option value="subgroups">Subgrupos</option>
              </select>
            </div>

            {/* Download Template */}
            <div>
              <button
                type="button"
                onClick={() => downloadTemplate(importType)}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                Baixar Template
              </button>
            </div>

            {/* Upload Arquivo */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Selecionar Arquivo CSV
              </label>
              <input
                id="file-input"
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Mensagens */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <p className="text-red-800">{error}</p>
              </div>
            )}

            {message && (
              <div className="bg-green-50 border border-green-200 rounded-md p-4">
                <p className="text-green-800">{message}</p>
              </div>
            )}

            {/* Botão Importar */}
            <div>
              <button
                type="button"
                onClick={handleImport}
                disabled={!selectedFile || loading}
                className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Importando...' : 'Importar CSV'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default function CSVImport() {
  return (
    <ProtectedRoute>
      <CSVImportContent />
    </ProtectedRoute>
  );
}
