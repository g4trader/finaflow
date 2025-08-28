import React, { useContext } from 'react';
import { render, act } from '@testing-library/react';
import { AuthProvider, AuthContext } from '../context/AuthContext';

jest.mock('../services/api', () => ({
  login: jest.fn(),
  signup: jest.fn(),
}));

jest.mock('jwt-decode', () => jest.fn());

const api = require('../services/api');
const mockedLogin = api.login as jest.Mock;
const mockedSignup = api.signup as jest.Mock;
const mockedJwtDecode = require('jwt-decode') as jest.Mock;

describe('AuthContext', () => {
  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });

  test('login stores token and user info', async () => {
    mockedLogin.mockResolvedValue({ access_token: 'token123' });
    mockedJwtDecode.mockReturnValue({ role: 'admin', tenant_id: 'tenant1' });

    let ctx: any;
    const Consumer = () => {
      ctx = useContext(AuthContext);
      return null;
    };
    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>
    );

    await act(async () => {
      await ctx.login('user', 'pass');
    });

    expect(mockedLogin).toHaveBeenCalledWith('user', 'pass');
    expect(localStorage.getItem('token')).toBe('token123');
    expect(ctx.role).toBe('admin');
    expect(ctx.tenantId).toBe('tenant1');
  });

  test('logout clears token and user info', () => {
    localStorage.setItem('token', 'abc');

    let ctx: any;
    const Consumer = () => {
      ctx = useContext(AuthContext);
      return null;
    };
    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>
    );

    act(() => {
      ctx.logout();
    });

    expect(localStorage.getItem('token')).toBeNull();
    expect(ctx.token).toBeNull();
    expect(ctx.role).toBeNull();
    expect(ctx.tenantId).toBeNull();
  });

  test('signup works without token', async () => {
    mockedSignup.mockResolvedValue({});

    let ctx: any;
    const Consumer = () => {
      ctx = useContext(AuthContext);
      return null;
    };
    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>
    );

    await act(async () => {
      await ctx.signup({ username: 'new', password: 'pass' });
    });

    expect(mockedSignup).toHaveBeenCalledWith(
      { username: 'new', password: 'pass' },
      undefined
    );
  });

  test('signup uses token when available', async () => {
    mockedLogin.mockResolvedValue({ access_token: 'token123' });
    mockedJwtDecode.mockReturnValue({ role: 'user', tenant_id: null });
    mockedSignup.mockResolvedValue({});

    let ctx: any;
    const Consumer = () => {
      ctx = useContext(AuthContext);
      return null;
    };
    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>
    );

    await act(async () => {
      await ctx.login('user', 'pass');
    });

    await act(async () => {
      await ctx.signup({ username: 'new', password: 'pass' });
    });

    expect(mockedSignup).toHaveBeenCalledWith(
      { username: 'new', password: 'pass' },
      'token123'
    );
  });
});
