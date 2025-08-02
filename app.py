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
from utility.templates.template_manager import TemplateManager
from utility.render.template_render_engine import TemplateRenderEngine
import argparse

# Importar banco de dados apenas quando necessário
try:
    from database import VideoDatabase
    DB_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Banco de dados não disponível: {e}")
    DB_AVAILABLE = False

async def generate_video_with_template(topic: str, template_id: str = None, credentials_name: str = "default", use_db: bool = True):
    """Gera vídeo com template aplicado"""
    
    print(f"🎬 INICIANDO GERAÇÃO DE VÍDEO")
    print(f"📝 Tópico: {topic}")
    print(f"🎨 Template: {template_id or 'Automático'}")
    print("="*60)
    
    # Inicializar sistema de templates
    template_manager = TemplateManager()
    template_render_engine = TemplateRenderEngine()
    
    # Auto-detect template se não especificado
    if not template_id:
        recommendations = template_render_engine.get_template_recommendations(topic)
        if recommendations:
            template_id = recommendations[0]['template_id']
            print(f"🎯 Template auto-detectado: {recommendations[0]['name']}")
        else:
            print("⚠️ Nenhum template adequado encontrado, usando geração padrão")
    
    db = None
    video_id = None
    
    if use_db and DB_AVAILABLE:
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
        # Aplicar template se especificado
        if template_id:
            print(f"🎨 APLICANDO TEMPLATE: {template_id}")
            template = template_manager.get_template(template_id)
            if template:
                # Aplicar configurações do template
                template_render_engine.apply_template_to_video(
                    video_path="",  # Será definido depois
                    template_id=template_id,
                    script="",  # Será definido depois
                    audio_path=""  # Será definido depois
                )
            else:
                print(f"⚠️ Template {template_id} não encontrado, usando geração padrão")
        
        # Gerar script
        response = generate_script(topic)
        print("📝 Script gerado: {}".format(response))
        
        # Atualizar script no banco se estiver usando
        if use_db and video_id:
            await db.update_video_status(video_id, "PROCESSING")
        
        # Gerar áudio
        SAMPLE_FILE_NAME = f"audio_tts_{video_id}.wav" if video_id else "audio_tts.wav"
        await generate_audio(response, SAMPLE_FILE_NAME)
        print(f"🎵 Áudio gerado: {SAMPLE_FILE_NAME}")
        
        # Gerar legendas
        timed_captions = generate_timed_captions(SAMPLE_FILE_NAME)
        print(f"📝 Legendas temporizadas: {len(timed_captions)} segmentos")
        
        # Gerar termos de busca
        search_terms = getVideoSearchQueriesTimed(response, timed_captions)
        print(f"🔍 Termos de busca: {search_terms}")
        
        # Gerar vídeos de fundo
        VIDEO_SERVER = "pexel"
        background_video_urls = None
        if search_terms is not None:
            background_video_urls = generate_video_url(search_terms, VIDEO_SERVER)
            print(f"🎬 Vídeos de fundo: {len(background_video_urls) if background_video_urls else 0} encontrados")
        else:
            print("⚠️ Nenhum vídeo de fundo encontrado")
        
        if background_video_urls is not None:
            background_video_urls = merge_empty_intervals(background_video_urls)
        
        # Renderizar vídeo final
        if background_video_urls is not None:
            print("🎬 Iniciando renderização com template...")
            output_video = get_output_media(SAMPLE_FILE_NAME, timed_captions, background_video_urls, VIDEO_SERVER)
            print(f"✅ Vídeo renderizado: {output_video}")
            
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
            print("❌ Falha ao gerar vídeo - nenhum vídeo de fundo disponível")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        if use_db and video_id:
            await db.update_video_status(video_id, "FAILED")
    
    finally:
        if db:
            await db.disconnect()

async def generate_video_with_db(topic: str, credentials_name: str = "default", use_db: bool = True):
    """Gera vídeo e salva no banco de dados (método original)"""
    
    db = None
    video_id = None
    
    if use_db and DB_AVAILABLE:
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
        await generate_audio(response, SAMPLE_FILE_NAME)
        
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
        
        if background_video_urls is not None:
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
    parser.add_argument("topic", nargs='?', type=str, help="The topic for the video")
    parser.add_argument("--credentials", type=str, default="default", help="Credentials name to use")
    parser.add_argument("--no-db", action="store_true", help="Disable database integration")
    parser.add_argument("--template", type=str, help="Template ID to use for video generation")
    parser.add_argument("--list-templates", action="store_true", help="List available templates")
    parser.add_argument("--suggest", type=str, help="Get template suggestions for a topic")
    parser.add_argument("--preview", type=str, help="Preview template assets")

    args = parser.parse_args()
    
    use_db = not args.no_db and DB_AVAILABLE
    
    # Listar templates
    if args.list_templates:
        template_manager = TemplateManager()
        templates = template_manager.list_templates()
        print("🎨 TEMPLATES DISPONÍVEIS:")
        print("="*50)
        for template in templates:
            print(f"   • {template['name']} ({template['id']})")
            print(f"     {template['description']}")
            print()
        exit(0)
    
    # Sugerir templates
    if args.suggest:
        template_render_engine = TemplateRenderEngine()
        recommendations = template_render_engine.get_template_recommendations(args.suggest)
        print(f"🎯 SUGESTÕES PARA: {args.suggest}")
        print("="*50)
        for rec in recommendations:
            print(f"   • {rec['name']} (Score: {rec['score']})")
            print(f"     {rec['description']}")
            print(f"     Assets prontos: {rec['assets_ready']}")
            for reason in rec['reasons']:
                print(f"     - {reason}")
            print()
        exit(0)
    
    # Preview de template
    if args.preview:
        template_render_engine = TemplateRenderEngine()
        preview = template_render_engine.preview_template_assets(args.preview)
        if 'error' not in preview:
            print(f"🔍 PREVIEW DO TEMPLATE: {preview['template_name']}")
            print("="*50)
            print(f"Seções: {len(preview['sections'])}")
            for asset_type, count in preview['total_assets'].items():
                print(f"{asset_type}: {count}")
        else:
            print(f"❌ {preview['error']}")
        exit(0)
    
    # Verificar se tópico é obrigatório para geração
    if not args.topic:
        print("❌ Tópico é obrigatório para geração de vídeo!")
        parser.print_help()
        exit(1)
    
    # Gerar vídeo com template se especificado
    if args.template:
        asyncio.run(generate_video_with_template(args.topic, args.template, args.credentials, use_db))
    else:
        asyncio.run(generate_video_with_db(args.topic, args.credentials, use_db))