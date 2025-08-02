import os
import json
import sys
from typing import Dict, List, Optional
from pathlib import Path

# Adicionar o diretório raiz ao path para importar módulos
sys.path.append(str(Path(__file__).parent.parent.parent))

from utility.templates.template_manager import TemplateManager
from utility.script.template_script_generator import TemplateScriptGenerator

class TemplateRenderEngine:
    """Motor de renderização que integra templates com assets"""
    
    def __init__(self):
        self.template_manager = TemplateManager()
        self.script_generator = TemplateScriptGenerator()
    
    def generate_video_with_template(self, topic: str, template_id: str, output_path: str = None) -> Dict:
        """Gera vídeo completo usando template"""
        print(f"🎬 GERANDO VÍDEO COM TEMPLATE")
        print(f"📝 Tópico: {topic}")
        print(f"🎨 Template: {template_id}")
        print("="*60)
        
        # 1. Gerar roteiro com template
        script_result = self.script_generator.generate_script_with_pauses(topic, template_id)
        if 'error' in script_result:
            return script_result
        
        # 2. Validar assets do template
        assets_validation = self.script_generator.validate_template_assets(template_id)
        if not assets_validation.get('success', False):
            print("⚠️ Alguns assets estão faltando, mas continuando...")
        
        # 3. Preparar estrutura de renderização
        render_structure = self._prepare_render_structure(script_result, template_id)
        
        # 4. Gerar plano de execução
        execution_plan = self._create_execution_plan(render_structure)
        
        # 5. Retornar estrutura completa
        result = {
            'success': True,
            'topic': topic,
            'template_id': template_id,
            'template_name': script_result['template_name'],
            'script': script_result['script'],
            'render_structure': render_structure,
            'execution_plan': execution_plan,
            'assets_validation': assets_validation,
            'output_path': output_path or f"video_{template_id}_{topic.replace(' ', '_')}.mp4"
        }
        
        print(f"✅ Estrutura de renderização criada!")
        print(f"   • Seções: {len(render_structure['sections'])}")
        print(f"   • Assets de áudio: {len(render_structure['assets']['audio_effects'])}")
        print(f"   • Assets de vídeo: {len(render_structure['assets']['video_effects'])}")
        print(f"   • Trilhas sonoras: {len(render_structure['assets']['background_music'])}")
        
        return result
    
    def _prepare_render_structure(self, script_result: Dict, template_id: str) -> Dict:
        """Prepara a estrutura de renderização"""
        template_data = script_result['template_data']
        
        # Estrutura base
        render_structure = {
            'template_id': template_id,
            'script': script_result['script'],
            'sections': {},
            'assets': {
                'audio_effects': [],
                'video_effects': [],
                'background_music': []
            },
            'visual_settings': template_data.get('visual_settings', {}),
            'audio_settings': template_data.get('audio_settings', {}),
            'pauses_strategy': script_result.get('pauses_strategy', {})
        }
        
        # Organizar seções e assets
        for section_name, section_data in template_data.get('sections', {}).items():
            render_structure['sections'][section_name] = {
                'tone': section_data.get('tone'),
                'visual_style': section_data.get('visual_style'),
                'duration': section_data.get('duration'),
                'assets': section_data.get('assets', {})
            }
            
            # Adicionar assets à lista geral
            assets = section_data.get('assets', {})
            for asset_type, asset_list in assets.items():
                if asset_type not in render_structure['assets']:
                    render_structure['assets'][asset_type] = []
                
                if isinstance(asset_list, list):
                    render_structure['assets'][asset_type].extend(asset_list)
                elif isinstance(asset_list, str):
                    render_structure['assets'][asset_type].append(asset_list)
        
        return render_structure
    
    def _create_execution_plan(self, render_structure: Dict) -> Dict:
        """Cria plano de execução para renderização"""
        plan = {
            'steps': [],
            'estimated_duration': 0,
            'assets_required': {
                'audio_effects': [],
                'video_effects': [],
                'background_music': []
            }
        }
        
        # Step 1: Preparar áudio
        plan['steps'].append({
            'step': 1,
            'action': 'generate_audio',
            'description': 'Gerar áudio do roteiro',
            'settings': render_structure['audio_settings'],
            'estimated_time': 30
        })
        
        # Step 2: Gerar captions
        plan['steps'].append({
            'step': 2,
            'action': 'generate_captions',
            'description': 'Gerar legendas temporizadas',
            'settings': render_structure['visual_settings'],
            'estimated_time': 20
        })
        
        # Step 3: Buscar vídeos de fundo
        plan['steps'].append({
            'step': 3,
            'action': 'search_background_videos',
            'description': 'Buscar vídeos de fundo baseados no roteiro',
            'estimated_time': 45
        })
        
        # Step 4: Aplicar efeitos visuais
        for section_name, section_data in render_structure['sections'].items():
            plan['steps'].append({
                'step': len(plan['steps']) + 1,
                'action': 'apply_visual_effects',
                'description': f'Aplicar efeitos visuais para seção: {section_name}',
                'section': section_name,
                'assets': section_data.get('assets', {}),
                'estimated_time': 60
            })
        
        # Step 5: Aplicar efeitos sonoros
        plan['steps'].append({
            'step': len(plan['steps']) + 1,
            'action': 'apply_audio_effects',
            'description': 'Aplicar efeitos sonoros do template',
            'assets': render_structure['assets']['audio_effects'],
            'estimated_time': 40
        })
        
        # Step 6: Renderizar vídeo final
        plan['steps'].append({
            'step': len(plan['steps']) + 1,
            'action': 'render_final_video',
            'description': 'Renderizar vídeo final com todos os elementos',
            'estimated_time': 120
        })
        
        # Calcular tempo total estimado
        plan['estimated_duration'] = sum(step['estimated_time'] for step in plan['steps'])
        
        # Listar assets necessários
        for asset_type, assets in render_structure['assets'].items():
            plan['assets_required'][asset_type] = assets
        
        return plan
    
    def get_template_recommendations(self, topic: str) -> List[Dict]:
        """Obtém recomendações de templates para um tópico"""
        suggestions = self.script_generator.get_template_suggestions(topic)
        
        recommendations = []
        for suggestion in suggestions:
            # Validar assets do template
            assets_validation = self.script_generator.validate_template_assets(suggestion['template_id'])
            
            recommendation = {
                'template_id': suggestion['template_id'],
                'name': suggestion['name'],
                'description': suggestion['description'],
                'score': suggestion['score'],
                'reasons': suggestion['reasons'],
                'assets_ready': assets_validation.get('success', False),
                'missing_assets_count': sum(len(assets) for assets in assets_validation.get('missing_assets', {}).values())
            }
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def preview_template_assets(self, template_id: str) -> Dict:
        """Mostra preview dos assets de um template"""
        template = self.template_manager.get_template(template_id)
        if not template:
            return {'error': 'Template não encontrado'}
        
        preview = {
            'template_name': template.get('name'),
            'sections': {},
            'total_assets': {
                'audio_effects': 0,
                'video_effects': 0,
                'background_music': 0
            }
        }
        
        for section_name, section in template.get('sections', {}).items():
            assets = section.get('assets', {})
            section_preview = {
                'tone': section.get('tone'),
                'visual_style': section.get('visual_style'),
                'duration': section.get('duration'),
                'assets': {
                    'audio_effects': len(assets.get('audio_effects', [])),
                    'video_effects': len(assets.get('video_effects', [])),
                    'background_music': len(assets.get('background_music', []))
                }
            }
            
            preview['sections'][section_name] = section_preview
            
            # Somar assets
            for asset_type, count in section_preview['assets'].items():
                preview['total_assets'][asset_type] += count
        
        return preview

