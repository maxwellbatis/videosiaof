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

class VideoJob:
    def __init__(self, topic, user_id=None):
        self.id = str(uuid.uuid4())
        self.topic = topic
        self.user_id = user_id
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

async def generate_video_async(job_id, topic, use_db=False):
    """Gera vídeo de forma assíncrona"""
    try:
        job = jobs[job_id]
        update_job_progress(job_id, 10, "PROCESSING")
        
        # Verificar se as variáveis de ambiente estão configuradas
        if not os.environ.get("GROQ_API_KEY"):
            raise Exception("GROQ_API_KEY não configurada. Configure a variável de ambiente.")
        if not os.environ.get("PEXELS_KEY"):
            raise Exception("PEXELS_KEY não configurada. Configure a variável de ambiente.")
        
        # 1. Gerar script
        update_job_progress(job_id, 20)
        response = generate_script(topic)
        print(f"Script gerado: {response[:100]}...")
        
        # 2. Gerar áudio
        update_job_progress(job_id, 40)
        audio_file = f"audio_tts_{job_id}.wav"
        await generate_audio(response, audio_file)
        job.audio_path = audio_file
        print(f"Áudio gerado: {audio_file}")
        
        # 3. Gerar legendas
        update_job_progress(job_id, 60)
        timed_captions = generate_timed_captions(audio_file)
        print(f"Legendas geradas: {len(timed_captions)} segmentos")
        
        # 4. Gerar termos de busca
        update_job_progress(job_id, 70)
        search_terms = getVideoSearchQueriesTimed(response, timed_captions)
        print(f"Termos de busca gerados: {len(search_terms) if search_terms else 0}")
        
        # 5. Gerar vídeos de fundo
        update_job_progress(job_id, 80)
        background_video_urls = None
        if search_terms:
            background_video_urls = generate_video_url(search_terms, "pexel")
            background_video_urls = merge_empty_intervals(background_video_urls)
        print(f"Vídeos de fundo: {len(background_video_urls) if background_video_urls else 0}")
        
        # 6. Renderizar vídeo final
        update_job_progress(job_id, 90)
        if background_video_urls:
            output_video = get_output_media(audio_file, timed_captions, background_video_urls, "pexel")
            job.video_path = output_video
            job.status = "COMPLETED"
            job.duration = 47.0  # Aproximado
            print(f"Vídeo renderizado: {output_video}")
            
            # Mover para completed_videos
            completed_videos[job_id] = job.to_dict()
            
            update_job_progress(job_id, 100, "COMPLETED")
            socketio.emit('job_completed', {'job_id': job_id, 'video_path': output_video})
        else:
            raise Exception("Não foi possível gerar vídeos de fundo")
            
    except Exception as e:
        print(f"❌ Erro na geração do vídeo: {e}")
        job.status = "FAILED"
        job.error = str(e)
        update_job_progress(job_id, 0, "FAILED")
        socketio.emit('job_failed', {'job_id': job_id, 'error': str(e)})

def run_async_generation(job_id, topic, use_db=False):
    """Executa geração de vídeo em thread separada"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(generate_video_async(job_id, topic, use_db))
    finally:
        loop.close()

# Rotas da aplicação

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """Lista todos os jobs"""
    all_jobs = {**jobs, **completed_videos}
    return jsonify({
        'jobs': [job.to_dict() if hasattr(job, 'to_dict') else job for job in all_jobs.values()]
    })

@app.route('/api/jobs', methods=['POST'])
def create_job():
    """Cria um novo job de geração de vídeo"""
    data = request.get_json()
    topic = data.get('topic', '').strip()
    
    if not topic:
        return jsonify({'error': 'Tópico é obrigatório'}), 400
    
    # Criar novo job
    job = VideoJob(topic)
    jobs[job.id] = job
    
    # Iniciar geração em thread separada
    thread = threading.Thread(
        target=run_async_generation,
        args=(job.id, topic, DB_AVAILABLE)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'job_id': job.id,
        'message': 'Job criado com sucesso',
        'status': job.status
    }), 201

@app.route('/api/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    """Obtém status de um job específico"""
    all_jobs = {**jobs, **completed_videos}
    
    if job_id not in all_jobs:
        return jsonify({'error': 'Job não encontrado'}), 404
    
    job = all_jobs[job_id]
    return jsonify(job.to_dict() if hasattr(job, 'to_dict') else job)

@app.route('/api/videos/<job_id>', methods=['GET'])
def download_video(job_id):
    """Download do vídeo gerado"""
    if job_id not in completed_videos:
        return jsonify({'error': 'Vídeo não encontrado'}), 404
    
    video_data = completed_videos[job_id]
    video_path = video_data.get('video_path')
    
    if not video_path or not os.path.exists(video_path):
        return jsonify({'error': 'Arquivo de vídeo não encontrado'}), 404
    
    return send_file(video_path, as_attachment=True)

@app.route('/gallery')
def gallery():
    """Página da galeria de vídeos"""
    return render_template('gallery.html', videos=completed_videos)

@app.route('/status/<job_id>')
def status_page(job_id):
    """Página de status de um job específico"""
    return render_template('status.html', job_id=job_id)

# WebSocket events

@socketio.on('connect')
def handle_connect():
    print('Cliente conectado')

@socketio.on('disconnect')
def handle_disconnect():
    print('Cliente desconectado')

@socketio.on('subscribe_job')
def handle_subscribe_job(data):
    """Inscreve cliente para atualizações de um job"""
    job_id = data.get('job_id')
    if job_id in jobs:
        emit('job_update', jobs[job_id].to_dict())

if __name__ == '__main__':
    print("🚀 Iniciando servidor Text-to-Video AI...")
    print("📱 Interface web disponível em: http://localhost:5000")
    print("🎬 API disponível em: http://localhost:5000/api")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True) 