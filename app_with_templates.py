from openai import OpenAI
import os
import edge_tts
import json
import asyncio
import whisper_timestamped as whisper
import argparse
from utility.script.script_generator import generate_script
from utility.audio.audio_generator import generate_audio
from utility.captions.timed_captions_generator import generate_timed_captions
from utility.video.background_video_generator import generate_video_url
from utility.render.render_engine import get_output_media
from utility.video.video_search_query_generator import getVideoSearchQueriesTimed, merge_empty_intervals

# Importar sistema de templates
from utility.templates.template_manager import TemplateManager
from utility.script.template_script_generator import TemplateScriptGenerator
from utility.render.template_render_engine import TemplateRenderEngine

# Importar banco de dados apenas quando necessário
try:
    from database import VideoDatabase
    DB_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Banco de dados não disponível: {e}")
    DB_AVAILABLE = False

async def generate_video_with_template(topic: str, template_id: str = None, credentials_name: str = "default", use_db: bool = True):
    """Gera vídeo usando sistema de templates"""
    
    print(f"🎬 GERANDO VÍDEO COM TEMPLATES")
    print(f"📝 Tópico: {topic}")
    print(f"🎨 Template: {template_id or 'Auto-detectado'}")
    print("="*60)
    
    # Inicializar sistema de templates
    template_engine = TemplateRenderEngine()
    template_script_generator = TemplateScriptGenerator()
    
    # Se não especificou template, usar sugestão automática
    if not template_id:
        suggestions = template_script_generator.get_template_suggestions(topic)
        if suggestions:
            template_id = suggestions[0]['template_id']
            print(f"✅ Template sugerido: {suggestions[0]['name']}")
        else:
            print("⚠️ Nenhum template encontrado, usando geração padrão")
            template_id = None
    
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
        # Gerar script usando template ou método padrão
        if template_id:
            print(f"🎨 Usando template: {template_id}")
            script_result = template_script_generator.generate_script_with_pauses(topic, template_id)
            if 'error' in script_result:
                print(f"❌ Erro no template: {script_result['error']}")
                print("🔄 Usando geração padrão...")
                response = generate_script(topic)
            else:
                response = script_result['script']
                print(f"✅ Script gerado com template: {len(response.split())} palavras")
        else:
            print("📝 Usando geração padrão de script")
            response = generate_script(topic)
        
        print(f"📝 Script: {response}")
        
        # Atualizar script no banco se estiver usando
        if use_db and video_id:
            await db.update_video_status(video_id, "PROCESSING")
        
        # Gerar áudio
        SAMPLE_FILE_NAME = f"audio_tts_{video_id}.wav" if video_id else "audio_tts.wav"
        await generate_audio(response, SAMPLE_FILE_NAME)
        
        # Gerar legendas
        timed_captions = generate_timed_captions(SAMPLE_FILE_NAME)
        print(f"📝 Legendas geradas: {len(timed_captions)} segmentos")
        
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
            print("❌ Falha ao gerar vídeo - sem vídeos de fundo")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        if use_db and video_id:
            await db.update_video_status(video_id, "FAILED")
    
    finally:
        if db:
            await db.disconnect()

def list_templates():
    """Lista todos os templates disponíveis"""
    template_manager = TemplateManager()
    templates = template_manager.list_templates()
    
    print("📋 TEMPLATES DISPONÍVEIS:")
    print("="*50)
    for i, template in enumerate(templates, 1):
        print(f"{i}. {template['name']}")
        print(f"   Descrição: {template['description']}")
        print(f"   Versão: {template['version']}")
        print()
    
    return templates

def suggest_template(topic: str):
    """Sugere template para um tópico"""
    template_script_generator = TemplateScriptGenerator()
    suggestions = template_script_generator.get_template_suggestions(topic)
    
    print(f"🎯 SUGESTÕES PARA: {topic}")
    print("="*50)
    for i, suggestion in enumerate(suggestions, 1):
        print(f"{i}. {suggestion['name']} (Score: {suggestion['score']})")
        print(f"   Descrição: {suggestion['description']}")
        for reason in suggestion['reasons']:
            print(f"   • {reason}")
        print()
    
    return suggestions

def preview_template(template_id: str):
    """Mostra preview de um template"""
    template_engine = TemplateRenderEngine()
    preview = template_engine.preview_template_assets(template_id)
    
    if 'error' in preview:
        print(f"❌ {preview['error']}")
        return
    
    print(f"🔍 PREVIEW DO TEMPLATE: {preview['template_name']}")
    print("="*50)
    print(f"Seções: {len(preview['sections'])}")
    for asset_type, count in preview['total_assets'].items():
        print(f"Assets de {asset_type}: {count}")
    
    print("\n📋 SEÇÕES:")
    for section_name, section_data in preview['sections'].items():
        print(f"• {section_name}:")
        print(f"  - Tom: {section_data['tone']}")
        print(f"  - Estilo: {section_data['visual_style']}")
        print(f"  - Duração: {section_data['duration']}")
        for asset_type, count in section_data['assets'].items():
            if count > 0:
                print(f"  - {asset_type}: {count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a video from a topic using templates.")
    parser.add_argument("topic", nargs='?', type=str, help="The topic for the video")
    parser.add_argument("--template", type=str, help="Template ID to use")
    parser.add_argument("--credentials", type=str, default="default", help="Credentials name to use")
    parser.add_argument("--no-db", action="store_true", help="Disable database integration")
    parser.add_argument("--list-templates", action="store_true", help="List available templates")
    parser.add_argument("--suggest", action="store_true", help="Suggest templates for topic")
    parser.add_argument("--preview", type=str, help="Preview a specific template")

    args = parser.parse_args()
    
    if args.list_templates:
        list_templates()
    elif args.suggest and args.topic:
        suggest_template(args.topic)
    elif args.preview:
        preview_template(args.preview)
    elif args.topic:
        use_db = not args.no_db and DB_AVAILABLE
        asyncio.run(generate_video_with_template(args.topic, args.template, args.credentials, use_db))
    else:
        print("❌ Tópico é obrigatório para gerar vídeo!")
        print("💡 Use --list-templates para ver templates disponíveis")
        print("💡 Use --suggest 'tópico' para sugestões")
        print("💡 Use --preview 'template_id' para preview") 