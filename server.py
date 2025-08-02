#!/usr/bin/env python3
"""
Servidor Web para Text-to-Video AI
Gerencia criação, status e visualização de vídeos
"""

import os
import asyncio
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
from flask_socketio import SocketIO, emit
import threading
import time

# Importar módulos do projeto
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

# Importar banco de dados (opcional)
try:
    from database import VideoDatabase
    DB_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Banco de dados não disponível: {e}")
    DB_AVAILABLE = False

app = Flask(__name__)
app.config['SECRET_KEY'] = 'textoemvideos_secret_key_2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# Armazenamento temporário de jobs (se não houver banco)
jobs = {}
completed_videos = {}

# Inicializar sistema de templates
template_manager = TemplateManager()
template_script_generator = TemplateScriptGenerator()
template_render_engine = TemplateRenderEngine()

class VideoJob:
    def __init__(self, topic, user_id=None, template_id=None):
        self.id = str(uuid.uuid4())
        self.topic = topic
        self.user_id = user_id
        self.template_id = template_id
        self.status = "PENDING"
        self.progress = 0
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.video_path = None
        self.audio_path = None
        self.duration = None
        self.error = None

    def to_dict(self):
        return {
            'id': self.id,
            'topic': self.topic,
            'template_id': self.template_id,
            'status': self.status,
            'progress': self.progress,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'video_path': self.video_path,
            'audio_path': self.audio_path,
            'duration': self.duration,
            'error': self.error
        }

def update_job_progress(job_id, progress, status=None):
    """Atualiza progresso do job e notifica via WebSocket"""
    if job_id in jobs:
        jobs[job_id].progress = progress
        if status:
            jobs[job_id].status = status
        jobs[job_id].updated_at = datetime.now()
        
        # Emitir atualização via WebSocket
        socketio.emit('job_update', {
            'job_id': job_id,
            'progress': progress,
            'status': jobs[job_id].status
        })

async def generate_video_async(job_id, topic, template_id=None, use_db=False):
    """Gera vídeo de forma assíncrona com suporte a templates"""
    try:
        job = jobs[job_id]
        update_job_progress(job_id, 10, "PROCESSING")
        
        # Verificar se as variáveis de ambiente estão configuradas
        if not os.environ.get("GROQ_API_KEY"):
            raise Exception("GROQ_API_KEY não configurada. Configure a variável de ambiente.")
        if not os.environ.get("PEXELS_KEY"):
            raise Exception("PEXELS_KEY não configurada. Configure a variável de ambiente.")
        
        # 1. Gerar script (com ou sem template)
        update_job_progress(job_id, 20)
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
        
        print(f"Script gerado: {response[:100]}...")
        
        # 3. Gerar áudio
        update_job_progress(job_id, 40)
        audio_filename = f"audio_tts_{job_id}.wav"
        await generate_audio(response, audio_filename)
        print(f"Áudio gerado: {audio_filename}")
        
        # 4. Gerar legendas
        update_job_progress(job_id, 50)
        timed_captions = generate_timed_captions(audio_filename)
        print(f"Legendas geradas: {len(timed_captions)} segmentos")
        
        # 4.5. Aplicar template com timestamps reais se especificado
        if template_id:
            print(f"🎨 APLICANDO TEMPLATE COM TIMESTAMPS REAIS: {template_id}")
            template = template_manager.get_template(template_id)
            if template:
                # Aplicar configurações do template usando timestamps reais
                template_render_engine.apply_template_to_video(
                    video_path="",  # Será definido depois
                    template_id=template_id,
                    script=response,  # Script já gerado
                    audio_path=audio_filename  # Áudio já gerado
                )
                print(f"✅ Template {template_id} aplicado com timestamps reais!")
            else:
                print(f"⚠️ Template {template_id} não encontrado, usando geração padrão")
        
        # 5. Gerar termos de busca
        update_job_progress(job_id, 60)
        search_terms = getVideoSearchQueriesTimed(response, timed_captions)
        print(f"Termos de busca gerados: {len(search_terms) if search_terms else 0}")
        
        # 6. Buscar vídeos de fundo
        update_job_progress(job_id, 70)
        background_video_urls = None
        if search_terms:
            background_video_urls = generate_video_url(search_terms, "pexel")
            if background_video_urls:
                background_video_urls = merge_empty_intervals(background_video_urls)
                print(f"Vídeos de fundo encontrados: {len(background_video_urls)}")
            else:
                print("Nenhum vídeo de fundo encontrado")
        
        # 7. Renderizar vídeo final (com template aplicado)
        update_job_progress(job_id, 80)
        if background_video_urls:
            print("🎬 Iniciando renderização com template...")
            output_video = get_output_media(audio_filename, timed_captions, background_video_urls, "pexel")
            print(f"Vídeo renderizado: {output_video}")
            
            # Atualizar job com sucesso
            job.video_path = output_video
            job.audio_path = audio_filename
            job.duration = 42.5  # Duração estimada
            update_job_progress(job_id, 100, "COMPLETED")
            
            # Salvar no banco se disponível
            if use_db and DB_AVAILABLE:
                try:
                    db = VideoDatabase()
                    await db.connect()
                    await db.update_video_status(
                        video_id=job_id,
                        status="COMPLETED",
                        audio_path=audio_filename,
                        video_path=output_video,
                        duration=42.5
                    )
                    await db.disconnect()
                except Exception as e:
                    print(f"⚠️ Erro ao salvar no banco: {e}")
            
            # Emitir evento de conclusão
            socketio.emit('job_completed', {
                'job_id': job_id,
                'video_path': output_video,
                'duration': 42.5
            })
            
        else:
            raise Exception("Não foi possível encontrar vídeos de fundo adequados")
            
    except Exception as e:
        print(f"❌ Erro na geração: {e}")
        job.error = str(e)
        update_job_progress(job_id, 0, "FAILED")
        
        # Salvar erro no banco se disponível
        if use_db and DB_AVAILABLE:
            try:
                db = VideoDatabase()
                await db.connect()
                await db.update_video_status(job_id, "FAILED")
                await db.disconnect()
            except Exception as db_error:
                print(f"⚠️ Erro ao salvar erro no banco: {db_error}")
        
        # Emitir evento de falha
        socketio.emit('job_failed', {
            'job_id': job_id,
            'error': str(e)
        })

