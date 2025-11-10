import { useEffect } from 'react';
import { useRouter } from 'next/router';

export default function ExtratoContasBancariasRedirect() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/contas-bancarias');
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="rounded-lg bg-white p-6 text-center shadow-md">
        <p className="text-sm text-gray-600">Redirecionando para Contas Bancárias...</p>
      </div>
    </div>
  );
}

