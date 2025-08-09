import React from 'react';
import Head from 'next/head';
import Link from 'next/link';

export default function Landing() {
  return (
    <>
      <Head>
        <title>FinaFlow — Gestão financeira clara e em tempo real</title>
        <meta name="description" content="FinaFlow é o sistema SaaS para previsão, realizado e fluxo de caixa com visual moderno e multi-empresa." />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      {/* Header */}
      <header className="sticky top-0 z-40 backdrop-blur bg-white/70 border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src="/logo-finaflow.svg" alt="FinaFlow" className="h-8 w-auto" />
          </div>
          <nav className="hidden md:flex items-center gap-6 text-sm text-gray-600">
            <a href="#features" className="hover:text-gray-900">Recursos</a>
            <a href="#pricing" className="hover:text-gray-900">Planos</a>
            <a href="#faq" className="hover:text-gray-900">FAQ</a>
          </nav>
          <div className="flex items-center gap-3">
            <Link href="/login" className="text-sm text-gray-600 hover:text-gray-900">Entrar</Link>
            <Link href="/login" className="hidden sm:inline-block bg-blue-600 hover:bg-blue-700 text-white text-sm px-4 py-2 rounded-md">Começar agora</Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="bg-gradient-to-b from-blue-50 to-white">
        <div className="max-w-7xl mx-auto px-6 py-20 text-center">
          <span className="inline-flex items-center gap-2 text-xs font-medium text-blue-700 bg-blue-100 px-3 py-1 rounded-full">
            Novo • Visual moderno e relatórios mais claros
          </span>
          <h1 className="mt-6 text-4xl md:text-6xl font-extrabold tracking-tight text-gray-900">
            Controle financeiro sem planilhas complicadas
          </h1>
          <p className="mt-5 text-lg md:text-xl text-gray-600 max-w-3xl mx-auto">
            O FinaFlow reúne <strong>Previsto</strong>, <strong>Realizado</strong> e <strong>Fluxo de Caixa</strong> em um só lugar.
            Multi-empresa, multi-usuário e pronto para crescer com você.
          </p>
          <div className="mt-8 flex items-center justify-center gap-3">
            <Link href="/login" className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium">
              Criar minha conta
            </Link>
            <a href="#features" className="px-6 py-3 rounded-lg font-medium border border-gray-300 text-gray-700 hover:bg-gray-50">
              Ver recursos
            </a>
          </div>
          <p className="mt-4 text-xs text-gray-500">Teste grátis por 14 dias • Sem cartão de crédito</p>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid md:grid-cols-3 gap-6">
            {[
              {title:'Dashboard de impacto',desc:'Indicadores de Previsto, Realizado, Performance e distribuição por grupo.'},
              {title:'Fluxo de Caixa inteligente',desc:'Projeções mensais e análise de variação com poucos cliques.'},
              {title:'Multi-empresa e BU',desc:'Separe empresas e unidades com permissões de acesso por perfil.'},
              {title:'BigQuery nativo',desc:'Armazenamento analítico e consultas rápidas em grande volume.'},
              {title:'Importação e conciliação',desc:'CSV/OFX e conciliação simplificada (roadmap).'},
              {title:'Segurança e auditoria',desc:'Permissões por usuário, logs e criptografia em trânsito.'},
            ].map((f, i) => (
              <div key={i} className="rounded-2xl border border-gray-100 p-6 shadow-sm hover:shadow-md transition">
                <div className="w-10 h-10 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center font-semibold mb-4">
                  {i+1}
                </div>
                <h3 className="text-lg font-semibold text-gray-900">{f.title}</h3>
                <p className="mt-2 text-gray-600">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-10">
            <h2 className="text-3xl md:text-4xl font-extrabold text-gray-900">Planos simples, claros e que escalam com você</h2>
            <p className="mt-3 text-gray-600">Cancele quando quiser. Todos os planos incluem dashboard, lançamentos e múltiplas empresas.</p>
          </div>
          <div className="grid md:grid-cols-4 gap-6">
            {/* Solo */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm flex flex-col">
              <h3 className="text-lg font-semibold text-gray-900">Solo</h3>
              <p className="text-sm text-gray-500">1 usuário</p>
              <div className="mt-4">
                <span className="text-3xl font-extrabold">R$ 129</span>
                <span className="text-gray-500">/mês</span>
              </div>
              <ul className="mt-4 space-y-2 text-sm text-gray-600 list-disc pl-5">
                <li>Dashboard e lançamentos</li>
                <li>1 empresa</li>
                <li>Suporte por email</li>
              </ul>
              <Link href="/login" className="mt-auto bg-blue-600 hover:bg-blue-700 text-white w-full text-center py-3 rounded-lg font-medium">
                Assinar Solo
              </Link>
            </div>

            {/* Team */}
            <div className="bg-white rounded-2xl border border-blue-300 p-6 shadow-md ring-1 ring-blue-100 flex flex-col">
              <h3 className="text-lg font-semibold text-gray-900">Team</h3>
              <p className="text-sm text-gray-500">até 5 usuários</p>
              <div className="mt-4">
                <span className="text-3xl font-extrabold">R$ 499</span>
                <span className="text-gray-500">/mês</span>
              </div>
              <ul className="mt-4 space-y-2 text-sm text-gray-600 list-disc pl-5">
                <li>Tudo do Solo</li>
                <li>Empresas ilimitadas</li>
                <li>Perfis e permissões</li>
              </ul>
              <Link href="/login" className="mt-auto bg-blue-600 hover:bg-blue-700 text-white w-full text-center py-3 rounded-lg font-medium">
                Assinar Team
              </Link>
            </div>

            {/* Business */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm flex flex-col">
              <h3 className="text-lg font-semibold text-gray-900">Business</h3>
              <p className="text-sm text-gray-500">até 10 usuários</p>
              <div className="mt-4">
                <span className="text-3xl font-extrabold">R$ 899</span>
                <span className="text-gray-500">/mês</span>
              </div>
              <ul className="mt-4 space-y-2 text-sm text-gray-600 list-disc pl-5">
                <li>Tudo do Team</li>
                <li>Relatórios avançados</li>
                <li>Suporte prioritário</li>
              </ul>
              <Link href="/login" className="mt-auto bg-blue-600 hover:bg-blue-700 text-white w-full text-center py-3 rounded-lg font-medium">
                Assinar Business
              </Link>
            </div>

            {/* Enterprise */}
            <div className="bg-white rounded-2xl border-2 border-gray-900 p-6 shadow-sm flex flex-col">
              <h3 className="text-lg font-semibold text-gray-900">Enterprise</h3>
              <p className="text-sm text-gray-500">equipes maiores • SSO • SLA</p>
              <div className="mt-4">
                <span className="text-2xl font-extrabold">Sob consulta</span>
              </div>
              <ul className="mt-4 space-y-2 text-sm text-gray-600 list-disc pl-5">
                <li>SSO/SAML, auditoria e logs</li>
                <li>Ambiente dedicado</li>
                <li>Integrações e onboarding</li>
              </ul>
              <a href="mailto:vendas@finaflow.com" className="mt-auto border border-gray-900 text-gray-900 hover:bg-gray-900 hover:text-white w-full text-center py-3 rounded-lg font-medium">
                Falar com vendas
              </a>
            </div>
          </div>
          <p className="mt-6 text-xs text-gray-500 text-center">
            Preços em BRL por mês. Impostos podem variar conforme a sua região.
          </p>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="py-20 bg-white">
        <div className="max-w-4xl mx-auto px-6">
          <h3 className="text-2xl md:text-3xl font-extrabold text-gray-900 text-center mb-10">Perguntas frequentes</h3>
          <div className="space-y-6 text-gray-700">
            <details className="rounded-xl border border-gray-200 p-4">
              <summary className="font-medium cursor-pointer">Posso testar antes de assinar?</summary>
              <p className="mt-2 text-gray-600">Sim. Você tem 14 dias de teste grátis sem precisar informar cartão.</p>
            </details>
            <details className="rounded-xl border border-gray-200 p-4">
              <summary className="font-medium cursor-pointer">Consigo cancelar quando quiser?</summary>
              <p className="mt-2 text-gray-600">Claro. Basta acessar a área de Billing e encerrar sua assinatura.</p>
            </details>
            <details className="rounded-xl border border-gray-200 p-4">
              <summary className="font-medium cursor-pointer">Como funciona o multi-empresa?</summary>
              <p className="mt-2 text-gray-600">Crie empresas e unidades (BUs) separadas e gerencie permissões por usuário.</p>
            </details>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-100 py-10">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-gray-500">
          <div className="flex items-center gap-2">
            <img src="/logo-finaflow.svg" alt="FinaFlow" className="h-6" />
            <span>© {new Date().getFullYear()} FinaFlow. Todos os direitos reservados.</span>
          </div>
          <div className="flex items-center gap-4">
            <a href="#pricing" className="hover:text-gray-700">Planos</a>
            <a href="#features" className="hover:text-gray-700">Recursos</a>
            <Link href="/login" className="hover:text-gray-700">Entrar</Link>
          </div>
        </div>
      </footer>
    </>
  );
}
