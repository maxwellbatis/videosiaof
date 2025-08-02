#!/usr/bin/env python3
"""
Script para configurar o ambiente do Text-to-Video AI com banco de dados
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path

def create_env_file():
    """Cria o arquivo .env se não existir"""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("🔧 Criando arquivo .env...")
        
        # Solicitar informações do banco
        print("\n📋 Configuração do Banco de Dados:")
        db_host = input("Host (localhost): ").strip() or "localhost"
        db_port = input("Porta (5432): ").strip() or "5432"
        db_name = input("Nome do banco (textoemvideos): ").strip() or "textoemvideos"
        db_user = input("Usuário (postgres): ").strip() or "postgres"
        db_password = input("Senha do PostgreSQL: ").strip()
        
        if not db_password:
            print("❌ Senha é obrigatória!")
            return False
        
        # Criar conteúdo do .env
        env_content = f"""# Database Configuration
DATABASE_URL="postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?schema=public"

# API Keys (opcional - podem ser armazenadas no banco)
OPENAI_KEY=""
GROQ_API_KEY=""
PEXELS_KEY=""
"""
        
        # Salvar arquivo
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(env_content)
        
        print("✅ Arquivo .env criado com sucesso!")
        return True
    else:
        print("✅ Arquivo .env já existe!")
        return True

def setup_database():
    """Configura o banco de dados"""
    print("\n🗄️ Configurando banco de dados...")
    
    try:
        # Aplicar schema
        result = subprocess.run(["npx", "prisma", "db", "push"], 
                              capture_output=True, text=True, check=True)
        print("✅ Schema aplicado com sucesso!")
        
        # Configurar credenciais padrão
        print("\n🔑 Configurando credenciais padrão...")
        asyncio.run(setup_default_credentials())
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao configurar banco: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

async def setup_default_credentials():
    """Configura credenciais padrão no banco"""
    try:
        from database import VideoDatabase
        
        db = VideoDatabase()
        await db.connect()
        
        # Verificar se já existem credenciais
        existing = await db.get_credentials("default")
        if existing:
            print("✅ Credenciais padrão já existem!")
            await db.disconnect()
            return
        
        # Criar credenciais padrão
        print("\n🔑 Configurando credenciais padrão...")
        print("💡 Você pode configurar as chaves das APIs depois usando:")
        print("   python -m database.setup_database")
        
        credentials = await db.create_credentials(
            name="default",
            openai_key="",  # Será configurado depois
            groq_key="",    # Será configurado depois
            pexels_key=""   # Será configurado depois
        )
        
        print(f"✅ Credenciais padrão criadas: {credentials.id}")
        await db.disconnect()
        
    except Exception as e:
        print(f"⚠️ Erro ao configurar credenciais: {e}")
        print("💡 Você pode configurar manualmente depois")

def main():
    """Função principal"""
    print("🚀 Configurando Text-to-Video AI com Banco de Dados")
    print("=" * 50)
    
    # Verificar se Node.js está instalado
    try:
        subprocess.run(["node", "--version"], capture_output=True, check=True)
        print("✅ Node.js encontrado")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Node.js não encontrado!")
        print("💡 Instale o Node.js em: https://nodejs.org/")
        return False
    
    # Verificar se npm está instalado
    try:
        subprocess.run(["npm", "--version"], capture_output=True, check=True)
        print("✅ npm encontrado")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ npm não encontrado!")
        return False
    
    # Criar arquivo .env
    if not create_env_file():
        return False
    
    # Configurar banco
    if not setup_database():
        return False
    
    print("\n🎉 Configuração concluída com sucesso!")
    print("\n📖 Próximos passos:")
    print("1. Configure suas chaves de API:")
    print("   python -m database.setup_database")
    print("\n2. Teste gerando um vídeo:")
    print("   python app.py 'Fatos sobre o Brasil'")
    print("\n3. Liste os vídeos gerados:")
    print("   python -m database.setup_database list")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 