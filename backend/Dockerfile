FROM python:3.11-slim

# Definir variáveis de ambiente para Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Criar usuário não-root para segurança
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copiar toda a estrutura do projeto
COPY . .

# Alterar proprietário dos arquivos para o usuário não-root
RUN chown -R appuser:appuser /app

# Mudar para usuário não-root
USER appuser

# Expor porta 8080
EXPOSE 8080

# Comando para iniciar a aplicação
CMD ["python", "hybrid_app.py"]

