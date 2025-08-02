import asyncio
from .database import VideoDatabase

async def setup_database():
    """Configura o banco de dados com credenciais padrão"""
    db = VideoDatabase()
    await db.connect()
    
    try:
        # Criar credenciais padrão
        credentials = await db.create_credentials(
            name="default",
            openai_key="sua_chave_openai_aqui",
            groq_key="sua_chave_groq_aqui", 
            pexels_key="sua_chave_pexels_aqui"
        )
        print(f"✅ Credenciais padrão criadas: {credentials.id}")
        
        # Listar credenciais existentes
        print("\n📋 Credenciais existentes:")
        all_credentials = await db.db.apicredentials.find_many()
        for cred in all_credentials:
            print(f"  - {cred.name} (ID: {cred.id})")
            
    except Exception as e:
        print(f"❌ Erro ao configurar banco: {e}")
    
    finally:
        await db.disconnect()

async def list_videos():
    """Lista todos os vídeos no banco"""
    db = VideoDatabase()
    await db.connect()
    
    try:
        videos = await db.list_videos(limit=20)
        print(f"\n📹 Vídeos no banco ({len(videos)} encontrados):")
        
        for video in videos:
            status_emoji = {
                "PENDING": "⏳",
                "PROCESSING": "🔄", 
                "COMPLETED": "✅",
                "FAILED": "❌"
            }.get(video.status, "❓")
            
            print(f"  {status_emoji} {video.title}")
            print(f"     Tópico: {video.topic}")
            print(f"     Status: {video.status}")
            print(f"     ID: {video.id}")
            if video.videoPath:
                print(f"     Arquivo: {video.videoPath}")
            print()
            
    except Exception as e:
        print(f"❌ Erro ao listar vídeos: {e}")
    
    finally:
        await db.disconnect()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        asyncio.run(list_videos())
    else:
        print("🔧 Configurando banco de dados...")
        asyncio.run(setup_database())
        print("\n📋 Listando vídeos...")
        asyncio.run(list_videos()) 