import React from 'react';
import Layout from '../components/layout/Layout';
import Card from '../components/ui/Card';

export default function Groups() {
  return (
    <Layout title="Groups">
      <div className="space-y-6">
        <Card>
          <Card.Header>
            <h2 className="text-xl font-semibold">Groups</h2>
          </Card.Header>
          <Card.Body>
            <p className="text-gray-600">Manage your groups here.</p>
          </Card.Body>
        </Card>
      </div>
    </Layout>
  );
}

