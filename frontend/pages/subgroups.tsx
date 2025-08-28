import React from 'react';
import Layout from '../components/layout/Layout';
import Card from '../components/ui/Card';

export default function Subgroups() {
  return (
    <Layout title="Subgroups">
      <div className="space-y-6">
        <Card>
          <Card.Header>
            <h2 className="text-xl font-semibold">Subgroups</h2>
          </Card.Header>
          <Card.Body>
            <p className="text-gray-600">Organize subgroups here.</p>
          </Card.Body>
        </Card>
      </div>
    </Layout>
  );
}

