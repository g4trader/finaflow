import { NextApiRequest, NextApiResponse } from 'next';
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
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
        }
      );

      res.status(backendResponse.status).json(backendResponse.data);
    } catch (error: any) {
      console.error('Proxy Business Units Error:', error.response?.data || error.message);
      res.status(error.response?.status || 500).json(error.response?.data || { detail: 'Internal Server Error' });
    }
  } else {
    res.setHeader('Allow', ['GET']);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}


