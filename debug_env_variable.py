#!/usr/bin/env python3
"""
Script para verificar o valor real da variável de ambiente no frontend
"""

import requests
import re
import json

def check_environment_variable():
    """Verifica o valor real da variável de ambiente no frontend"""
    print("🔍 Verificando variável de ambiente no frontend...")
    
    try:
        # Acessar o frontend
        response = requests.get("https://finaflow.vercel.app", timeout=10)
        
        if response.status_code == 200:
            print("✅ Frontend acessível")
            
            # Procurar por NEXT_PUBLIC_API_URL no código fonte
            content = response.text
            
            # Padrões para encontrar a variável
            patterns = [
                r'NEXT_PUBLIC_API_URL["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'process\.env\.NEXT_PUBLIC_API_URL',
                r'baseURL["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            ]
            
            found_urls = []
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                found_urls.extend(matches)
            
            # Procurar por URLs específicas do backend
            backend_patterns = [
                r'["\'](https?://finaflow-backend[^"\']+)["\']',
                r'["\'](https?://[^"\']*\.a\.run\.app[^"\']*)["\']',
            ]
            
            for pattern in backend_patterns:
                matches = re.findall(pattern, content)
                found_urls.extend(matches)
            
            print(f"\n📊 URLs encontradas no código fonte:")
            if found_urls:
                for url in set(found_urls):
                    if url:
                        protocol = "🔴 HTTP" if url.startswith("http://") else "🟢 HTTPS"
                        print(f"   {protocol}: {url}")
            else:
                print("   ⚠️  Nenhuma URL encontrada")
            
            # Verificar se há algum script que define a URL
            script_patterns = [
                r'<script[^>]*>([^<]+)</script>',
                r'window\.__NEXT_DATA__\s*=\s*({[^<]+})',
            ]
            
            print(f"\n🔍 Verificando scripts inline...")
            for pattern in script_patterns:
                matches = re.findall(pattern, content, re.DOTALL)
                for match in matches:
                    if 'finaflow-backend' in match or 'NEXT_PUBLIC_API_URL' in match:
                        print(f"   📄 Script encontrado com referência ao backend")
                        # Procurar por URLs HTTP no script
                        http_urls = re.findall(r'http://[^"\']*finaflow-backend[^"\']*', match)
                        if http_urls:
                            print(f"   ❌ URLs HTTP encontradas no script:")
                            for url in http_urls:
                                print(f"      - {url}")
            
            return len([url for url in found_urls if url.startswith("http://")]) > 0
                
        else:
            print(f"❌ Frontend não acessível: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao acessar frontend: {e}")
        return False

def check_build_output():
    """Verifica se há algum arquivo de build que pode conter a URL hardcoded"""
    print("\n🔍 Verificando se há URLs hardcoded...")
    
    try:
        # Tentar acessar arquivos JavaScript compilados
        js_files = [
            "/_next/static/chunks/pages/transactions-*.js",
            "/_next/static/chunks/pages/csv-import-*.js",
            "/_next/static/chunks/pages/_app-*.js",
        ]
        
        for js_pattern in js_files:
            try:
                # Tentar acessar o diretório _next
                response = requests.get("https://finaflow.vercel.app/_next/static/chunks/", timeout=5)
                if response.status_code == 200:
                    print("   📁 Diretório _next acessível")
                    break
            except:
                pass
        
        # Verificar se há algum arquivo de configuração
        config_files = [
            "/next.config.js",
            "/package.json",
            "/.env",
            "/.env.local",
        ]
        
        for config_file in config_files:
            try:
                response = requests.get(f"https://finaflow.vercel.app{config_file}", timeout=5)
                if response.status_code == 200:
                    print(f"   📄 {config_file} acessível")
                    content = response.text
                    if 'http://' in content and 'finaflow-backend' in content:
                        print(f"   ❌ {config_file} contém URL HTTP!")
            except:
                pass
                
    except Exception as e:
        print(f"   ⚠️  Erro ao verificar build: {e}")

def provide_detailed_solution():
    """Fornece solução detalhada"""
    print("\n🔧 SOLUÇÃO DETALHADA:")
    print("=" * 50)
    print("O problema pode estar em várias fontes:")
    print("\n1. 📝 Verificar arquivos de configuração:")
    print("   - .env.local")
    print("   - .env.production") 
    print("   - next.config.js")
    print("\n2. 🔄 Forçar rebuild completo:")
    print("   - Deletar .next/ no Vercel")
    print("   - Fazer commit com mudança real")
    print("\n3. 🛠️  Verificar se há fallback hardcoded:")
    print("   - Procurar por 'http://' no código")
    print("   - Verificar se há valor padrão")

def main():
    print("🚀 Debug da Variável de Ambiente - finaFlow")
    print("=" * 50)
    
    has_http = check_environment_variable()
    check_build_output()
    provide_detailed_solution()
    
    if has_http:
        print("\n❌ PROBLEMA CONFIRMADO: URLs HTTP encontradas no frontend")
    else:
        print("\n✅ Nenhuma URL HTTP encontrada no código fonte")
        print("   O problema pode estar no build ou cache")

if __name__ == "__main__":
    main()
