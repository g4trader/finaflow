// Utilitário para importação dinâmica do api, evitando SSR
export const getApi = async () => {
  if (typeof window === 'undefined') {
    throw new Error('API só pode ser usada no cliente');
  }
  const apiModule = await import('../services/api');
  return apiModule.default;
};

