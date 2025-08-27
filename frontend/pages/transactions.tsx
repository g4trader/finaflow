import React, { useState } from 'react';
import Layout from '../components/layout/Layout';

interface Transaction {
  id: string;
  accountId: string;
  amount: number;
  description: string;
  date: string;
}

export default function Transactions() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [form, setForm] = useState<Omit<Transaction, 'id'>>({
    accountId: '',
    amount: 0,
    description: '',
    date: ''
  });
  const [editingId, setEditingId] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: name === 'amount' ? Number(value) : value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (editingId) {
      setTransactions(transactions.map(t => t.id === editingId ? { id: editingId, ...form } : t));
      setEditingId(null);
    } else {
      const id = Date.now().toString();
      setTransactions([...transactions, { id, ...form }]);
    }
    setForm({ accountId: '', amount: 0, description: '', date: '' });
  };

  const handleEdit = (id: string) => {
    const tx = transactions.find(t => t.id === id);
    if (tx) {
      setForm({ accountId: tx.accountId, amount: tx.amount, description: tx.description, date: tx.date });
      setEditingId(id);
    }
  };

  return (
    <Layout>
      <div className="max-w-2xl mx-auto p-4">
        <h1 className="text-2xl font-bold mb-4">Transactions</h1>
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
          <input
            type="date"
            name="date"
            value={form.date}
            onChange={handleChange}
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
              <th className="border p-2">Amount</th>
              <th className="border p-2">Description</th>
              <th className="border p-2">Date</th>
              <th className="border p-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map(tx => (
              <tr key={tx.id}>
                <td className="border p-2">{tx.accountId}</td>
                <td className="border p-2">{tx.amount}</td>
                <td className="border p-2">{tx.description}</td>
                <td className="border p-2">{tx.date}</td>
                <td className="border p-2">
                  <button
                    onClick={() => handleEdit(tx.id)}
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
