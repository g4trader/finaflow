import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useRouter } from 'next/router';

const CSVImport = () => {
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
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, '')}/csv/import/${importType}`, {
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
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, '')}/csv/template/${type}`, {
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
      }
    } catch (err) {
      setError('Erro ao baixar template');
    }
  };

  // Renderizar loading enquanto verifica autenticação
  if (!isClient || !token) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Carregando...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white shadow-lg rounded-lg p-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">Importação de Dados CSV</h1>

          {/* Tipo de Importação */}
          <div className="mb-6">
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
              <option value="plan-accounts">Plano de Contas</option>
            </select>
          </div>

          {/* Descrição do tipo selecionado */}
          <div className="mb-6 p-4 bg-blue-50 rounded-md">
            <h3 className="font-medium text-blue-900 mb-2">
              {importType === 'accounts' && 'Importação de Contas'}
              {importType === 'transactions' && 'Importação de Transações'}
              {importType === 'plan-accounts' && 'Importação do Plano de Contas'}
            </h3>
            <p className="text-blue-700 text-sm">
              {importType === 'accounts' && 'Importe contas com saldo inicial e subgrupo.'}
              {importType === 'transactions' && 'Importe transações financeiras com data, valor e descrição.'}
              {importType === 'plan-accounts' && 'Importe a estrutura completa do plano de contas (grupos, subgrupos e contas).'}
            </p>
          </div>

          {/* Download Template */}
          <div className="mb-6">
            <button
              onClick={() => downloadTemplate(importType)}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              📥 Baixar Template CSV
            </button>
          </div>

          {/* Upload de Arquivo */}
          <div className="mb-6">
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
            {selectedFile && (
              <p className="mt-2 text-sm text-gray-600">
                Arquivo selecionado: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(2)} KB)
              </p>
            )}
          </div>

          {/* Botão de Importação */}
          <div className="mb-6">
            <button
              onClick={handleImport}
              disabled={!selectedFile || loading}
              className={`w-full px-4 py-2 text-white font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
                !selectedFile || loading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {loading ? 'Importando...' : 'Importar Dados'}
            </button>
          </div>

          {/* Mensagens */}
          {message && (
            <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-md">
              <p className="text-green-800">{message}</p>
            </div>
          )}

          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          {/* Instruções */}
          <div className="mt-8 p-4 bg-gray-50 rounded-md">
            <h3 className="font-medium text-gray-900 mb-2">Instruções de Uso</h3>
            <ul className="text-sm text-gray-700 space-y-1">
              <li>• Certifique-se de que o arquivo CSV está no formato correto</li>
              <li>• Use o template fornecido como base para seu arquivo</li>
              <li>• Verifique se todos os campos obrigatórios estão preenchidos</li>
              <li>• Para valores monetários, use vírgula como separador decimal</li>
              <li>• Para datas, use o formato DD/MM/AAAA</li>
            </ul>
          </div>

          {/* Exemplos de Estrutura */}
          <div className="mt-6">
            <h3 className="font-medium text-gray-900 mb-2">Estrutura do CSV</h3>
            <div className="bg-gray-100 p-4 rounded-md overflow-x-auto">
              <pre className="text-sm text-gray-800">
                {importType === 'accounts' && `Conta,Subgrupo,Saldo,Descrição
Conta Corrente,Bancos,1000.00,Conta principal da empresa
Caixa,Caixa,500.00,Caixa da empresa`}
                {importType === 'transactions' && `Data Movimentação,Conta,Valor,Descrição
02/01/2025,Conta Corrente,100.00,Recebimento de cliente
03/01/2025,Caixa,-50.00,Compra de material`}
                {importType === 'plan-accounts' && `Conta,Subgrupo,Grupo,Escolha
Conta Corrente,Bancos,Ativo,Usar
Caixa,Caixa,Ativo,Usar
Vendas,Receitas,Receita,Usar`}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CSVImport;
