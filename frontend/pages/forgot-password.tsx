'use client';
import React, { useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import axios from 'axios';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import { Mail } from 'lucide-react';

// Garantir HTTPS
const getApiUrl = () => {
  const url = process.env.NEXT_PUBLIC_API_URL;
  if (!url) {
    return 'https://finaflow-backend-609095880025.us-central1.run.app';
  }
  // Forçar HTTPS se for HTTP
  if (url.startsWith('http://')) {
    return url.replace('http://', 'https://');
  }
  return url;
};

const API_URL = getApiUrl();

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      setLoading(true);
      await axios.post(`${API_URL}/auth/forgot-password`, { email });
      setSent(true);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Não foi possível enviar as instruções.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>finaFlow — Recuperar senha</title>
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50 flex items-center justify-center p-6">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <img src="/logo-finaflow.svg" alt="finaFlow" className="h-10 mx-auto mb-4" />
            <h1 className="text-2xl font-semibold text-gray-900">Recuperar senha</h1>
            <p className="text-gray-600">Enviaremos um link para resetar sua senha.</p>
          </div>

          <div className="bg-white/80 backdrop-blur-sm border border-white/20 shadow-xl rounded-xl p-6">
            {sent ? (
              <div className="text-center">
                <p className="text-gray-700 mb-6">
                  Se <strong>{email}</strong> estiver cadastrado, você receberá um email com instruções em alguns minutos.
                </p>
                <Link href="/login" className="text-blue-600 hover:text-blue-700 font-medium">Voltar para o login</Link>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="relative">
                  <div className="pointer-events-none absolute inset-y-0 left-0 pl-3 flex items-center">
                    <Mail className="w-5 h-5 text-gray-400" />
                  </div>
                  <Input
                    type="email"
                    name="email"
                    label="Email"
                    placeholder="voce@empresa.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    fullWidth
                    className="pl-10"
                  />
                </div>

                {error && <p className="text-sm text-red-600">{error}</p>}

                <Button type="submit" size="lg" fullWidth loading={loading}>
                  Enviar instruções
                </Button>

                <p className="text-center text-sm text-gray-600">
                  Lembrou a senha?{' '}
                  <Link href="/login" className="text-blue-600 hover:text-blue-700 font-medium">Entrar</Link>
                </p>
              </form>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
