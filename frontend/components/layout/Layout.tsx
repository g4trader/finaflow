import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  LayoutDashboard, 
  Users, 
  CreditCard, 
  BarChart3, 
  Layers, 
  Layers3, 
  Wallet, 
  TrendingUp, 
  Settings, 
  Upload,
  Menu, 
  X, 
  Search, 
  Bell, 
  LogOut,
  ChevronDown,
  Building2,
  GitBranch,
  Shield,
  BookOpen,
  FileSpreadsheet,
  Activity,
  Calendar
} from 'lucide-react';
import Button from '../ui/Button';
import { useAuth } from '../../context/AuthContext';
import { getUserInfo } from '../../services/api';
import { useRouter } from 'next/router';
import { useEffect } from 'react';

interface LayoutProps {
  children: React.ReactNode;
  title?: string;
}

const Layout: React.FC<LayoutProps> = ({ children, title }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { logout, role, tenantId, user } = useAuth();
  const router = useRouter();
  const [userInfo, setUserInfo] = useState<any>(null);

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  // Buscar informações completas do usuário
  useEffect(() => {
    const fetchUserInfo = async () => {
      try {
        const info = await getUserInfo();
        setUserInfo(info);
      } catch (error) {
        console.error('Erro ao buscar informações do usuário:', error);
      }
    };

    if (user) {
      fetchUserInfo();
    }
  }, [user]);

  // Detectar se a página atual está em um submenu e expandir automaticamente
  const getInitialExpandedMenus = () => {
    const expanded = new Set<string>();
    
      // Verificar se a página atual está no submenu de Configurações
  const configSubmenuPages = [
    'Empresas', 'Business Units', 'Usuários', 'Plano de Contas',
    'Grupos', 'Subgrupos', 'Importar CSV', 'Importar Google Sheets', 'Permissões de Usuário'
  ];
    
    if (title && configSubmenuPages.includes(title)) {
      expanded.add('Configurações');
    }
    
    return expanded;
  };

  const [expandedMenus, setExpandedMenus] = useState<Set<string>>(getInitialExpandedMenus());

  const toggleMenu = (menuKey: string) => {
    const newExpanded = new Set(expandedMenus);
    if (newExpanded.has(menuKey)) {
      newExpanded.delete(menuKey);
    } else {
      newExpanded.add(menuKey);
    }
    setExpandedMenus(newExpanded);
  };

  // Função para verificar se um item está ativo baseado no pathname e título
  const isItemActive = (itemHref: string | null, itemTitle: string) => {
    if (itemHref && router.pathname === itemHref) {
      return true;
    }
    if (title && title === itemTitle) {
      return true;
    }
    return false;
  };

  const menuItems = [
    {
      icon: <LayoutDashboard className="w-5 h-5" />,
      label: 'Dashboard',
      href: '/dashboard',
      active: isItemActive('/dashboard', 'Dashboard'),
      description: 'Visão geral do sistema'
    },
    {
      icon: <CreditCard className="w-5 h-5" />,
      label: 'Lançamentos Financeiros',
      href: '/transactions',
      active: isItemActive('/transactions', 'Lançamentos Financeiros'),
      description: 'Lançamentos diários com estrutura da planilha (Grupo, Subgrupo, Conta)'
    },

    {
      icon: <TrendingUp className="w-5 h-5" />,
      label: 'Previsões Financeiras',
      href: '/financial-forecasts',
      active: isItemActive('/financial-forecasts', 'Previsões Financeiras'),
      description: 'Gerenciar previsões financeiras'
    },
    {
      icon: <Activity className="w-5 h-5" />,
      label: 'Fluxo de Caixa Mensal',
      href: '/cash-flow',
      active: isItemActive('/cash-flow', 'Fluxo de Caixa'),
      description: 'Análise Previsto x Realizado por mês'
    },
    {
      icon: <Calendar className="w-5 h-5" />,
      label: 'Fluxo de Caixa Diário',
      href: '/daily-cash-flow',
      active: isItemActive('/daily-cash-flow', 'Fluxo de Caixa Diário'),
      description: 'Movimentação diária do mês'
    },
    {
      icon: <BarChart3 className="w-5 h-5" />,
      label: 'Relatórios',
      href: '/reports',
      active: isItemActive('/reports', 'Relatórios'),
      description: 'Relatórios e análises'
    },
    {
      icon: <Settings className="w-5 h-5" />,
      label: 'Configurações',
      href: null,
      active: false,
      description: 'Configurações do sistema',
      hasSubmenu: true,
      submenu: [
        {
          icon: <Building2 className="w-4 h-4" />,
          label: 'Empresas',
          href: '/companies',
          active: isItemActive('/companies', 'Empresas'),
          description: 'Gerenciar empresas (tenants)'
        },
        {
          icon: <GitBranch className="w-4 h-4" />,
          label: 'Business Units',
          href: '/business-units',
          active: isItemActive('/business-units', 'Business Units'),
          description: 'Gerenciar business units'
        },
        {
          icon: <Users className="w-4 h-4" />,
          label: 'Usuários',
          href: '/users',
          active: isItemActive('/users', 'Usuários'),
          description: 'Gerenciar usuários do sistema'
        },

        {
          icon: <BookOpen className="w-4 h-4" />,
          label: 'Plano de Contas',
          href: '/chart-accounts',
          active: isItemActive('/chart-accounts', 'Plano de Contas'),
          description: 'Estrutura contábil da empresa'
        },
        {
          icon: <Layers className="w-4 h-4" />,
          label: 'Grupos',
          href: '/groups',
          active: isItemActive('/groups', 'Grupos'),
          description: 'Gerenciar grupos do plano de contas'
        },
        {
          icon: <Layers3 className="w-4 h-4" />,
          label: 'Subgrupos',
          href: '/subgroups',
          active: isItemActive('/subgroups', 'Subgrupos'),
          description: 'Gerenciar subgrupos do plano de contas'
        },
        {
          icon: <Upload className="w-4 h-4" />,
          label: 'Importar CSV',
          href: '/csv-import',
          active: isItemActive('/csv-import', 'Importar CSV'),
          description: 'Importar dados via arquivo CSV'
        },
        {
          icon: <FileSpreadsheet className="w-4 h-4" />,
          label: 'Importar Google Sheets',
          href: '/google-sheets-import',
          active: isItemActive('/google-sheets-import', 'Importar Google Sheets'),
          description: 'Importar dados da metodologia Ana Paula via Google Sheets'
        },
        {
          icon: <Shield className="w-4 h-4" />,
          label: 'Permissões de Usuário',
          href: '/user-permissions',
          active: isItemActive('/user-permissions', 'Permissões de Usuário'),
          description: 'Gerenciar permissões de usuário por empresa/BU'
        },

      ]
    },
  ];

  const Sidebar = ({ mobile = false }: { mobile?: boolean }) => {
    return (
      <motion.div
        initial={mobile ? { x: -300 } : { x: 0 }}
        animate={mobile ? { x: 0 } : { x: 0 }}
        exit={mobile ? { x: -300 } : { x: 0 }}
        transition={{ duration: 0.3 }}
        className={`bg-white border-r border-gray-200 flex flex-col ${
          mobile ? 'fixed inset-y-0 left-0 z-50 w-80 lg:hidden' : 'hidden lg:flex w-80'
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">F</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">FinaFlow</h1>
              <p className="text-xs text-gray-500">Gestão Financeira</p>
            </div>
          </div>
          {mobile && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSidebarOpen(false)}
              icon={<X className="w-5 h-5" />}
            />
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto p-4">
          <div className="space-y-2">
            {menuItems.map((item) => (
              <div key={item.label}>
                {item.hasSubmenu ? (
                  <div>
                    <button
                      onClick={() => toggleMenu(item.label)}
                      className={`flex items-center justify-between w-full px-3 py-2 rounded-lg transition-colors group ${
                        item.active
                          ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-700'
                          : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                      }`}
                      title={item.description}
                    >
                      <div className="flex items-center space-x-3">
                        <span className={item.active ? 'text-blue-600' : 'text-gray-400 group-hover:text-gray-600'}>
                          {item.icon}
                        </span>
                        <span className="font-medium">{item.label}</span>
                      </div>
                      <ChevronDown 
                        className={`w-4 h-4 transition-transform ${
                          expandedMenus.has(item.label) ? 'rotate-180' : ''
                        }`}
                      />
                    </button>
                    {expandedMenus.has(item.label) && (
                      <div className="ml-6 mt-2 space-y-1">
                        {item.submenu?.map((subItem) => (
                          <a
                            key={subItem.href}
                            href={subItem.href}
                            className={`flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors group ${
                              subItem.active
                                ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-700'
                                : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                            }`}
                            title={subItem.description}
                          >
                            <span className={subItem.active ? 'text-blue-600' : 'text-gray-400 group-hover:text-gray-600'}>
                              {subItem.icon}
                            </span>
                            <span className="font-medium text-sm">{subItem.label}</span>
                          </a>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <a
                    href={item.href}
                    className={`flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors group ${
                      item.active
                        ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-700'
                        : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                    title={item.description}
                  >
                    <span className={item.active ? 'text-blue-600' : 'text-gray-400 group-hover:text-gray-600'}>
                      {item.icon}
                    </span>
                    <span className="font-medium">{item.label}</span>
                  </a>
                )}
              </div>
            ))}
          </div>
        </nav>

        {/* User Menu */}
        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
            <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
              <span className="text-white text-sm font-medium">
                {userInfo?.first_name?.charAt(0) || user?.first_name?.charAt(0) || 'A'}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-700 truncate">
                {userInfo?.first_name || user?.first_name || 'Usuário'}
              </p>
              <p className="text-xs text-gray-500 truncate">
                {userInfo?.email || user?.email || 'email@exemplo.com'}
              </p>
              {userInfo?.tenant_name && (
                <p className="text-xs text-blue-600 font-medium">
                  {userInfo.tenant_name}
                </p>
              )}
              {userInfo?.business_unit_name && (
                <p className="text-xs text-green-600 font-medium">
                  {userInfo.business_unit_name}
                </p>
              )}
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleLogout}
            icon={<LogOut className="w-4 h-4" />}
            className="w-full mt-3 justify-start text-gray-600 hover:text-red-600 hover:bg-red-50"
          >
            Sair do Sistema
          </Button>
        </div>
      </motion.div>
    );
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Desktop Sidebar */}
      <Sidebar />

      {/* Mobile Sidebar */}
      {sidebarOpen && (
        <>
          <div className="fixed inset-0 z-40 bg-black bg-opacity-50 lg:hidden" onClick={() => setSidebarOpen(false)} />
          <AnimatePresence>{sidebarOpen && <Sidebar mobile />}</AnimatePresence>
        </>
      )}

      {/* Main Content */}
      <div className="flex flex-col flex-1 overflow-hidden">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSidebarOpen(true)}
                icon={<Menu className="w-5 h-5" />}
                className="lg:hidden"
              />
              {title && (
                <h1 className="ml-4 lg:ml-0 text-2xl font-semibold text-gray-900">{title}</h1>
              )}
            </div>

            <div className="flex items-center space-x-4">
              {/* Search */}
              <div className="hidden md:block relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Buscar no sistema..."
                  className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 w-64"
                />
              </div>

              {/* Notifications */}
              <Button 
                variant="ghost" 
                size="sm" 
                icon={<Bell className="w-5 h-5" />}
                className="relative"
              >
                <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full"></span>
              </Button>

              {/* Profile Dropdown */}
              <div className="relative">
                <Button
                  variant="ghost"
                  size="sm"
                  icon={<ChevronDown className="w-4 h-4" />}
                  className="flex items-center space-x-2"
                >
                  <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-medium">A</span>
                  </div>
                </Button>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-6">
          <motion.div 
            initial={{ opacity: 0, y: 20 }} 
            animate={{ opacity: 1, y: 0 }} 
            transition={{ duration: 0.3 }}
            className="h-full"
          >
            {children}
          </motion.div>
        </main>
      </div>
    </div>
  );
};

export default Layout;
