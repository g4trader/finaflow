import React from 'react';
import Layout from '../components/layout/Layout';
import Card from '../components/ui/Card';

export default function Grupos() {
  return (
    <Layout title="Grupos">
      <div className="space-y-6">
        <Card>
          <Card.Header>
            <h2 className="text-xl font-semibold">Grupos</h2>
          </Card.Header>
          <Card.Body>
            <p className="text-gray-600">Gerencie seus grupos aqui.</p>
          </Card.Body>
        </Card>
      </div>
    </Layout>
  );
}

