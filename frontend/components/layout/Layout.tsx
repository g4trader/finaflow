import React, { useState } from 'react';
import { motion, AnimatePresence, type MotionProps } from 'framer-motion';
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
  LogOut,
  Menu,
  X,
  Bell,
  Search,
} from 'lucide-react';
import Button from '../ui/Button';

interface LayoutProps {
  children: React.ReactNode;
  title?: string;
}

interface MenuItem {
  icon: React.ReactNode;
  label: string;
  href: string;
  active?: boolean;
}

const Layout: React.FC<LayoutProps> = ({ children, title }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const menuItems: MenuItem[] = [
    { icon: <LayoutDashboard className="w-5 h-5" />, label: 'Dashboard', href: '/dashboard', active: title === 'Dashboard' },
    { icon: <Users className="w-5 h-5" />, label: 'Usuários', href: '/users', active: title === 'Usuários' },
    { icon: <CreditCard className="w-5 h-5" />, label: 'Transações', href: '/transactions', active: title === 'Transações' },
    { icon: <BarChart3 className="w-5 h-5" />, label: 'Relatórios', href: '/reports', active: title === 'Relatórios' },
    { icon: <Layers className="w-5 h-5" />, label: 'Grupos', href: '/groups', active: title === 'Grupos' },
    { icon: <Layers3 className="w-5 h-5" />, label: 'Subgrupos', href: '/subgroups', active: title === 'Subgrupos' },
    { icon: <Wallet className="w-5 h-5" />, label: 'Contas', href: '/accounts', active: title === 'Contas' },
    { icon: <TrendingUp className="w-5 h-5" />, label: 'Previsões', href: '/forecasts', active: title === 'Previsões' },
    { icon: <Settings className="w-5 h-5" />, label: 'Configurações', href: '/settings', active: title === 'Configurações' },
  ];

  const Sidebar: React.FC<{ mobile?: boolean }> = ({ mobile = false }) => {
    const motionProps: MotionProps = mobile
      ? { initial: { x: -300 }, animate: { x: 0 }, exit: { x: -300 } }
      : {};
    return (
      <motion.div
        {...motionProps}
        className={`${mobile ? 'fixed inset-y-0 left-0 z-50 w-64' : 'hidden lg:flex lg:w-64 lg:flex-col'} bg-white border-r border-gray-200`}
      >
        <div className="flex flex-col flex-1 min-h-0">
          {/* Brand */}
          <div className="flex items-center h-16 px-6 border-b border-gray-200">
            <a href="/" className="flex items-center gap-3">
              <img src="/logo-finaflow.svg" alt="finaFlow" className="h-8 w-auto" />
              <span className="sr-only">finaFlow</span>
            </a>
            {mobile && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSidebarOpen(false)}
                icon={<X className="w-5 h-5" />}
                className="ml-auto"
              />
            )}
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-1">
            {menuItems.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className={`flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                  item.active ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-700' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                {item.icon}
                <span className="ml-3">{item.label}</span>
              </a>
            ))}
          </nav>

          {/* User Menu */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-gray-300 rounded-full"></div>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-700">Admin User</p>
                <p className="text-xs text-gray-500">admin@finaflow.com</p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              icon={<LogOut className="w-4 h-4" />}
              className="w-full mt-3 justify-start"
            >
              Sair
            </Button>
          </div>
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
        <header className="bg-white border-b border-gray-200 px-6 py-4">
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
                  placeholder="Buscar..."
                  className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              {/* Notifications */}
              <Button variant="ghost" size="sm" icon={<Bell className="w-5 h-5" />} />

              {/* Profile */}
              <div className="w-8 h-8 bg-gray-300 rounded-full"></div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-6">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
            {children}
          </motion.div>
        </main>
      </div>
    </div>
  );
};

export default Layout;
