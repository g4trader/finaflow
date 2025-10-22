import { NextApiRequest, NextApiResponse } from 'next';
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'POST') {
    try {
      const authHeader = req.headers.authorization;
      
      if (!authHeader) {
        return res.status(401).json({ detail: 'Token de autorização não fornecido' });
      }

      const { business_unit_id } = req.body;

      if (!business_unit_id) {
        return res.status(400).json({ detail: 'business_unit_id é obrigatório' });
      }

      console.log('🔍 [Proxy Select] Tentando selecionar BU:', business_unit_id);
      console.log('🔍 [Proxy Select] API URL:', API_BASE_URL);

      const backendResponse = await axios.post(
        `${API_BASE_URL}/api/v1/auth/select-business-unit`,
        { business_unit_id },
        {
          headers: {
            'Authorization': authHeader,
            'Content-Type': 'application/json',
          },
        }
      );

      console.log('✅ [Proxy Select] Sucesso:', backendResponse.status);
      res.status(backendResponse.status).json(backendResponse.data);
    } catch (error: any) {
      console.error('❌ [Proxy Select] Erro:', error.response?.status, error.response?.data || error.message);
      res.status(error.response?.status || 500).json(error.response?.data || { detail: 'Internal Server Error' });
    }
  } else {
    res.setHeader('Allow', ['POST']);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}



