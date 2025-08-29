#!/usr/bin/env python3
"""
Script para adicionar proteção de rotas em todas as páginas principais
"""

import os
import re

def add_protection_to_page(file_path):
    """Adiciona proteção de rotas a uma página"""
    print(f"🔒 Adicionando proteção a: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar se já tem ProtectedRoute
    if 'ProtectedRoute' in content:
        print(f"   ⚠️ {file_path} já tem proteção")
        return False
    
    # Adicionar import
    if 'import ProtectedRoute' not in content:
        # Encontrar linha de imports
        import_pattern = r'(import.*from.*[\'"]\.\./services/api[\'"])'
        match = re.search(import_pattern, content)
        if match:
            # Adicionar import do ProtectedRoute após os imports existentes
            protected_import = 'import ProtectedRoute from \'../components/ProtectedRoute\';'
            content = content.replace(match.group(1), match.group(1) + '\n' + protected_import)
    
    # Encontrar a função principal
    main_function_pattern = r'export default function (\w+)\(\) \{'
    match = re.search(main_function_pattern, content)
    
    if match:
        function_name = match.group(1)
        print(f"   📝 Função encontrada: {function_name}")
        
        # Renomear função principal para Content
        content = re.sub(
            r'export default function (\w+)\(\) \{',
            r'function \1Content() {',
            content
        )
        
        # Adicionar nova função wrapper com ProtectedRoute
        wrapper_function = f'''
export default function {function_name}() {{
  return (
    <ProtectedRoute>
      <{function_name}Content />
    </ProtectedRoute>
  );
}}'''
        
        # Adicionar antes do último }
        content = content.rstrip() + '\n' + wrapper_function + '\n'
        
        # Salvar arquivo
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"   ✅ Proteção adicionada com sucesso")
        return True
    
    print(f"   ❌ Não foi possível adicionar proteção")
    return False

def main():
    """Função principal"""
    pages_dir = "frontend/pages"
    protected_pages = [
        "groups.tsx",
        "subgroups.tsx", 
        "users.tsx",
        "forecast.tsx",
        "reports.tsx",
        "settings.tsx",
        "csv-import.tsx"
    ]
    
    print("🔒 ADICIONANDO PROTEÇÃO DE ROTAS")
    print("=" * 50)
    
    success_count = 0
    total_count = len(protected_pages)
    
    for page in protected_pages:
        file_path = os.path.join(pages_dir, page)
        if os.path.exists(file_path):
            if add_protection_to_page(file_path):
                success_count += 1
        else:
            print(f"❌ Arquivo não encontrado: {file_path}")
    
    print("\n" + "=" * 50)
    print(f"📊 RESULTADO: {success_count}/{total_count} páginas protegidas")
    
    if success_count == total_count:
        print("🎉 Todas as páginas foram protegidas!")
    else:
        print("⚠️ Algumas páginas não foram protegidas")

if __name__ == "__main__":
    main()
