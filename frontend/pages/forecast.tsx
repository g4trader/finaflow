import React, { useState } from 'react';
import Layout from '../components/layout/Layout';

interface Forecast {
  id: string;
  accountId: string;
  expectedDate: string;
  amount: number;
  description: string;
}

export default function ForecastPage() {
  const [forecasts, setForecasts] = useState<Forecast[]>([]);
  const [form, setForm] = useState<Omit<Forecast, 'id'>>({
    accountId: '',
    expectedDate: '',
    amount: 0,
    description: ''
  });
  const [editingId, setEditingId] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: name === 'amount' ? Number(value) : value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (editingId) {
      setForecasts(forecasts.map(f => f.id === editingId ? { id: editingId, ...form } : f));
      setEditingId(null);
    } else {
      const id = Date.now().toString();
      setForecasts([...forecasts, { id, ...form }]);
    }
    setForm({ accountId: '', expectedDate: '', amount: 0, description: '' });
  };

  const handleEdit = (id: string) => {
    const fc = forecasts.find(f => f.id === id);
    if (fc) {
      setForm({ accountId: fc.accountId, expectedDate: fc.expectedDate, amount: fc.amount, description: fc.description });
      setEditingId(id);
    }
  };

  return (
    <Layout>
      <div className="max-w-2xl mx-auto p-4">
        <h1 className="text-2xl font-bold mb-4">Forecast</h1>
        <form onSubmit={handleSubmit} className="space-y-2 mb-6">
          <input
            type="text"
            name="accountId"
            value={form.accountId}
            onChange={handleChange}
            placeholder="Account ID"
            className="border p-2 w-full"
          />
          <input
            type="date"
            name="expectedDate"
            value={form.expectedDate}
            onChange={handleChange}
            className="border p-2 w-full"
          />
          <input
            type="number"
            name="amount"
            value={form.amount}
            onChange={handleChange}
            placeholder="Amount"
            className="border p-2 w-full"
          />
          <input
            type="text"
            name="description"
            value={form.description}
            onChange={handleChange}
            placeholder="Description"
            className="border p-2 w-full"
          />
          <button type="submit" className="bg-blue-600 text-white px-4 py-2">
            {editingId ? 'Update' : 'Add'}
          </button>
        </form>

        <table className="w-full border">
          <thead>
            <tr className="bg-gray-100">
              <th className="border p-2">Account</th>
              <th className="border p-2">Date</th>
              <th className="border p-2">Amount</th>
              <th className="border p-2">Description</th>
              <th className="border p-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {forecasts.map(fc => (
              <tr key={fc.id}>
                <td className="border p-2">{fc.accountId}</td>
                <td className="border p-2">{fc.expectedDate}</td>
                <td className="border p-2">{fc.amount}</td>
                <td className="border p-2">{fc.description}</td>
                <td className="border p-2">
                  <button
                    onClick={() => handleEdit(fc.id)}
                    className="text-blue-600 hover:underline mr-2"
                  >
                    Edit
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Layout>
  );
}
