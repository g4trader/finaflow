import { NextApiRequest, NextApiResponse } from 'next';
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://finaflow-backend-staging-642830139828.us-central1.run.app';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  // Configurar timeout
  res.setTimeout(30000); // 30 segundos
  
  if (req.method === 'GET') {
    try {
      const authHeader = req.headers.authorization;
      
      if (!authHeader) {
        return res.status(401).json({ detail: 'Token de autorização não fornecido' });
      }

      const backendResponse = await axios.get(
        `${API_BASE_URL}/api/v1/auth/user-business-units`,
        {
          headers: {
            'Authorization': authHeader,
            'Content-Type': 'application/json',
          },
          timeout: 25000, // Timeout de 25 segundos
        }
      );

      res.status(backendResponse.status).json(backendResponse.data);
    } catch (error: any) {
      console.error('Proxy Business Units Error:', error.response?.data || error.message);
      const statusCode = error.response?.status || 500;
      const errorData = error.response?.data || { detail: error.message || 'Internal Server Error' };
      return res.status(statusCode).json(errorData);
    }
  } else {
    res.setHeader('Allow', ['GET']);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}


