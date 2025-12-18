#!/bin/bash
# Compliance OS - Initial Setup Script
# Sets up the development environment for first-time contributors

set -e

echo "🚀 Setting up Compliance OS V1..."
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 required but not installed. Aborting."; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js required but not installed. Aborting."; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Docker required but not installed. Aborting."; exit 1; }

echo "✅ All prerequisites found"
echo ""

# Backend setup
echo "🐍 Setting up backend..."
cd backend

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "   Python version: $PYTHON_VERSION"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "   Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Setup environment file
if [ ! -f ".env" ]; then
    echo "   Creating .env file from template..."
    cp .env.example .env
    echo "   ⚠️  Remember to update .env with your configuration!"
fi

cd ..
echo "✅ Backend setup complete"
echo ""

# Frontend setup
echo "⚛️  Setting up frontend..."
cd frontend

# Check Node version
NODE_VERSION=$(node --version)
echo "   Node version: $NODE_VERSION"

# Install dependencies
echo "   Installing Node dependencies..."
npm install

# Setup environment file
if [ ! -f ".env.local" ]; then
    echo "   Creating .env.local file from template..."
    cp .env.example .env.local
    echo "   ⚠️  Remember to update .env.local with your configuration!"
fi

cd ..
echo "✅ Frontend setup complete"
echo ""

# Docker setup check
echo "🐳 Checking Docker..."
if docker info >/dev/null 2>&1; then
    echo "✅ Docker is running"
else
    echo "⚠️  Docker is not running. Please start Docker Desktop."
fi
echo ""

# Summary
echo "✨ Setup complete!"
echo ""
echo "📚 Next steps:"
echo "  1. Update .env files with your configuration:"
echo "     - backend/.env"
echo "     - frontend/.env.local"
echo ""
echo "  2. Start services:"
echo "     docker-compose up -d"
echo ""
echo "  3. Setup database:"
echo "     make migrate"
echo ""
echo "  4. Seed data (optional):"
echo "     make seed"
echo ""
echo "  5. Start development servers:"
echo "     make dev"
echo ""
echo "📖 For more information, see README.md"
