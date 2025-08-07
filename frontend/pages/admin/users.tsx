import React, { useContext, useState } from 'react';
import api from '../../services/api';
import { AuthContext } from '../../context/AuthContext';

export default function UsersAdmin() {
  const { token } = useContext(AuthContext);
  const [data, setData] = useState({
    username: '',
    email: '',
    password: '',
    role: 'tenant_user',
    tenant_id: ''
  });
  const [message, setMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/users', data, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMessage('Usuário criado com sucesso');
    } catch {
      setMessage('Erro ao criar usuário');
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-xl mb-4">Administração de Usuários</h1>
      <form onSubmit={handleSubmit} className="space-y-2">
        <input
          onChange={e => setData({ ...data, username: e.target.value })}
          placeholder="Username"
          className="border p-2 w-full"
        />
        <input
          onChange={e => setData({ ...data, email: e.target.value })}
          placeholder="Email"
          className="border p-2 w-full"
        />
        <input
          type="password"
          onChange={e => setData({ ...data, password: e.target.value })}
          placeholder="Password"
          className="border p-2 w-full"
        />
        <input
          onChange={e => setData({ ...data, tenant_id: e.target.value })}
          placeholder="Tenant ID"
          className="border p-2 w-full"
        />
        <button className="bg-green-500 text-white px-4 py-2">Criar Usuário</button>
      </form>
      {message && <p className="mt-4">{message}</p>}
    </div>
  );
}
