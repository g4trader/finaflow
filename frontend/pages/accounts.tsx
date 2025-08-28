import React from 'react';
import Layout from '../components/layout/Layout';
import Card from '../components/ui/Card';

export default function Contas() {
  return (
    <Layout title="Contas">
      <div className="space-y-6">
        <Card>
          <Card.Header>
            <h2 className="text-xl font-semibold">Contas</h2>
          </Card.Header>
          <Card.Body>
            <p className="text-gray-600">Gerenciamento de contas em breve.</p>
          </Card.Body>
        </Card>
      </div>
    </Layout>
  );
}

