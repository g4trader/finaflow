import React from 'react';
import Layout from '../components/layout/Layout';
import Card from '../components/ui/Card';

export default function Forecasts() {
  return (
    <Layout title="Forecasts">
      <div className="space-y-6">
        <Card>
          <Card.Header>
            <h2 className="text-xl font-semibold">Forecasts</h2>
          </Card.Header>
          <Card.Body>
            <p className="text-gray-600">Forecast analytics will appear here.</p>
          </Card.Body>
        </Card>
      </div>
    </Layout>
  );
}