def main():
    """Teste do TemplateRenderEngine"""
    print("🎬 TESTE DO TEMPLATE RENDER ENGINE")
    print("="*60)
    
    engine = TemplateRenderEngine()
    
    # Testar recomendações de templates
    print("\n🎯 RECOMENDAÇÕES DE TEMPLATES:")
    recommendations = engine.get_template_recommendations("profecia bíblica do apocalipse")
    for rec in recommendations:
        print(f"   • {rec['name']} (Score: {rec['score']})")
        print(f"     Assets prontos: {rec['assets_ready']}")
    
    # Testar preview de assets
    print("\n🔍 PREVIEW DE ASSETS:")
    preview = engine.preview_template_assets("cinematic_religious")
    if 'error' not in preview:
        print(f"   • Template: {preview['template_name']}")
        print(f"   • Seções: {len(preview['sections'])}")
        print(f"   • Total de assets:")
        for asset_type, count in preview['total_assets'].items():
            print(f"     - {asset_type}: {count}")
    else:
        print(f"   ❌ {preview['error']}")
    
    # Testar geração de vídeo
    print("\n🎬 GERANDO VÍDEO COM TEMPLATE:")
    result = engine.generate_video_with_template("profecia bíblica", "cinematic_religious")
    
    if 'error' in result:
        print(f"❌ Erro: {result['error']}")
    else:
        print(f"✅ Estrutura de renderização criada!")
        print(f"   • Template: {result['template_name']}")
        print(f"   • Seções: {len(result['render_structure']['sections'])}")
        print(f"   • Passos de execução: {len(result['execution_plan']['steps'])}")
        print(f"   • Tempo estimado: {result['execution_plan']['estimated_duration']}s")
        
        # Mostrar passos de execução
        print(f"\n📋 PASSOS DE EXECUÇÃO:")
        for step in result['execution_plan']['steps']:
            print(f"   {step['step']}. {step['description']} ({step['estimated_time']}s)")

if __name__ == "__main__":
    main() 