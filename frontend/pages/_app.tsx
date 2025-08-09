import '../styles/globals.css';
import { AuthProvider } from '../context/AuthContext';
import Head from 'next/head';

const FIXED_TITLE = 'finaFlow — Gestão financeira clara e em tempo real';
const FIXED_DESC =
  'finaFlow é o sistema SaaS para previsão, realizado e fluxo de caixa com visual moderno e multi-empresa.';

export default function MyApp({ Component, pageProps }) {
  return (
    <AuthProvider>
      {/* Render da página */}
      <Component {...pageProps} />

      {/* Head GLOBAL (vem por último para prevalecer em qualquer tela) */}
      <Head>
        <title>{FIXED_TITLE}</title>
        <meta name="description" content={FIXED_DESC} />
        <meta property="og:title" content={FIXED_TITLE} />
        <meta property="og:description" content={FIXED_DESC} />
        <meta name="application-name" content="finaFlow" />
      </Head>
    </AuthProvider>
  );
}
