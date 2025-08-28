'use client';
// Page for uploading CSV files into backend tables
import React, { useState, useContext } from 'react';
import Layout from '../components/layout/Layout';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import { importCsv } from '../services/api';
import { AuthContext } from '../context/AuthContext';

export default function ImportCsvPage() {
  const { token } = useContext(AuthContext);
  const [file, setFile] = useState<File | null>(null);
  const [table, setTable] = useState('PlanOfAccounts');
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setSuccess('');
    setError('');
    try {
      await importCsv(file, table, token ?? undefined);
      setSuccess('Importação realizada com sucesso.');
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? 'Erro ao importar CSV.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout title="Importar CSV">
      <Card>
        <Card.Body>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Arquivo CSV
              </label>
              <input
                type="file"
                accept=".csv"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="block w-full text-sm text-gray-700 border border-gray-300 rounded-lg cursor-pointer focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tabela
              </label>
              <select
                value={table}
                onChange={(e) => setTable(e.target.value)}
                className="input"
              >
                <option value="PlanOfAccounts">PlanOfAccounts</option>
                <option value="Transactions">Transactions</option>
                <option value="Forecasts">Forecasts</option>
              </select>
            </div>
            <Button type="submit" variant="primary" loading={loading} disabled={!file}>
              Importar
            </Button>
          </form>
          {success && <p className="text-green-600 mt-4">{success}</p>}
          {error && <p className="text-red-600 mt-4">{error}</p>}
        </Card.Body>
      </Card>
    </Layout>
  );
}
