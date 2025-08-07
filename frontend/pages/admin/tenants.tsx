import React, { useContext, useEffect, useState } from 'react';
import api from '../../services/api';
import { AuthContext } from '../../context/AuthContext';

export default function Tenants() {
  const { token } = useContext(AuthContext);
  const [tenants, setTenants] = useState<any[]>([]);
  const [name, setName] = useState('');
  const [parentTenantId, setParentTenantId] = useState('');

  useEffect(() => {
    const fetchTenants = async () => {
      const res = await api.get('/tenants', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTenants(res.data);
    };
    if (token) {
      fetchTenants();
    }
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await api.post('/tenants', { name, parent_tenant_id: parentTenantId }, {
      headers: { Authorization: `Bearer ${token}` }
    });
    setName('');
    setParentTenantId('');
    const res = await api.get('/tenants', {
      headers: { Authorization: `Bearer ${token}` }
    });
    setTenants(res.data);
  };

  return (
    <div className="p-6">
      <h1 className="text-xl mb-4">Administração de Tenants</h1>
      <form onSubmit={handleSubmit} className="mb-4">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Nome"
          className="border p-2 mr-2"
        />
        <input
          value={parentTenantId}
          onChange={(e) => setParentTenantId(e.target.value)}
          placeholder="Parent Tenant ID"
          className="border p-2 mr-2"
        />
        <button className="bg-blue-500 text-white px-4 py-2">Criar</button>
      </form>
      <ul>
        {tenants.map((t) => (
          <li key={t.id}>
            {t.name} ({t.id})
          </li>
        ))}
      </ul>
    </div>
  );
}
