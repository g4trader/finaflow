import React from 'react';
import Layout from '../components/layout/Layout';
import Card from '../components/ui/Card';

export default function Settings() {
  return (
    <Layout title="Configurações">
      <div className="space-y-6">
        <Card>
          <Card.Header>
            <h2 className="text-xl font-semibold">Configurações</h2>
          </Card.Header>
          <Card.Body>
            <p className="text-gray-600">Ajuste as preferências da sua conta.</p>
          </Card.Body>
        </Card>
      </div>
    </Layout>
  );
}