def run_async_generation(job_id, topic, template_id=None, use_db=False):
    """Executa geração de vídeo em thread separada"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(generate_video_async(job_id, topic, template_id, use_db))
    finally:
        loop.close()

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """Lista todos os jobs"""
    try:
        if DB_AVAILABLE:
            # Tentar carregar do banco de dados
            async def load_db_videos():
                try:
                    db = VideoDatabase()
                    await db.connect()
                    videos = await db.list_videos()
                    await db.disconnect()
                    return videos
                except Exception as e:
                    print(f"⚠️ Erro ao carregar do banco: {e}")
                    return []
            
            def run_async_load():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(load_db_videos())
                finally:
                    loop.close()
            
            # Executar em thread separada para evitar conflito com Flask
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_async_load)
                videos = future.result()
            
            # Converter para formato compatível
            jobs_list = []
            for video in videos:
                job_dict = {
                    'id': str(video.id),
                    'topic': video.topic,
                    'status': video.status,
                    'progress': 100 if video.status == "COMPLETED" else 0,
                    'created_at': video.created_at.isoformat() if hasattr(video, 'created_at') else datetime.now().isoformat(),
                    'updated_at': video.updated_at.isoformat() if hasattr(video, 'updated_at') else datetime.now().isoformat(),
                    'video_path': video.video_path,
                    'audio_path': video.audio_path,
                    'duration': video.duration
                }
                jobs_list.append(job_dict)
            
            return jsonify(jobs_list)
        else:
            # Usar jobs em memória
            return jsonify([job.to_dict() for job in jobs.values()])
    except Exception as e:
        print(f"❌ Erro ao listar jobs: {e}")
        return jsonify([])

@app.route('/api/jobs', methods=['POST'])
def create_job():
    """Cria um novo job de geração de vídeo"""
    try:
        data = request.get_json()
        topic = data.get('topic', '').strip()
        template_id = data.get('template_id')  # Novo campo para template
        
        if not topic:
            return jsonify({'error': 'Tópico é obrigatório'}), 400
        
        # Criar job
        job = VideoJob(topic=topic, template_id=template_id)
        jobs[job.id] = job
        
        # Salvar no banco se disponível
        use_db = DB_AVAILABLE
        if use_db:
            try:
                async def save_to_db():
                    db = VideoDatabase()
                    await db.connect()
                    video = await db.create_video(
                        title=f"Vídeo sobre {topic}",
                        topic=topic,
                        script="",
                        credentials_id=1  # Usar credenciais padrão
                    )
                    await db.update_video_status(video.id, "PENDING")
                    await db.disconnect()
                    return video.id
                
                def run_async_save():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        return loop.run_until_complete(save_to_db())
                    finally:
                        loop.close()
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_async_save)
                    db_job_id = future.result()
                    job.id = str(db_job_id)  # Usar ID do banco
            except Exception as e:
                print(f"⚠️ Erro ao salvar no banco: {e}")
                use_db = False
        
        # Iniciar geração em thread separada
        thread = threading.Thread(
            target=run_async_generation,
            args=(job.id, topic, template_id, use_db)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'job_id': job.id,
            'topic': topic,
            'template_id': template_id,
            'status': 'PENDING'
        })
        
    except Exception as e:
        print(f"❌ Erro ao criar job: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    """Obtém status de um job específico"""
    if job_id in jobs:
        return jsonify(jobs[job_id].to_dict())
    else:
        return jsonify({'error': 'Job não encontrado'}), 404

@app.route('/api/videos/<job_id>', methods=['GET'])
def download_video(job_id):
    """Download do vídeo gerado"""
    if job_id in jobs:
        job = jobs[job_id]
        if job.video_path and os.path.exists(job.video_path):
            return send_file(job.video_path, as_attachment=True)
        else:
            return jsonify({'error': 'Vídeo não encontrado'}), 404
    else:
        return jsonify({'error': 'Job não encontrado'}), 404

@app.route('/gallery')
def gallery():
    """Página da galeria de vídeos"""
    return render_template('gallery.html')

@app.route('/status/<job_id>')
def status_page(job_id):
    """Página de status de um job"""
    return render_template('status.html', job_id=job_id)

@app.route('/api/templates', methods=['GET'])
def list_templates():
    """Lista todos os templates disponíveis"""
    try:
        templates = template_manager.list_templates()
        return jsonify(templates)
    except Exception as e:
        print(f"❌ Erro ao listar templates: {e}")
        return jsonify([])

@app.route('/api/templates/suggest', methods=['POST'])
def suggest_templates():
    """Sugere templates para um tópico"""
    try:
        data = request.get_json()
        topic = data.get('topic', '').strip()
        
        if not topic:
            return jsonify({'error': 'Tópico é obrigatório'}), 400
        
        suggestions = template_script_generator.get_template_suggestions(topic)
        return jsonify(suggestions)
    except Exception as e:
        print(f"❌ Erro ao sugerir templates: {e}")
        return jsonify([])

@app.route('/api/chat', methods=['POST'])
def chat_with_ai():
    """Chat com IA para sugestões de tópicos"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'error': 'Mensagem é obrigatória'}), 400
        
        # Verificar se a API key está configurada
        if not os.environ.get("GROQ_API_KEY"):
            return jsonify({'error': 'GROQ_API_KEY não configurada'}), 500
        
        # Gerar resposta usando Groq
        from groq import Groq
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        
        prompt = f"""Você é um assistente especializado em sugestões de conteúdo para vídeos curtos.
        O usuário está pedindo sugestões de tópicos para vídeos de fatos curiosos, histórias interessantes, 
        ou conteúdo educativo. Responda com 3-5 sugestões criativas e envolventes.
        
        Mensagem do usuário: {message}
        
        Responda apenas com as sugestões, uma por linha, sem numeração."""
        
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": message}
            ],
            max_tokens=200,
            temperature=0.8
        )
        
        suggestions = response.choices[0].message.content.strip().split('\n')
        suggestions = [s.strip() for s in suggestions if s.strip()]
        
        return jsonify({
            'suggestions': suggestions,
            'message': message
        })
        
    except Exception as e:
        print(f"❌ Erro no chat: {e}")
        return jsonify({'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    """Cliente conectado"""
    print(f"Cliente conectado: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """Cliente desconectado"""
    print(f"Cliente desconectado: {request.sid}")

@socketio.on('subscribe_job')
def handle_subscribe_job(data):
    """Cliente se inscreve para atualizações de um job"""
    job_id = data.get('job_id')
    if job_id:
        print(f"Cliente {request.sid} inscrito para job {job_id}")

if __name__ == '__main__':
    print("🚀 Iniciando servidor Text-to-Video AI...")
    print(f"📋 Templates carregados: {len(template_manager.list_templates())}")
    print(f"🗄️ Banco de dados: {'Disponível' if DB_AVAILABLE else 'Não disponível'}")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True) 