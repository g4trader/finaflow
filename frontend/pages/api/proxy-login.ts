import type { NextApiRequest, NextApiResponse } from 'next';

// Configurar body parser
export const config = {
  api: {
    bodyParser: {
      sizeLimit: '1mb',
    },
  },
};

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  console.log('🔍 [Proxy Login] Iniciando handler');
  console.log('🔍 [Proxy Login] Method:', req.method);
  console.log('🔍 [Proxy Login] Headers:', JSON.stringify(req.headers));
  console.log('🔍 [Proxy Login] Body type:', typeof req.body);
  console.log('🔍 [Proxy Login] Body:', JSON.stringify(req.body));
  
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'https://finaflow-backend-staging-556803510516.us-central1.run.app';
  console.log('🔍 [Proxy Login] BACKEND_URL:', BACKEND_URL);

  try {
    // Tentar parsear body se necessário
    let body = req.body;
    
    // Se o body é uma string, tentar parsear como JSON
    if (typeof body === 'string') {
      try {
        body = JSON.parse(body);
      } catch (e) {
        console.error('❌ [Proxy Login] Erro ao parsear body como JSON:', e);
      }
    }
    
    // Validar body
    if (!body || (typeof body === 'object' && Object.keys(body).length === 0)) {
      console.error('❌ [Proxy Login] Body vazio ou inválido');
      return res.status(400).json({ error: 'Body é obrigatório' });
    }
    
    const { username, password } = body;
    console.log('🔍 [Proxy Login] Username:', username ? `"${username}"` : 'não fornecido');
    console.log('🔍 [Proxy Login] Password:', password ? '***fornecido***' : 'não fornecido');
    
    // Validar campos obrigatórios
    if (!username || !password) {
      console.error('❌ [Proxy Login] Username ou password faltando');
      console.error('❌ [Proxy Login] Body completo:', JSON.stringify(body));
      return res.status(400).json({ error: 'Username e password são obrigatórios' });
    }

    // Fazer requisição para o backend
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    console.log('🔍 [Proxy Login] Fazendo requisição para:', `${BACKEND_URL}/api/v1/auth/login`);

    // Criar AbortController para timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 25000);

    let response;
    try {
      response = await fetch(`${BACKEND_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString(),
        signal: controller.signal,
      });
      console.log('🔍 [Proxy Login] Resposta recebida, status:', response.status);
    } finally {
      clearTimeout(timeoutId);
    }

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
      console.error('❌ [Proxy Login] Resposta não OK:', response.status, data);
      return res.status(response.status).json(data);
    }

    console.log('✅ [Proxy Login] Sucesso');
    return res.status(200).json(data);
  } catch (error: any) {
    console.error('❌ [Proxy Login] Erro capturado:', error);
    console.error('❌ [Proxy Login] Error name:', error?.name);
    console.error('❌ [Proxy Login] Error message:', error?.message);
    console.error('❌ [Proxy Login] Error stack:', error?.stack);
    
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


