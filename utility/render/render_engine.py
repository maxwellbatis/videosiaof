import time
import os
import tempfile
import zipfile
import platform
import subprocess
import json
from pathlib import Path
from moviepy.editor import (AudioFileClip, CompositeVideoClip, CompositeAudioClip, ImageClip,
                            TextClip, VideoFileClip)
from moviepy.audio.fx.audio_loop import audio_loop
from moviepy.audio.fx.audio_normalize import audio_normalize
import requests

def download_file(url, filename):
    with open(filename, 'wb') as f:
        headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        f.write(response.content)

def search_program(program_name):
    try: 
        search_cmd = "where" if platform.system() == "Windows" else "which"
        return subprocess.check_output([search_cmd, program_name]).decode().strip()
    except subprocess.CalledProcessError:
        return None

def get_program_path(program_name):
    program_path = search_program(program_name)
    return program_path

def load_template_configs():
    """Carrega configurações de template se disponíveis"""
    configs = {}
    
    # Carregar configurações visuais
    visual_config_file = Path(__file__).parent.parent.parent / "temp_visual_config.json"
    if visual_config_file.exists():
        try:
            with open(visual_config_file, 'r', encoding='utf-8') as f:
                configs['visual'] = json.load(f)
            print("✅ Configurações visuais do template carregadas")
        except Exception as e:
            print(f"⚠️ Erro ao carregar configurações visuais: {e}")
    
    # Carregar configurações de áudio
    audio_config_file = Path(__file__).parent.parent.parent / "temp_audio_config.json"
    if audio_config_file.exists():
        try:
            with open(audio_config_file, 'r', encoding='utf-8') as f:
                configs['audio'] = json.load(f)
            print("✅ Configurações de áudio do template carregadas")
        except Exception as e:
            print(f"⚠️ Erro ao carregar configurações de áudio: {e}")
    
    # Carregar configurações de pausas
    pauses_config_file = Path(__file__).parent.parent.parent / "temp_pauses_config.json"
    if pauses_config_file.exists():
        try:
            with open(pauses_config_file, 'r', encoding='utf-8') as f:
                configs['pauses'] = json.load(f)
            print("✅ Configurações de pausas do template carregadas")
        except Exception as e:
            print(f"⚠️ Erro ao carregar configurações de pausas: {e}")
    
    # Carregar configurações de efeitos
    effects_config_file = Path(__file__).parent.parent.parent / "temp_effects_config.json"
    if effects_config_file.exists():
        try:
            with open(effects_config_file, 'r', encoding='utf-8') as f:
                configs['effects'] = json.load(f)
            print("✅ Configurações de efeitos do template carregadas")
        except Exception as e:
            print(f"⚠️ Erro ao carregar configurações de efeitos: {e}")
    
    return configs

def apply_template_effects_to_audio(audio_clip, template_configs):
    """Aplica efeitos de áudio do template"""
    if 'audio' not in template_configs:
        return audio_clip
    
    audio_config = template_configs['audio']
    
    # Aplicar volume do template
    volume = audio_config.get('volume', 1.0)
    if volume != 1.0:
        audio_clip = audio_clip.volumex(volume)
        print(f"🎵 Aplicado volume do template: {volume}")
    
    # Aplicar efeitos sonoros se disponíveis
    if 'effects' in template_configs:
        effects_config = template_configs['effects']
        audio_effects = []
        
        for section_name, section_data in effects_config.items():
            assets = section_data.get('assets', {})
            audio_effects.extend(assets.get('audio_effects', []))
        
        effects_volume = audio_config.get('effects_volume', 0.5)
        if audio_effects:
            print(f"🎵 Aplicando {len(audio_effects)} efeitos sonoros do template")
            # Aplicar efeitos sonoros reais
            for effect_path in audio_effects:
                if os.path.exists(effect_path):
                    try:
                        effect_clip = AudioFileClip(effect_path)
                        # Aplicar efeito com volume reduzido
                        effect_clip = effect_clip.volumex(effects_volume)
                        # Combinar com áudio principal
                        audio_clip = CompositeAudioClip([audio_clip, effect_clip])
                        print(f"   ✅ Efeito aplicado: {effect_path}")
                    except Exception as e:
                        print(f"   ❌ Erro ao aplicar efeito {effect_path}: {e}")
                else:
                    print(f"   ❌ Efeito não encontrado: {effect_path}")
    
    return audio_clip

def apply_strategic_pauses(audio_clip, pauses_config):
    """Aplica pausas estratégicas ao áudio"""
    print(f"⏱️ Aplicando {len(pauses_config)} pausas estratégicas")
    
    # Ordenar pausas por posição
    sorted_pauses = sorted(pauses_config, key=lambda x: x.get('position', 0))
    
    # Criar clips de áudio com pausas
    audio_clips = []
    current_time = 0
    
    for pause in sorted_pauses:
        pause_position = pause.get('position', 0)
        pause_duration = pause.get('duration', 0)
        
        # Adicionar áudio até a pausa
        if pause_position > current_time:
            segment = audio_clip.subclip(current_time, pause_position)
            audio_clips.append(segment)
        
        # Adicionar pausa (silêncio)
        if pause_duration > 0:
            from moviepy.audio.AudioClip import AudioClip
            silence = AudioClip(lambda t: 0, duration=pause_duration)
            audio_clips.append(silence)
            print(f"   ⏸️ Pausa em {pause_position:.1f}s por {pause_duration:.1f}s: {pause.get('description', '')}")
        
        current_time = pause_position + pause_duration
    
    # Adicionar o resto do áudio
    if current_time < audio_clip.duration:
        final_segment = audio_clip.subclip(current_time, audio_clip.duration)
        audio_clips.append(final_segment)
    
    # Combinar todos os clips
    if audio_clips:
        return CompositeAudioClip(audio_clips)
    else:
        return audio_clip

