#!/usr/bin/env python3
"""
Script para verificar e corrigir problemas do frontend FinaFlow
"""

import os
import re
from pathlib import Path

class FrontendFixer:
    def __init__(self):
        self.frontend_path = Path("frontend")
        self.issues = []
        self.fixes = []
        
    def check_auth_context(self):
        """Verifica e corrige o AuthContext"""
        print("🔍 Verificando AuthContext...")
        
        auth_file = self.frontend_path / "context" / "AuthContext.tsx"
        if not auth_file.exists():
            self.issues.append("❌ AuthContext.tsx não encontrado")
            return
        
        with open(auth_file, 'r') as f:
            content = f.read()
        
        # Verificar se useAuth está exportado
        if 'export const useAuth' not in content:
            self.issues.append("❌ useAuth não está exportado")
            
            # Adicionar o hook useAuth
            if 'import React, { createContext, useState, useEffect, ReactNode }' in content:
                new_import = 'import React, { createContext, useState, useEffect, ReactNode, useContext }'
                content = content.replace(
                    'import React, { createContext, useState, useEffect, ReactNode }',
                    new_import
                )
            
            # Adicionar o hook useAuth após a definição do contexto
            if 'export const AuthContext = createContext<AuthContextType>({} as AuthContextType);' in content:
                hook_code = '''
// Hook personalizado para usar o contexto de autenticação
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth deve ser usado dentro de um AuthProvider');
  }
  return context;
};
'''
                content = content.replace(
                    'export const AuthContext = createContext<AuthContextType>({} as AuthContextType);',
                    'export const AuthContext = createContext<AuthContextType>({} as AuthContextType);' + hook_code
                )
                
                with open(auth_file, 'w') as f:
                    f.write(content)
                
                self.fixes.append("✅ useAuth adicionado ao AuthContext")
                print("✅ useAuth adicionado ao AuthContext")
        else:
            print("✅ useAuth já está exportado")
    
    def check_csv_import_page(self):
        """Verifica a página de importação CSV"""
        print("🔍 Verificando página CSV Import...")
        
        csv_page = self.frontend_path / "pages" / "csv-import.tsx"
        if not csv_page.exists():
            self.issues.append("❌ csv-import.tsx não encontrado")
            return
        
        with open(csv_page, 'r') as f:
            content = f.read()
        
        # Verificar importações
        if 'import { useAuth } from \'../context/AuthContext\';' not in content:
            self.issues.append("❌ useAuth não está sendo importado")
        else:
            print("✅ useAuth está sendo importado corretamente")
        
        # Verificar se a página está usando o hook
        if 'const { token } = useAuth();' not in content:
            self.issues.append("❌ useAuth não está sendo usado")
        else:
            print("✅ useAuth está sendo usado corretamente")
    
    def check_package_json(self):
        """Verifica o package.json"""
        print("🔍 Verificando package.json...")
        
        package_file = self.frontend_path / "package.json"
        if not package_file.exists():
            self.issues.append("❌ package.json não encontrado")
            return
        
        with open(package_file, 'r') as f:
            content = f.read()
        
        # Verificar dependências essenciais
        essential_deps = [
            "next",
            "react",
            "react-dom",
            "typescript",
            "jwt-decode"
        ]
        
        missing_deps = []
        for dep in essential_deps:
            if f'"{dep}"' not in content:
                missing_deps.append(dep)
        
        if missing_deps:
            self.issues.append(f"❌ Dependências faltando: {missing_deps}")
        else:
            print("✅ Todas as dependências essenciais estão presentes")
    
    def check_tsconfig(self):
        """Verifica o tsconfig.json"""
        print("🔍 Verificando tsconfig.json...")
        
        tsconfig_file = self.frontend_path / "tsconfig.json"
        if not tsconfig_file.exists():
            self.issues.append("❌ tsconfig.json não encontrado")
            return
        
        with open(tsconfig_file, 'r') as f:
            content = f.read()
        
        # Verificar configurações essenciais
        if '"strict": false' in content:
            print("⚠️  TypeScript strict mode está desabilitado")
        else:
            print("✅ TypeScript strict mode está habilitado")
        
        if '"jsx": "preserve"' in content:
            print("✅ JSX está configurado corretamente")
        else:
            self.issues.append("❌ JSX não está configurado")
    
    def check_app_structure(self):
        """Verifica a estrutura do app"""
        print("🔍 Verificando estrutura do app...")
        
        required_files = [
            "pages/_app.tsx",
            "pages/csv-import.tsx",
            "context/AuthContext.tsx",
            "services/api.ts",
            "package.json",
            "tsconfig.json"
        ]
        
        for file_path in required_files:
            full_path = self.frontend_path / file_path
            if full_path.exists():
                print(f"✅ {file_path}")
            else:
                self.issues.append(f"❌ {file_path} não encontrado")
    
    def check_environment_variables(self):
        """Verifica variáveis de ambiente"""
        print("🔍 Verificando variáveis de ambiente...")
        
        env_file = self.frontend_path / ".env.local"
        if not env_file.exists():
            print("⚠️  .env.local não encontrado - será criado")
            
            env_content = """# Configurações da API
NEXT_PUBLIC_API_URL=http://localhost:8000

# Configurações do ambiente
NODE_ENV=development
"""
            
            with open(env_file, 'w') as f:
                f.write(env_content)
            
            self.fixes.append("✅ .env.local criado")
            print("✅ .env.local criado")
        else:
            print("✅ .env.local encontrado")
    
    def create_next_config(self):
        """Cria next.config.js se não existir"""
        print("🔍 Verificando next.config.js...")
        
        next_config = self.frontend_path / "next.config.js"
        if not next_config.exists():
            print("⚠️  next.config.js não encontrado - será criado")
            
            config_content = """/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  experimental: {
    appDir: false,
  },
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
  },
}

module.exports = nextConfig
"""
            
            with open(next_config, 'w') as f:
                f.write(config_content)
            
            self.fixes.append("✅ next.config.js criado")
            print("✅ next.config.js criado")
        else:
            print("✅ next.config.js encontrado")
    
    def create_postcss_config(self):
        """Cria postcss.config.js se não existir"""
        print("🔍 Verificando postcss.config.js...")
        
        postcss_config = self.frontend_path / "postcss.config.js"
        if not postcss_config.exists():
            print("⚠️  postcss.config.js não encontrado - será criado")
            
            config_content = """module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
"""
            
            with open(postcss_config, 'w') as f:
                f.write(config_content)
            
            self.fixes.append("✅ postcss.config.js criado")
            print("✅ postcss.config.js criado")
        else:
            print("✅ postcss.config.js encontrado")
    
    def create_tailwind_config(self):
        """Cria tailwind.config.js se não existir"""
        print("🔍 Verificando tailwind.config.js...")
        
        tailwind_config = self.frontend_path / "tailwind.config.js"
        if not tailwind_config.exists():
            print("⚠️  tailwind.config.js não encontrado - será criado")
            
            config_content = """/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
      },
    },
  },
  plugins: [],
}
"""
            
            with open(tailwind_config, 'w') as f:
                f.write(config_content)
            
            self.fixes.append("✅ tailwind.config.js criado")
            print("✅ tailwind.config.js criado")
        else:
            print("✅ tailwind.config.js encontrado")
    
    def run_fixes(self):
        """Executa todas as correções"""
        print("🚀 VERIFICANDO E CORRIGINDO PROBLEMAS DO FRONTEND\n")
        print("=" * 60)
        
        checks = [
            ("Estrutura do App", self.check_app_structure),
            ("AuthContext", self.check_auth_context),
            ("Página CSV Import", self.check_csv_import_page),
            ("Package.json", self.check_package_json),
            ("TSConfig", self.check_tsconfig),
            ("Variáveis de Ambiente", self.check_environment_variables),
            ("Next Config", self.create_next_config),
            ("PostCSS Config", self.create_postcss_config),
            ("Tailwind Config", self.create_tailwind_config),
        ]
        
        for check_name, check_func in checks:
            try:
                check_func()
            except Exception as e:
                self.issues.append(f"❌ Erro no check {check_name}: {e}")
        
        # Relatório final
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO FINAL")
        print("=" * 60)
        
        print(f"\n❌ Problemas encontrados: {len(self.issues)}")
        for issue in self.issues:
            print(f"  {issue}")
        
        print(f"\n✅ Correções aplicadas: {len(self.fixes)}")
        for fix in self.fixes:
            print(f"  {fix}")
        
        # Instruções para build
        print("\n🎯 PRÓXIMOS PASSOS")
        print("=" * 60)
        
        if not self.issues:
            print("✅ FRONTEND PRONTO PARA BUILD!")
            print("\n📋 Comandos para executar:")
            print("1. cd frontend")
            print("2. npm install")
            print("3. npm run build")
            print("4. npm start")
        else:
            print("⚠️  CORRIJA OS PROBLEMAS ANTES DO BUILD!")
            print("\n🔧 Ações necessárias:")
            for issue in self.issues:
                print(f"  - {issue}")
        
        print(f"\n📊 Resumo:")
        print(f"  ✅ Correções: {len(self.fixes)}")
        print(f"  ❌ Problemas: {len(self.issues)}")
        print(f"  🎯 Status: {'PRONTO' if not self.issues else 'PENDENTE'}")

if __name__ == "__main__":
    fixer = FrontendFixer()
    fixer.run_fixes()
