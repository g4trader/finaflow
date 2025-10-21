import { useState, useEffect, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import type { YearFilterState } from '../../types/dashboard';

export const useYearFilter = (): YearFilterState => {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // Estado do ano - default para ano atual
  const [year, setYearState] = useState(() => {
    const currentYear = new Date().getFullYear();
    const urlYear = searchParams.get('year');
    return urlYear ? parseInt(urlYear, 10) : currentYear;
  });
  
  const [isLoading, setIsLoading] = useState(false);

  // Função para atualizar o ano
  const setYear = useCallback((newYear: number) => {
    setIsLoading(true);
    setYearState(newYear);
    
    // Atualizar URL com o novo ano
    const params = new URLSearchParams(searchParams.toString());
    params.set('year', newYear.toString());
    
    // Usar replace para não adicionar ao histórico
    router.replace(`/dashboard?${params.toString()}`, { scroll: false });
    
    // Simular loading (será removido quando implementarmos os fetches)
    setTimeout(() => setIsLoading(false), 300);
  }, [router, searchParams]);

  // Sincronizar com mudanças na URL
  useEffect(() => {
    const urlYear = searchParams.get('year');
    if (urlYear) {
      const parsedYear = parseInt(urlYear, 10);
      if (parsedYear !== year && !isNaN(parsedYear)) {
        setYearState(parsedYear);
      }
    }
  }, [searchParams, year]);

  return {
    year,
    setYear,
    isLoading
  };
};
