#!/usr/bin/env python3
"""
Script para corrigir erros de indentação no hybrid_app.py
"""
import re

def fix_indentation(file_path):
    """Corrige erros de indentação conhecidos"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"📖 Lendo arquivo: {file_path}")
    print(f"   Tamanho: {len(content)} caracteres")
    
    # Correção 1: try: seguido de linha sem indentação
    # Padrão: "try:\n    user_id" deve ser "try:\n        user_id"
    pattern1 = r'(\s+try:)\n(\s{0,3}[a-z_])'
    
    def fix_try_block(match):
        try_line = match.group(1)
        next_line_start = match.group(2)
        
        # Calcular indentação correta (indentação do try + 4 espaços)
        try_indent = len(try_line) - len(try_line.lstrip())
        correct_indent = ' ' * (try_indent + 4)
        
        # Remover indentação existente e adicionar correta
        next_line_content = next_line_start.lstrip()
        
        return f"{try_line}\n{correct_indent}{next_line_content}"
    
    original_content = content
    content = re.sub(pattern1, fix_try_block, content)
    
    if content != original_content:
        print(f"   ✅ Correção 1 aplicada: try: com indentação")
    
    # Correção 2: return fora do try block
    # Procurar padrões onde return está no mesmo nível que try
    lines = content.split('\n')
    fixed_lines = []
    in_function = False
    try_indent_level = None
    
    for i, line in enumerate(lines):
        # Detectar início de função async/def
        if re.match(r'^\s*(async\s+)?def\s+', line):
            in_function = True
            try_indent_level = None
        
        # Detectar try:
        if in_function and line.strip() == 'try:':
            try_indent_level = len(line) - len(line.lstrip())
        
        # Detectar return no mesmo nível do try
        if (try_indent_level is not None and 
            line.strip().startswith('return ') and
            len(line) - len(line.lstrip()) == try_indent_level):
            
            # Adicionar 4 espaços de indentação
            line = ' ' * 4 + line
            print(f"   ✅ Correção 2 aplicada: return indentado (linha {i+1})")
        
        fixed_lines.append(line)
    
    content = '\n'.join(fixed_lines)
    
    # Salvar arquivo corrigido
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Arquivo salvo: {file_path}\n")
    
    return True

if __name__ == "__main__":
    import sys
    
    # Arquivos para corrigir
    files = [
        "/Users/lucianoterres/Documents/GitHub/finaflow/hybrid_app.py",
    ]
    
    print("="*80)
    print("  🔧 CORREÇÃO AUTOMÁTICA DE INDENTAÇÃO")
    print("="*80)
    print()
    
    for file_path in files:
        try:
            fix_indentation(file_path)
        except Exception as e:
            print(f"❌ Erro ao corrigir {file_path}: {e}")
            sys.exit(1)
    
    print("="*80)
    print("  ✅ CORREÇÕES CONCLUÍDAS")
    print("="*80)
    print()
    print("Próximo passo:")
    print("  cp hybrid_app.py backend/hybrid_app.py")
    print("  python3 -m py_compile backend/hybrid_app.py")
    print("  gcloud builds submit --config backend/cloudbuild.yaml .")


