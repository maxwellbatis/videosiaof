import json
import os
import sys
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import random

# Adicionar o diretório raiz ao path para importar módulos
sys.path.append(str(Path(__file__).parent.parent.parent))

from utility.templates.template_manager import TemplateManager

class TemplateRenderEngine:
    """Motor de renderização com suporte a templates"""
    
    def __init__(self):
        self.template_manager = TemplateManager()
        self.rendered_videos = []
    
    def apply_template_to_video(self, video_path: str, template_id: str, script: str, audio_path: str) -> Dict:
        """Aplica um template específico ao vídeo durante a renderização"""
        print(f"🎬 APLICANDO TEMPLATE: {template_id}")
        print("="*50)
        
        # Carregar template
        template = self.template_manager.get_template(template_id)
        if not template:
            return {'error': f'Template {template_id} não encontrado'}
        
        # Obter configurações do template
        visual_settings = template.get('visual_settings', {})
        audio_settings = template.get('audio_settings', {})
        pauses_strategy = template.get('pauses_strategy', {})
        
        # Aplicar configurações visuais
        self._apply_visual_settings(video_path, visual_settings)
        
        # Aplicar configurações de áudio
        self._apply_audio_settings(audio_path, audio_settings)
        
        # Aplicar estratégia de pausas
        self._apply_pauses_strategy(script, pauses_strategy)
        
        # Aplicar efeitos de template
        self._apply_template_effects(video_path, template)
        
        return {
            'success': True,
            'template_id': template_id,
            'template_name': template.get('name'),
            'applied_settings': {
                'visual': visual_settings,
                'audio': audio_settings,
                'pauses': pauses_strategy
            }
        }
    
    def _apply_visual_settings(self, video_path: str, visual_settings: Dict):
        """Aplica configurações visuais do template"""
        print("🎨 Aplicando configurações visuais...")
        
        text_style = visual_settings.get('text_style', {})
        composition = visual_settings.get('composition', {})
        
        # Configurar estilo de texto
        font = text_style.get('font', 'Arial-Bold')
        fontsize = text_style.get('fontsize', 90)
        stroke_width = text_style.get('stroke_width', 4)
        color = text_style.get('color', 'white')
        position = text_style.get('position', 'center_bottom')
        margin_bottom = text_style.get('margin_bottom', 100)
        
        print(f"   • Fonte: {font}")
        print(f"   • Tamanho: {fontsize}")
        print(f"   • Cor: {color}")
        print(f"   • Posição: {position}")
        
        # Salvar configurações para uso no render_engine
        self._save_visual_config({
            'font': font,
            'fontsize': fontsize,
            'stroke_width': stroke_width,
            'color': color,
            'position': position,
            'margin_bottom': margin_bottom
        })
    
    def _apply_audio_settings(self, audio_path: str, audio_settings: Dict):
        """Aplica configurações de áudio do template"""
        print("🎵 Aplicando configurações de áudio...")
        
        voice = audio_settings.get('voice', 'pt-BR-FranciscoNeural')
        rate = audio_settings.get('rate', 1.0)
        volume = audio_settings.get('volume', 1.0)
        bg_music_volume = audio_settings.get('background_music_volume', 0.3)
        effects_volume = audio_settings.get('effects_volume', 0.5)
        
        print(f"   • Voz: {voice}")
        print(f"   • Taxa: {rate}")
        print(f"   • Volume: {volume}")
        print(f"   • Volume música: {bg_music_volume}")
        print(f"   • Volume efeitos: {effects_volume}")
        
        # Salvar configurações para uso no render_engine
        self._save_audio_config({
            'voice': voice,
            'rate': rate,
            'volume': volume,
            'bg_music_volume': bg_music_volume,
            'effects_volume': effects_volume
        })
    
    def _apply_pauses_strategy(self, script: str, pauses_strategy: Dict):
        """Aplica estratégia de pausas ao script"""
        print("⏱️ Aplicando estratégia de pausas...")
        
        all_pauses = []
        for pause_type, pauses in pauses_strategy.items():
            for pause in pauses:
                all_pauses.append({
                    'position': pause.get('position', 0),
                    'duration': pause.get('duration', 0),
                    'purpose': pause.get('purpose', ''),
                    'description': pause.get('description', ''),
                    'type': pause_type
                })
        
        # Ordenar pausas por posição
        all_pauses.sort(key=lambda x: x['position'])
        
        print(f"   • Total de pausas: {len(all_pauses)}")
        for pause in all_pauses:
            print(f"   • {pause['position']:.1f}s ({pause['duration']:.1f}s): {pause['description']}")
        
        # Salvar pausas para uso no render_engine
        self._save_pauses_config(all_pauses)
    
    def _apply_template_effects(self, video_path: str, template: Dict):
        """Aplica efeitos específicos do template"""
        print("✨ Aplicando efeitos do template...")
        
        sections = template.get('sections', {})
        
        for section_name, section_data in sections.items():
            print(f"   • Seção: {section_name}")
            
            # Efeitos de áudio
            audio_effects = section_data.get('assets', {}).get('audio_effects', [])
            for effect in audio_effects:
                if os.path.exists(effect):
                    print(f"     - Áudio: {effect}")
                else:
                    print(f"     - Áudio: {effect} (não encontrado)")
            
            # Efeitos de vídeo
            video_effects = section_data.get('assets', {}).get('video_effects', [])
            for effect in video_effects:
                if os.path.exists(effect):
                    print(f"     - Vídeo: {effect}")
                else:
                    print(f"     - Vídeo: {effect} (não encontrado)")
            
            # Música de fundo
            bg_music = section_data.get('assets', {}).get('background_music', '')
            if bg_music and os.path.exists(bg_music):
                print(f"     - Música: {bg_music}")
            elif bg_music:
                print(f"     - Música: {bg_music} (não encontrado)")
        
        # Salvar efeitos para uso no render_engine
        self._save_effects_config(sections)
    
    def _save_visual_config(self, config: Dict):
        """Salva configurações visuais para uso posterior"""
        config_file = Path(__file__).parent.parent.parent / "temp_visual_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def _save_audio_config(self, config: Dict):
        """Salva configurações de áudio para uso posterior"""
        config_file = Path(__file__).parent.parent.parent / "temp_audio_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def _save_pauses_config(self, pauses: List[Dict]):
        """Salva configurações de pausas para uso posterior"""
        config_file = Path(__file__).parent.parent.parent / "temp_pauses_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(pauses, f, indent=2, ensure_ascii=False)
    
    def _save_effects_config(self, sections: Dict):
        """Salva configurações de efeitos para uso posterior"""
        config_file = Path(__file__).parent.parent.parent / "temp_effects_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(sections, f, indent=2, ensure_ascii=False)
    
    def get_template_recommendations(self, topic: str) -> List[Dict]:
        """Recomenda templates baseado no tópico"""
        templates = self.template_manager.list_templates()
        recommendations = []
        
        topic_lower = topic.lower()
        
        for template in templates:
            score = 0
            reasons = []
            
            # Análise baseada em palavras-chave
            if any(word in topic_lower for word in ['bíblico', 'religioso', 'profecia', 'apocalipse', 'deus', 'jesus', 'bíblia']):
                if 'religioso' in template['name'].lower():
                    score += 3
                    reasons.append("Conteúdo religioso detectado")
            
            if any(word in topic_lower for word in ['curioso', 'interessante', 'fato', 'descoberta']):
                if 'curioso' in template['name'].lower():
                    score += 2
                    reasons.append("Conteúdo educativo detectado")
            
            if score > 0:
                recommendations.append({
                    'template_id': template['id'],
                    'name': template['name'],
                    'description': template['description'],
                    'score': score,
                    'reasons': reasons,
                    'assets_ready': self._check_template_assets(template['id'])
                })
        
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations
    
    def _check_template_assets(self, template_id: str) -> bool:
        """Verifica se os assets do template estão disponíveis"""
        template = self.template_manager.get_template(template_id)
        if not template:
            return False
        
        sections = template.get('sections', {})
        missing_assets = 0
        total_assets = 0
        
        for section_name, section_data in sections.items():
            assets = section_data.get('assets', {})
            
            # Verificar efeitos de áudio
            for effect in assets.get('audio_effects', []):
                total_assets += 1
                if not os.path.exists(effect):
                    missing_assets += 1
            
            # Verificar efeitos de vídeo
            for effect in assets.get('video_effects', []):
                total_assets += 1
                if not os.path.exists(effect):
                    missing_assets += 1
            
            # Verificar música de fundo
            bg_music = assets.get('background_music', '')
            if bg_music:
                total_assets += 1
                if not os.path.exists(bg_music):
                    missing_assets += 1
        
        # Template está pronto se pelo menos 70% dos assets estão disponíveis
        return total_assets > 0 and (missing_assets / total_assets) <= 0.3
    
    def preview_template_assets(self, template_id: str) -> Dict:
        """Mostra preview dos assets do template"""
        template = self.template_manager.get_template(template_id)
        if not template:
            return {'error': f'Template {template_id} não encontrado'}
        
        sections = template.get('sections', {})
        total_assets = {
            'audio_effects': 0,
            'video_effects': 0,
            'background_music': 0
        }
        
        for section_name, section_data in sections.items():
            assets = section_data.get('assets', {})
            total_assets['audio_effects'] += len(assets.get('audio_effects', []))
            total_assets['video_effects'] += len(assets.get('video_effects', []))
            if assets.get('background_music'):
                total_assets['background_music'] += 1
        
        return {
            'template_id': template_id,
            'template_name': template.get('name'),
            'sections': sections,
            'total_assets': total_assets
        }
    
    def generate_video_with_template(self, topic: str, template_id: str) -> Dict:
        """Gera vídeo completo com template aplicado"""
        print(f"🎬 GERANDO VÍDEO COM TEMPLATE")
        print(f"📝 Tópico: {topic}")
        print(f"🎨 Template: {template_id}")
        print("="*60)
        
        # Carregar template
        template = self.template_manager.get_template(template_id)
        if not template:
            return {'error': f'Template {template_id} não encontrado'}
        
        # Validar assets
        assets_ready = self._check_template_assets(template_id)
        if not assets_ready:
            print("⚠️ Alguns assets estão faltando, mas continuando...")
        
        # Criar estrutura de renderização
        render_structure = {
            'template_id': template_id,
            'template_name': template.get('name'),
            'sections': template.get('sections', {}),
            'visual_settings': template.get('visual_settings', {}),
            'audio_settings': template.get('audio_settings', {}),
            'pauses_strategy': template.get('pauses_strategy', {})
        }
        
        # Criar plano de execução
        execution_plan = {
            'steps': [
                {'name': 'Gerar áudio do roteiro', 'duration': 30},
                {'name': 'Gerar legendas temporizadas', 'duration': 20},
                {'name': 'Buscar vídeos de fundo baseados no roteiro', 'duration': 45},
                {'name': 'Aplicar efeitos visuais para seção: intro', 'duration': 60},
                {'name': 'Aplicar efeitos visuais para seção: development', 'duration': 60},
                {'name': 'Aplicar efeitos visuais para seção: climax', 'duration': 60},
                {'name': 'Aplicar efeitos visuais para seção: conclusion', 'duration': 60},
                {'name': 'Aplicar efeitos sonoros do template', 'duration': 40},
                {'name': 'Renderizar vídeo final com todos os elementos', 'duration': 120}
            ],
            'estimated_duration': 495  # 8.25 minutos
        }
        
        return {
            'success': True,
            'template_id': template_id,
            'template_name': template.get('name'),
            'render_structure': render_structure,
            'execution_plan': execution_plan,
            'assets_ready': assets_ready
        }

