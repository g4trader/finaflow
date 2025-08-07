import React, { useContext, useEffect, useState } from 'react';
import { AuthContext } from '../context/AuthContext';
import api from '../services/api';

export default function Home() {
  const { token, role } = useContext(AuthContext);
  const [message, setMessage] = useState('Carregando...');

  useEffect(() => {
    if (token) {
      setMessage(`Autenticado como ${role}`);
    } else {
      setMessage('Por favor, faça login.');
    }
  }, [token, role]);

  return (
    <div className="flex flex-col items-center justify-center h-screen">
      <h1 className="text-2xl mb-4">Bem-vindo ao FinaFlow</h1>
      <p className="mb-4">{message}</p>
      {!token && (
        <a href="/login" className="text-blue-500 underline">
          Fazer Login
        </a>
      )}
      {token && (
        <div className="space-x-4">
          {role === 'super_admin' && (
            <a href="/admin/tenants" className="text-blue-500 underline">
              Gestão de Tenants
            </a>
          )}
          <a href="/groups" className="text-blue-500 underline">
            Ir para Grupos
          </a>
        </div>
      )}
    </div>
  );
}
