import React, { useContext, useEffect, useState } from 'react';
import Layout from '../components/layout/Layout';
import Card from '../components/ui/Card';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { AuthContext } from '../context/AuthContext';
import { getCashFlowReport } from '../services/api'
import ProtectedRoute from '../components/ProtectedRoute';;

interface ReportItem {
  period: string;
  predicted: number;
  realized: number;
}

function ReportsContent() {
  const { token } = useContext(AuthContext);
  const [data, setData] = useState<ReportItem[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const results = await getCashFlowReport('month', token || undefined);
        setData(results);
      } catch (error) {
        console.error('Failed to fetch report', error);
      }
    };
    if (token) {
      fetchData();
    }
  }, [token]);

  return (
    <Layout title="Relatórios">
      <div className="space-y-6">
        <Card>
          <Card.Header>
            <h2 className="text-xl font-semibold">Previsto x Realizado</h2>
          </Card.Header>
          <Card.Body>
            <div className="w-full h-96">
              <ResponsiveContainer>
                <BarChart data={data}>
                  <XAxis dataKey="period" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="predicted" fill="#3B82F6" name="Previsto" />
                  <Bar dataKey="realized" fill="#10B981" name="Realizado" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card.Body>
        </Card>
      </div>
    </Layout>
  );
}

export default function Reports() {
  return (
    <ProtectedRoute>
      <ReportsContent />
    </ProtectedRoute>
  );
}
