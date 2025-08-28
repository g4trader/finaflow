import React from 'react';
import Layout from '../components/layout/Layout';
import Card from '../components/ui/Card';

export default function Accounts() {
  return (
    <Layout title="Accounts">
      <div className="space-y-6">
        <Card>
          <Card.Header>
            <h2 className="text-xl font-semibold">Accounts</h2>
          </Card.Header>
          <Card.Body>
            <p className="text-gray-600">Accounts management coming soon.</p>
          </Card.Body>
        </Card>
      </div>
    </Layout>
  );
}

