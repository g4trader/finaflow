import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Layout from '../components/layout/Layout';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Card from '../components/ui/Card';
import Modal from '../components/ui/Modal';
import { 
  getSampleSpreadsheetInfo, 
  validateGoogleSheetsData, 
  importFromGoogleSheets,
  getImportStatus 
} from '../services/api';

interface SpreadsheetInfo {
  spreadsheet_id: string;
  description: string;
  sheets: string[];
  instructions: string[];
}

interface ValidationResult {
  success: boolean;
  spreadsheet_id: string;
  spreadsheet_title?: string;
  sheets_found: string[];
  data_structure: {
    sheets_analysis: Array<{
      name: string;
      type: string;
      rows: number;
      columns: number;
      headers: string[];
    }>;
    total_sheets: number;
    supported_sheets: number;
  };
  validation_errors?: string[];
}

interface ImportResult {
  success: boolean;
  message: string;
  spreadsheet_id: string;
  spreadsheet_title?: string;
  sheets_processed?: string[];
  data_imported?: Record<string, number>;
  errors?: string[];
}

const GoogleSheetsImport: React.FC = () => {
  const router = useRouter();
  const [spreadsheetId, setSpreadsheetId] = useState('');
  const [sampleInfo, setSampleInfo] = useState<SpreadsheetInfo | null>(null);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [showValidationModal, setShowValidationModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [importType, setImportType] = useState('all');

  useEffect(() => {
    loadSampleInfo();
  }, []);

  const loadSampleInfo = async () => {
    try {
      const info = await getSampleSpreadsheetInfo();
      setSampleInfo(info);
      setSpreadsheetId(info.spreadsheet_id); // Preencher com o ID da planilha de exemplo
    } catch (error) {
      console.error('Erro ao carregar informações da planilha de exemplo:', error);
    }
  };

  const handleValidate = async () => {
    if (!spreadsheetId.trim()) {
      alert('Por favor, insira o ID da planilha');
      return;
    }

    setLoading(true);
    try {
      const result = await validateGoogleSheetsData(spreadsheetId);
      setValidationResult(result);
      setShowValidationModal(true);
    } catch (error: any) {
      console.error('Erro na validação:', error);
      alert('Erro na validação: ' + (error.message || 'Erro desconhecido'));
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async (validateOnly = false) => {
    if (!spreadsheetId.trim()) {
      alert('Por favor, insira o ID da planilha');
      return;
    }

    setLoading(true);
    try {
      const result = await importFromGoogleSheets({
        spreadsheet_id: spreadsheetId,
        import_type: importType,
        validate_only: validateOnly
      });
      setImportResult(result);
      setShowImportModal(true);
    } catch (error: any) {
      console.error('Erro na importação:', error);
      alert('Erro na importação: ' + (error.message || 'Erro desconhecido'));
    } finally {
      setLoading(false);
    }
  };

  const copySpreadsheetId = (id: string) => {
    navigator.clipboard.writeText(id);
    alert('ID copiado para a área de transferência!');
  };

  return (
    <Layout>
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              📊 Importação Google Sheets
            </h1>
            <p className="text-gray-600">
              Importe dados da metodologia Ana Paula diretamente do Google Sheets
            </p>
          </div>

          {/* Informações da Planilha de Exemplo */}
          {sampleInfo && (
            <Card className="mb-8">
              <h2 className="text-xl font-semibold mb-4">📋 Planilha de Exemplo</h2>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    ID da Planilha:
                  </label>
                  <div className="flex items-center space-x-2">
                    <Input
                      value={sampleInfo.spreadsheet_id}
                      readOnly
                      className="flex-1"
                    />
                    <Button
                      onClick={() => copySpreadsheetId(sampleInfo.spreadsheet_id)}
                      variant="secondary"
                      size="sm"
                    >
                      Copiar
                    </Button>
                  </div>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-2">
                    <strong>Descrição:</strong> {sampleInfo.description}
                  </p>
                  <p className="text-sm text-gray-600 mb-2">
                    <strong>Total de abas:</strong> {sampleInfo.sheets.length}
                  </p>
                  <div className="mb-3">
                    <p className="text-sm font-medium text-gray-700 mb-1">Abas disponíveis:</p>
                    <div className="flex flex-wrap gap-2">
                      {sampleInfo.sheets.slice(0, 8).map((sheet, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded"
                        >
                          {sheet}
                        </span>
                      ))}
                      {sampleInfo.sheets.length > 8 && (
                        <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                          +{sampleInfo.sheets.length - 8} mais
                        </span>
                      )}
                    </div>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-1">Instruções:</p>
                    <ul className="text-sm text-gray-600 space-y-1">
                      {sampleInfo.instructions.map((instruction, index) => (
                        <li key={index} className="flex items-start">
                          <span className="mr-2">•</span>
                          <span>{instruction}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            </Card>
          )}

          {/* Formulário de Importação */}
          <Card className="mb-8">
            <h2 className="text-xl font-semibold mb-4">🚀 Importar Dados</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ID da Planilha Google Sheets:
                </label>
                <Input
                  value={spreadsheetId}
                  onChange={(e) => setSpreadsheetId(e.target.value)}
                  placeholder="Cole aqui o ID da planilha (ex: 1yyHuP6qjnK2Rd26yPPzaOqi_OJVeRjAJnewRIOJvFVY)"
                  className="w-full"
                />
                <p className="text-xs text-gray-500 mt-1">
                  O ID pode ser encontrado na URL da planilha: docs.google.com/spreadsheets/d/[ID]/edit
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tipo de Importação:
                </label>
                <select
                  value={importType}
                  onChange={(e) => setImportType(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">Todos os dados</option>
                  <option value="accounts">Apenas estrutura de contas</option>
                  <option value="transactions">Apenas transações</option>
                  <option value="reports">Apenas relatórios</option>
                </select>
              </div>

              <div className="flex space-x-4">
                <Button
                  onClick={handleValidate}
                  loading={loading}
                  variant="secondary"
                  className="flex-1"
                >
                  🔍 Validar Planilha
                </Button>
                <Button
                  onClick={() => handleImport(true)}
                  loading={loading}
                  variant="secondary"
                  className="flex-1"
                >
                  ✅ Validar Importação
                </Button>
                <Button
                  onClick={() => handleImport(false)}
                  loading={loading}
                  className="flex-1"
                >
                  📥 Importar Dados
                </Button>
              </div>
            </div>
          </Card>

          {/* Resultados */}
          {(validationResult || importResult) && (
            <Card>
              <h2 className="text-xl font-semibold mb-4">📊 Resultados</h2>
              {validationResult && (
                <div className="mb-6">
                  <h3 className="text-lg font-medium mb-2">Validação da Planilha</h3>
                  <div className={`p-4 rounded-lg ${validationResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                    <div className="flex items-center mb-2">
                      <span className={`text-2xl mr-2 ${validationResult.success ? 'text-green-600' : 'text-red-600'}`}>
                        {validationResult.success ? '✅' : '❌'}
                      </span>
                      <span className={`font-medium ${validationResult.success ? 'text-green-800' : 'text-red-800'}`}>
                        {validationResult.success ? 'Validação bem-sucedida' : 'Erros encontrados na validação'}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">
                      <strong>Título:</strong> {validationResult.spreadsheet_title || 'N/A'}
                    </p>
                    <p className="text-sm text-gray-600 mb-2">
                      <strong>Abas encontradas:</strong> {validationResult.sheets_found.length}
                    </p>
                    <p className="text-sm text-gray-600 mb-2">
                      <strong>Abas suportadas:</strong> {validationResult.data_structure.supported_sheets}
                    </p>
                    {validationResult.validation_errors && validationResult.validation_errors.length > 0 && (
                      <div className="mt-3">
                        <p className="text-sm font-medium text-red-800 mb-1">Erros encontrados:</p>
                        <ul className="text-sm text-red-700 space-y-1">
                          {validationResult.validation_errors.map((error, index) => (
                            <li key={index}>• {error}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {importResult && (
                <div>
                  <h3 className="text-lg font-medium mb-2">Resultado da Importação</h3>
                  <div className={`p-4 rounded-lg ${importResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                    <div className="flex items-center mb-2">
                      <span className={`text-2xl mr-2 ${importResult.success ? 'text-green-600' : 'text-red-600'}`}>
                        {importResult.success ? '✅' : '❌'}
                      </span>
                      <span className={`font-medium ${importResult.success ? 'text-green-800' : 'text-red-800'}`}>
                        {importResult.message}
                      </span>
                    </div>
                    {importResult.data_imported && Object.keys(importResult.data_imported).length > 0 && (
                      <div className="mt-3">
                        <p className="text-sm font-medium text-gray-800 mb-1">Dados importados:</p>
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          {Object.entries(importResult.data_imported).map(([key, value]) => (
                            <div key={key} className="flex justify-between">
                              <span className="text-gray-600">{key}:</span>
                              <span className="font-medium text-green-600">{value}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {importResult.errors && importResult.errors.length > 0 && (
                      <div className="mt-3">
                        <p className="text-sm font-medium text-red-800 mb-1">Erros:</p>
                        <ul className="text-sm text-red-700 space-y-1">
                          {importResult.errors.map((error, index) => (
                            <li key={index}>• {error}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </Card>
          )}
        </div>
      </div>

      {/* Modal de Validação Detalhada */}
      {showValidationModal && validationResult && (
        <Modal
          isOpen={showValidationModal}
          onClose={() => setShowValidationModal(false)}
          title="Detalhes da Validação"
          size="xl"
        >
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Informações Gerais</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Título:</span>
                    <span className="font-medium">{validationResult.spreadsheet_title || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total de abas:</span>
                    <span className="font-medium">{validationResult.sheets_found.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Abas suportadas:</span>
                    <span className="font-medium text-green-600">{validationResult.data_structure.supported_sheets}</span>
                  </div>
                </div>
              </div>
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Status</h4>
                <div className={`p-3 rounded-lg ${validationResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                  <div className="flex items-center">
                    <span className={`text-xl mr-2 ${validationResult.success ? 'text-green-600' : 'text-red-600'}`}>
                      {validationResult.success ? '✅' : '❌'}
                    </span>
                    <span className={`font-medium ${validationResult.success ? 'text-green-800' : 'text-red-800'}`}>
                      {validationResult.success ? 'Pronto para importação' : 'Requer atenção'}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <h4 className="font-medium text-gray-900 mb-2">Análise das Abas</h4>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {validationResult.data_structure.sheets_analysis.map((sheet, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-gray-900">{sheet.name}</span>
                      <span className={`px-2 py-1 text-xs rounded ${
                        sheet.type === 'unknown' 
                          ? 'bg-gray-100 text-gray-600' 
                          : 'bg-blue-100 text-blue-800'
                      }`}>
                        {sheet.type}
                      </span>
                    </div>
                    <div className="text-sm text-gray-600 space-y-1">
                      <div>Linhas: {sheet.rows} | Colunas: {sheet.columns}</div>
                      {sheet.headers.length > 0 && (
                        <div>
                          <span className="font-medium">Cabeçalhos:</span> {sheet.headers.slice(0, 5).join(', ')}
                          {sheet.headers.length > 5 && '...'}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Modal>
      )}
    </Layout>
  );
};

export default GoogleSheetsImport;
