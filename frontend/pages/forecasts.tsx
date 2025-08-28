import React from 'react';
import Layout from '../components/layout/Layout';
import Card from '../components/ui/Card';

export default function Previsoes() {
  return (
    <Layout title="Previsões">
      <div className="space-y-6">
        <Card>
          <Card.Header>
            <h2 className="text-xl font-semibold">Previsões</h2>
          </Card.Header>
          <Card.Body>
            <p className="text-gray-600">As análises de previsões aparecerão aqui.</p>
          </Card.Body>
        </Card>
      </div>
    </Layout>
  );
}

