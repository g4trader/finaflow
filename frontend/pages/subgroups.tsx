import React from 'react';
import Layout from '../components/layout/Layout';
import Card from '../components/ui/Card';

export default function Subgrupos() {
  return (
    <Layout title="Subgrupos">
      <div className="space-y-6">
        <Card>
          <Card.Header>
            <h2 className="text-xl font-semibold">Subgrupos</h2>
          </Card.Header>
          <Card.Body>
            <p className="text-gray-600">Organize seus subgrupos aqui.</p>
          </Card.Body>
        </Card>
      </div>
    </Layout>
  );
}

