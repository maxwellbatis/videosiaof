from openai import OpenAI
import os
import edge_tts
import json
import asyncio
import whisper_timestamped as whisper
from utility.script.script_generator import generate_script
from utility.audio.audio_generator import generate_audio
from utility.captions.timed_captions_generator import generate_timed_captions
from utility.video.background_video_generator import generate_video_url
from utility.render.render_engine import get_output_media
from utility.video.video_search_query_generator import getVideoSearchQueriesTimed, merge_empty_intervals
from database import VideoDatabase
import argparse

async def generate_video_with_db(topic: str, credentials_name: str = "default", use_db: bool = True):
    """Gera vídeo e salva no banco de dados"""
    
    db = None
    video_id = None
    
    if use_db:
        # Conectar ao banco
        db = VideoDatabase()
        await db.connect()
        
        try:
            # Buscar credenciais
            credentials = await db.get_credentials(credentials_name)
            if not credentials:
                print(f"Credenciais '{credentials_name}' não encontradas! Usando variáveis de ambiente.")
            else:
                # Configurar variáveis de ambiente
                if credentials.openaiKey:
                    os.environ['OPENAI_KEY'] = credentials.openaiKey
                if credentials.groqKey:
                    os.environ['GROQ_API_KEY'] = credentials.groqKey
                if credentials.pexelsKey:
                    os.environ['PEXELS_KEY'] = credentials.pexelsKey
                
                # Criar registro de vídeo
                video = await db.create_video(
                    title=f"Vídeo sobre {topic}",
                    topic=topic,
                    script="",  # Será atualizado depois
                    credentials_id=credentials.id
                )
                video_id = video.id
                print(f"Vídeo criado no banco: {video_id}")
                
                # Atualizar status para PROCESSING
                await db.update_video_status(video_id, "PROCESSING")
        except Exception as e:
            print(f"⚠️ Erro ao conectar com banco: {e}. Continuando sem banco...")
            use_db = False
    
    try:
        # Gerar script
        response = generate_script(topic)
        print("script: {}".format(response))
        
        # Atualizar script no banco se estiver usando
        if use_db and video_id:
            await db.update_video_status(video_id, "PROCESSING")
        
        # Gerar áudio
        SAMPLE_FILE_NAME = f"audio_tts_{video_id}.wav" if video_id else "audio_tts.wav"
        asyncio.run(generate_audio(response, SAMPLE_FILE_NAME))
        
        # Gerar legendas
        timed_captions = generate_timed_captions(SAMPLE_FILE_NAME)
        print(timed_captions)
        
        # Gerar termos de busca
        search_terms = getVideoSearchQueriesTimed(response, timed_captions)
        print(search_terms)
        
        # Gerar vídeos de fundo
        VIDEO_SERVER = "pexel"
        background_video_urls = None
        if search_terms is not None:
            background_video_urls = generate_video_url(search_terms, VIDEO_SERVER)
            print(background_video_urls)
        else:
            print("No background video")
        
        background_video_urls = merge_empty_intervals(background_video_urls)
        
        # Renderizar vídeo final
        if background_video_urls is not None:
            output_video = get_output_media(SAMPLE_FILE_NAME, timed_captions, background_video_urls, VIDEO_SERVER)
            print(f"Vídeo renderizado: {output_video}")
            
            # Atualizar banco com caminhos dos arquivos
            if use_db and video_id:
                await db.update_video_status(
                    video_id=video_id,
                    status="COMPLETED",
                    audio_path=SAMPLE_FILE_NAME,
                    video_path=output_video,
                    duration=42.5  # Você pode calcular a duração real
                )
                print(f"✅ Vídeo '{topic}' gerado com sucesso!")
                print(f"📁 Arquivo: {output_video}")
                print(f"🆔 ID no banco: {video_id}")
            else:
                print(f"✅ Vídeo '{topic}' gerado com sucesso!")
                print(f"📁 Arquivo: {output_video}")
            
        else:
            if use_db and video_id:
                await db.update_video_status(video_id, "FAILED")
            print("❌ Falha ao gerar vídeo")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        if use_db and video_id:
            await db.update_video_status(video_id, "FAILED")
    
    finally:
        if db:
            await db.disconnect()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a video from a topic.")
    parser.add_argument("topic", type=str, help="The topic for the video")
    parser.add_argument("--credentials", type=str, default="default", help="Credentials name to use")
    parser.add_argument("--no-db", action="store_true", help="Disable database integration")

    args = parser.parse_args()
    
    use_db = not args.no_db
    asyncio.run(generate_video_with_db(args.topic, args.credentials, use_db))