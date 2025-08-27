import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import Reports from '../pages/reports';
import { AuthContext } from '../context/AuthContext';

jest.mock('../components/layout/Layout', () => ({ children }: any) => <div>{children}</div>);

jest.mock('recharts', () => ({
  BarChart: ({ children }: any) => <div data-testid="barchart">{children}</div>,
  Bar: () => <div />, 
  XAxis: () => <div />, 
  YAxis: () => <div />, 
  Tooltip: () => <div />, 
  ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
  Legend: () => <div />,
}));

jest.mock('../services/api', () => ({
  getCashFlowReport: jest.fn(),
}));

const api = require('../services/api');
const mockedGetReport = api.getCashFlowReport as jest.Mock;

describe('Reports page', () => {
  test('fetches and displays report data', async () => {
    mockedGetReport.mockResolvedValue([{ period: 'Jan', predicted: 100, realized: 80 }]);

    render(
      <AuthContext.Provider value={{ token: 'token123', role: null, tenantId: null, login: jest.fn(), signup: jest.fn(), logout: jest.fn() }}>
        <Reports />
      </AuthContext.Provider>
    );

    await waitFor(() => expect(mockedGetReport).toHaveBeenCalledWith('month', 'token123'));
    expect(screen.getByText('Previsto x Realizado')).toBeInTheDocument();
    expect(screen.getByTestId('barchart')).toBeInTheDocument();
  });
});
