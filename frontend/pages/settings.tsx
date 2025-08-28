"use client";
import React, { useContext, useState } from 'react';
import jwtDecode from 'jwt-decode';

import Layout from '../components/layout/Layout';
import Card from '../components/ui/Card';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import { AuthContext } from '../context/AuthContext';
import { updateUser, updateTenant } from '../services/api';

export default function Settings() {
  const { token, tenantId } = useContext(AuthContext);
  const userId = token ? (jwtDecode<{ sub: string }>(token).sub) : null;

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [tenantName, setTenantName] = useState('');

  const [emailMsg, setEmailMsg] = useState('');
  const [emailError, setEmailError] = useState('');
  const [passwordMsg, setPasswordMsg] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [tenantMsg, setTenantMsg] = useState('');
  const [tenantError, setTenantError] = useState('');

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setEmailMsg('');
    setEmailError('');
    try {
      if (!userId) throw new Error('user id missing');
      await updateUser(userId, { email }, token ?? undefined);
      setEmailMsg('Email atualizado com sucesso.');
      setEmail('');
    } catch (err) {
      setEmailError('Erro ao atualizar email.');
    }
  };

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordMsg('');
    setPasswordError('');
    try {
      if (!userId) throw new Error('user id missing');
      await updateUser(userId, { password }, token ?? undefined);
      setPasswordMsg('Senha atualizada com sucesso.');
      setPassword('');
    } catch (err) {
      setPasswordError('Erro ao atualizar senha.');
    }
  };

  const handleTenantSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setTenantMsg('');
    setTenantError('');
    try {
      if (!tenantId) throw new Error('tenant id missing');
      await updateTenant(tenantId, { name: tenantName }, token ?? undefined);
      setTenantMsg('Dados do tenant atualizados com sucesso.');
      setTenantName('');
    } catch (err) {
      setTenantError('Erro ao atualizar dados do tenant.');
    }
  };

  return (
    <Layout title="Configurações">
      <div className="space-y-6">
        <Card>
          <Card.Header>
            <h2 className="text-xl font-semibold">Configurações da Conta</h2>
          </Card.Header>
          <Card.Body className="space-y-8">
            <form onSubmit={handleEmailSubmit} className="space-y-4">
              <Input
                type="email"
                label="Novo Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                fullWidth
              />
              {emailMsg && <p className="text-sm text-green-600">{emailMsg}</p>}
              {emailError && <p className="text-sm text-red-600">{emailError}</p>}
              <Button type="submit">Atualizar Email</Button>
            </form>

            <form onSubmit={handlePasswordSubmit} className="space-y-4">
              <Input
                type="password"
                label="Nova Senha"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                fullWidth
              />
              {passwordMsg && <p className="text-sm text-green-600">{passwordMsg}</p>}
              {passwordError && <p className="text-sm text-red-600">{passwordError}</p>}
              <Button type="submit">Alterar Senha</Button>
            </form>

            <form onSubmit={handleTenantSubmit} className="space-y-4">
              <Input
                type="text"
                label="Nome do Tenant"
                value={tenantName}
                onChange={(e) => setTenantName(e.target.value)}
                fullWidth
              />
              {tenantMsg && <p className="text-sm text-green-600">{tenantMsg}</p>}
              {tenantError && <p className="text-sm text-red-600">{tenantError}</p>}
              <Button type="submit">Atualizar Tenant</Button>
            </form>
          </Card.Body>
        </Card>
      </div>
    </Layout>
  );
}

