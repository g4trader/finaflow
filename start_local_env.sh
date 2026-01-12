#!/bin/bash

# 🚀 Script de Inicialização - Local Development Environment

set -e  # Exit on error

REPO_DIR="/Users/lucianoterres/Documents/GitHub/finaflow"

echo "=================================="
echo "🚀 Finaflow Local Dev Setup"
echo "=================================="
echo ""

# Check if Docker is running
echo "1️⃣  Verificando Docker..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker não está rodando. Abra Docker Desktop."
    exit 1
fi
echo "✅ Docker está rodando"
echo ""

# Navigate to repo
cd "$REPO_DIR"
echo "📁 Diretório: $REPO_DIR"
echo ""

# Option to clean previous containers
read -p "2️⃣  Deseja limpar containers/volumes anteriores? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 Limpando containers e volumes..."
    docker-compose down -v
    echo "✅ Limpo"
else
    echo "Mantendo dados anteriores"
fi
echo ""

# Build and start
echo "3️⃣  Construindo imagens e iniciando containers..."
docker-compose up --build -d

echo "✅ Containers iniciados em background"
echo ""

# Wait for postgres
echo "4️⃣  Aguardando PostgreSQL estar pronto..."
until docker-compose exec -T postgres pg_isready -U finaflow_user > /dev/null 2>&1; do
    echo "   Aguardando..."
    sleep 2
done
echo "✅ PostgreSQL pronto"
echo ""

# Show status
echo "5️⃣  Status dos serviços:"
docker-compose ps
echo ""

# Show URLs
echo "=================================="
echo "✨ Ambiente pronto!"
echo "=================================="
echo ""
echo "📍 URLs de Acesso:"
echo "  • Frontend:     http://localhost:3000"
echo "  • Backend API:  http://localhost:8000/docs"
echo "  • Backend Redoc: http://localhost:8000/redoc"
echo "  • Database:     localhost:5432"
echo ""
echo "👤 Credenciais do Banco:"
echo "  • User:     finaflow_user"
echo "  • Password: Finaflow123!"
echo "  • Database: finaflow"
echo ""
echo "📋 Comandos úteis:"
echo "  • Ver logs:              docker-compose logs -f"
echo "  • Backend logs:          docker-compose logs -f backend"
echo "  • Conectar ao banco:     psql -h localhost -U finaflow_user -d finaflow"
echo "  • Parar tudo:            docker-compose stop"
echo "  • Parar e limpar:        docker-compose down -v"
echo ""
echo "📚 Documentação:"
echo "  • Setup completo: ./LOCAL_DEV_SETUP.md"
echo ""
echo "=================================="
