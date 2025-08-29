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
  ChevronDown
} from 'lucide-react';
import Button from '../ui/Button';
import { useAuth } from '../../context/AuthContext';
import { useRouter } from 'next/router';

interface LayoutProps {
  children: React.ReactNode;
  title?: string;
}

const Layout: React.FC<LayoutProps> = ({ children, title }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { logout, role, tenantId } = useAuth();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const menuItems = [
    {
      icon: <LayoutDashboard className="w-5 h-5" />,
      label: 'Dashboard',
      href: '/dashboard',
      active: title === 'Dashboard',
      description: 'Visão geral do sistema'
    },
    {
      icon: <Wallet className="w-5 h-5" />,
      label: 'Contas',
      href: '/accounts',
      active: title === 'Contas',
      description: 'Gerenciar contas bancárias'
    },
    {
      icon: <CreditCard className="w-5 h-5" />,
      label: 'Transações',
      href: '/transactions',
      active: title === 'Transações',
      description: 'Registrar e visualizar transações'
    },
    {
      icon: <Layers className="w-5 h-5" />,
      label: 'Grupos',
      href: '/groups',
      active: title === 'Grupos',
      description: 'Organizar contas em grupos'
    },
    {
      icon: <Layers3 className="w-5 h-5" />,
      label: 'Subgrupos',
      href: '/subgroups',
      active: title === 'Subgrupos',
      description: 'Subdivisões dos grupos'
    },
    {
      icon: <TrendingUp className="w-5 h-5" />,
      label: 'Previsões',
      href: '/forecast',
      active: title === 'Previsões',
      description: 'Análise e previsões financeiras'
    },
    {
      icon: <BarChart3 className="w-5 h-5" />,
      label: 'Relatórios',
      href: '/reports',
      active: title === 'Relatórios',
      description: 'Relatórios e análises'
    },
    {
      icon: <Upload className="w-5 h-5" />,
      label: 'Importar CSV',
      href: '/csv-import',
      active: title === 'Importar CSV',
      description: 'Importar dados via arquivo CSV'
    },
    {
      icon: <Users className="w-5 h-5" />,
      label: 'Usuários',
      href: '/users',
      active: title === 'Usuários',
      description: 'Gerenciar usuários do sistema'
    },
    {
      icon: <Settings className="w-5 h-5" />,
      label: 'Configurações',
      href: '/settings',
      active: title === 'Configurações',
      description: 'Configurações do sistema'
    },
  ];

  const Sidebar = ({ mobile = false }: { mobile?: boolean }) => {
    return (
      <motion.div
        initial={mobile ? { x: -300 } : false}
        animate={mobile ? { x: 0 } : false}
        exit={mobile ? { x: -300 } : false}
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
              <a
                key={item.href}
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
            ))}
          </div>
        </nav>

        {/* User Menu */}
        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
            <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
              <span className="text-white text-sm font-medium">A</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-700 truncate">Administrador</p>
              <p className="text-xs text-gray-500 truncate">admin@finaflow.com</p>
              {role && (
                <p className="text-xs text-blue-600 font-medium">{role}</p>
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
