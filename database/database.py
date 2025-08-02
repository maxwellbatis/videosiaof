import os
import asyncio
from prisma import Prisma
from datetime import datetime
from typing import Optional

class VideoDatabase:
    def __init__(self):
        self.db = Prisma()
    
    async def connect(self):
        await self.db.connect()
    
    async def disconnect(self):
        await self.db.disconnect()
    
    async def create_credentials(self, name: str, openai_key: Optional[str] = None, 
                                groq_key: Optional[str] = None, pexels_key: Optional[str] = None):
        """Cria um novo registro de credenciais"""
        return await self.db.apicredentials.create({
            'data': {
                'name': name,
                'openaiKey': openai_key,
                'groqKey': groq_key,
                'pexelsKey': pexels_key
            }
        })
    
    async def get_credentials(self, name: str):
        """Busca credenciais por nome"""
        return await self.db.apicredentials.find_unique({
            'where': {'name': name}
        })
    
    async def create_video(self, title: str, topic: str, script: str, credentials_id: str):
        """Cria um novo registro de vídeo"""
        return await self.db.video.create({
            'data': {
                'title': title,
                'topic': topic,
                'script': script,
                'status': 'PENDING',
                'credentialsId': credentials_id
            }
        })
    
    async def update_video_status(self, video_id: str, status: str, 
                                 audio_path: Optional[str] = None, 
                                 video_path: Optional[str] = None,
                                 duration: Optional[float] = None):
        """Atualiza o status e caminhos do vídeo"""
        return await self.db.video.update({
            'where': {'id': video_id},
            'data': {
                'status': status,
                'audioPath': audio_path,
                'videoPath': video_path,
                'duration': duration
            }
        })
    
    async def get_video(self, video_id: str):
        """Busca um vídeo por ID"""
        return await self.db.video.find_unique({
            'where': {'id': video_id},
            'include': {'credentials': True}
        })
    
    async def list_videos(self, limit: int = 10):
        """Lista os vídeos mais recentes"""
        return await self.db.video.find_many(
            take=limit,
            order=[{'createdAt': 'desc'}],
            include={'credentials': True}
        )
    
    async def delete_video(self, video_id: str):
        """Deleta um vídeo"""
        return await self.db.video.delete({
            'where': {'id': video_id}
        })

# Exemplo de uso
async def main():
    db = VideoDatabase()
    await db.connect()
    
    try:
        # Criar credenciais
        credentials = await db.create_credentials(
            name="default",
            openai_key="sua_chave_openai",
            groq_key="sua_chave_groq",
            pexels_key="sua_chave_pexels"
        )
        print(f"Credenciais criadas: {credentials.id}")
        
        # Criar vídeo
        video = await db.create_video(
            title="Fatos sobre o Brasil",
            topic="Fatos sobre o Brasil",
            script="O Brasil é o país com a maior biodiversidade...",
            credentials_id=credentials.id
        )
        print(f"Vídeo criado: {video.id}")
        
        # Atualizar status
        await db.update_video_status(
            video_id=video.id,
            status="COMPLETED",
            audio_path="audio_tts.wav",
            video_path="rendered_video.mp4",
            duration=42.5
        )
        print("Vídeo atualizado com sucesso!")
        
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(main()) 