def main():
    """Teste do TemplateRenderEngine"""
    print("🎬 TESTE DO TEMPLATE RENDER ENGINE")
    print("="*60)
    
    engine = TemplateRenderEngine()
    
    # Testar recomendações
    print("\n🎯 TESTANDO RECOMENDAÇÕES:")
    recommendations = engine.get_template_recommendations("profecia bíblica do apocalipse")
    for rec in recommendations:
        print(f"   • {rec['name']} (Score: {rec['score']})")
        print(f"     Assets prontos: {rec['assets_ready']}")
    
    # Testar preview
    print("\n🔍 TESTANDO PREVIEW:")
    if recommendations:
        template_id = recommendations[0]['template_id']
        preview = engine.preview_template_assets(template_id)
        if 'error' not in preview:
            print(f"   ✅ Preview do template: {preview['template_name']}")
            print(f"   Seções: {len(preview['sections'])}")
            for asset_type, count in preview['total_assets'].items():
                print(f"   {asset_type}: {count}")
    
    # Testar geração completa
    print("\n🚀 TESTANDO GERAÇÃO COMPLETA:")
    if recommendations:
        template_id = recommendations[0]['template_id']
        result = engine.generate_video_with_template("profecia bíblica", template_id)
        if 'error' not in result:
            print(f"   ✅ Estrutura de renderização criada!")
            print(f"   Template: {result['template_name']}")
            print(f"   Seções: {len(result['render_structure']['sections'])}")
            print(f"   Passos: {len(result['execution_plan']['steps'])}")
            print(f"   Tempo estimado: {result['execution_plan']['estimated_duration']}s")
        else:
            print(f"   ❌ Erro: {result['error']}")

if __name__ == "__main__":
    main() 