def apply_template_effects_to_video(video_clip, template_configs):
    """Aplica efeitos visuais do template"""
    if 'effects' not in template_configs:
        return video_clip
    
    effects_config = template_configs['effects']
    video_effects = []
    
    # Coletar todos os efeitos de vídeo do template
    for section_name, section_data in effects_config.items():
        assets = section_data.get('assets', {})
        video_effects.extend(assets.get('video_effects', []))
    
    if video_effects:
        print(f"🎬 Aplicando {len(video_effects)} efeitos visuais do template")
        # Aplicar efeitos visuais reais
        for effect_path in video_effects:
            if os.path.exists(effect_path):
                try:
                    # Carregar efeito visual
                    effect_clip = VideoFileClip(effect_path)
                    # Redimensionar para combinar com vídeo principal
                    effect_clip = effect_clip.resize(video_clip.size)
                    # Aplicar efeito como overlay
                    video_clip = CompositeVideoClip([video_clip, effect_clip])
                    print(f"   ✅ Efeito visual aplicado: {effect_path}")
                except Exception as e:
                    print(f"   ❌ Erro ao aplicar efeito visual {effect_path}: {e}")
            else:
                print(f"   ❌ Efeito visual não encontrado: {effect_path}")
    
    return video_clip

def get_output_media(audio_file_path, timed_captions, background_video_data, video_server):
    OUTPUT_FILE_NAME = "rendered_video.mp4"
    magick_path = get_program_path("magick")
    print(magick_path)
    if magick_path:
        os.environ['IMAGEMAGICK_BINARY'] = magick_path
    else:
        os.environ['IMAGEMAGICK_BINARY'] = '/usr/bin/convert'
    
    # Carregar configurações de template
    template_configs = load_template_configs()
    
    visual_clips = []
    for (t1, t2), video_url in background_video_data:
        # Verificar se a URL é válida
        if video_url is None or video_url == "None":
            print(f"⚠️ URL inválida para intervalo {t1}-{t2}, pulando...")
            continue
            
        try:
            # Download the video file
            video_filename = tempfile.NamedTemporaryFile(delete=False).name
            download_file(video_url, video_filename)
            
            # Create VideoFileClip from the downloaded file
            video_clip = VideoFileClip(video_filename)
            video_clip = video_clip.set_start(t1)
            video_clip = video_clip.set_end(t2)
            
            # Aplicar efeitos do template ao vídeo
            video_clip = apply_template_effects_to_video(video_clip, template_configs)
            
            visual_clips.append(video_clip)
        except Exception as e:
            print(f"❌ Erro ao processar vídeo {video_url}: {e}")
            continue
    
    audio_clips = []
    audio_file_clip = AudioFileClip(audio_file_path)
    
    # Aplicar efeitos do template ao áudio
    audio_file_clip = apply_template_effects_to_audio(audio_file_clip, template_configs)
    
    # Aplicar pausas estratégicas se configuradas
    if 'pauses' in template_configs and template_configs['pauses']:
        audio_file_clip = apply_strategic_pauses(audio_file_clip, template_configs['pauses'])
    
    audio_clips.append(audio_file_clip)

    # Obter configurações de texto do template ou usar padrão
    text_config = template_configs.get('visual', {})
    font = text_config.get('font', 'Arial-Bold')
    fontsize = text_config.get('fontsize', 90)
    stroke_width = text_config.get('stroke_width', 4)
    color = text_config.get('color', 'white')
    position = text_config.get('position', 'center_bottom')
    margin_bottom = text_config.get('margin_bottom', 100)
    
    print(f"🎨 Aplicando estilo de texto do template:")
    print(f"   • Fonte: {font}")
    print(f"   • Tamanho: {fontsize}")
    print(f"   • Cor: {color}")
    print(f"   • Posição: {position}")

    for (t1, t2), text in timed_captions:
        text_clip = (TextClip(txt=text,
                              fontsize=fontsize,
                              font=font,
                              color=color,
                              stroke_color="black",
                              stroke_width=stroke_width,
                              method="label")
                  .set_start(t1)
                  .set_end(t2)
                  .set_position(("center", "bottom"))
                  .margin(bottom=margin_bottom)
                  .crossfadein(0.3)
                  .crossfadeout(0.3))
        visual_clips.append(text_clip)

    video = CompositeVideoClip(visual_clips)
    
    if audio_clips:
        audio = CompositeAudioClip(audio_clips)
        video.duration = audio.duration
        video.audio = audio

    video.write_videofile(OUTPUT_FILE_NAME, codec='libx264', audio_codec='aac', fps=25, preset='veryfast')
    
    # Clean up downloaded files
    for (t1, t2), video_url in background_video_data:
        if video_url and video_url != "None":
            try:
                video_filename = tempfile.NamedTemporaryFile(delete=False).name
                os.remove(video_filename)
            except:
                pass

    # Limpar arquivos de configuração temporários
    cleanup_temp_configs()

    return OUTPUT_FILE_NAME

def cleanup_temp_configs():
    """Remove arquivos de configuração temporários"""
    temp_files = [
        "temp_visual_config.json",
        "temp_audio_config.json", 
        "temp_pauses_config.json",
        "temp_effects_config.json"
    ]
    
    for filename in temp_files:
        file_path = Path(__file__).parent.parent.parent / filename
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"🧹 Arquivo temporário removido: {filename}")
            except Exception as e:
                print(f"⚠️ Erro ao remover {filename}: {e}")
