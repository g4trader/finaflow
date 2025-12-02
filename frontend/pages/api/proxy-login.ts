import type { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'https://finaflow-backend-staging-642830139828.us-central1.run.app';

  try {
    // Validar body
    if (!req.body) {
      return res.status(400).json({ error: 'Body é obrigatório' });
    }
    
    const { username, password } = req.body;
    
    // Validar campos obrigatórios
    if (!username || !password) {
      return res.status(400).json({ error: 'Username e password são obrigatórios' });
    }

    // Fazer requisição para o backend
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    // Criar AbortController para timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 25000);

    const response = await fetch(`${BACKEND_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString(),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    // Verificar se a resposta é JSON
    const contentType = response.headers.get('content-type');
    let data;
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      const text = await response.text();
      return res.status(500).json({ 
        error: 'Resposta inválida do backend', 
        detail: text.substring(0, 200) 
      });
    }

    if (!response.ok) {
      return res.status(response.status).json(data);
    }

    return res.status(200).json(data);
  } catch (error: any) {
    console.error('Erro no proxy login:', error);
    
    // Verificar se foi timeout
    if (error.name === 'AbortError' || error.message?.includes('aborted')) {
      return res.status(504).json({ 
        error: 'Timeout ao conectar ao backend',
        detail: 'A requisição demorou mais de 25 segundos'
      });
    }
    
    const errorMessage = error?.message || 'Erro desconhecido';
    const errorDetail = error?.response?.data || error?.detail || errorMessage;
    return res.status(500).json({ 
      error: 'Erro ao conectar ao backend', 
      detail: typeof errorDetail === 'string' ? errorDetail : JSON.stringify(errorDetail)
    });
  }
}


