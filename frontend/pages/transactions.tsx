import React from 'react';
import Layout from '../components/layout/Layout';
import Card from '../components/ui/Card';

export default function Transactions() {
  return (
    <Layout title="Transações">
      <div className="space-y-6">
        <Card>
          <Card.Header>
            <h2 className="text-xl font-semibold">Transações</h2>
          </Card.Header>
          <Card.Body>
            <p className="text-gray-600">Gerencie e visualize suas transações aqui.</p>
          </Card.Body>
        </Card>
      </div>
    </Layout>
  );
}

