import React, { useContext } from 'react';
import Link from 'next/link';
import { AuthContext } from '../context/AuthContext';

export default function Home() {
  const { token, role } = useContext(AuthContext);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
      <div className="bg-white shadow-lg rounded-xl p-8 w-full max-w-md text-center">
        <img src="/logo.png" alt="FinaFlow" className="h-10 mx-auto mb-6" />
        <h1 className="text-2xl font-semibold mb-2">Bem-vindo ao FinaFlow</h1>
        <p className="text-gray-500 mb-6">
          Gerencie previsões, realizado e performance em um só lugar.
        </p>

        {!token ? (
          <Link href="/login" className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-md inline-block">
            Fazer Login
          </Link>
        ) : (
          <div className="space-y-3">
            {role === 'super_admin' && (
              <Link href="/admin/tenants" className="block text-blue-600 hover:underline">
                Área do Administrador
              </Link>
            )}
            <Link href="/dashboard" className="block text-blue-600 hover:underline">
              Ir para o Dashboard
            </Link>
          </div>
        )}

        <div className="mt-6 text-xs text-gray-400">
          <span>v0.1.0</span>
        </div>
      </div>
    </div>
  );
}
