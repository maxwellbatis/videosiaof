import json
import os
from typing import Dict, List, Optional
from pathlib import Path

class TemplateManager:
    """Gerenciador de templates para geração de vídeos"""
    
    def __init__(self, templates_dir: str = "utility/templates"):
        self.templates_dir = Path(templates_dir)
        self.templates = {}
        self.load_templates()
    
    def load_templates(self):
        """Carrega todos os templates disponíveis"""
        if not self.templates_dir.exists():
            print(f"❌ Diretório de templates não encontrado: {self.templates_dir}")
            return
        
        for template_file in self.templates_dir.glob("*.json"):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                    template_id = template_data.get('template')
                    if template_id:
                        self.templates[template_id] = template_data
                        print(f"✅ Template carregado: {template_data.get('name', template_id)}")
            except Exception as e:
                print(f"❌ Erro ao carregar template {template_file}: {e}")
    
    def get_template(self, template_id: str) -> Optional[Dict]:
        """Retorna um template específico"""
        return self.templates.get(template_id)
    
    def list_templates(self) -> List[Dict]:
        """Lista todos os templates disponíveis"""
        return [
            {
                'id': template_id,
                'name': template.get('name', template_id),
                'description': template.get('description', ''),
                'version': template.get('version', '1.0')
            }
            for template_id, template in self.templates.items()
        ]
    
    def get_template_sections(self, template_id: str) -> Optional[Dict]:
        """Retorna as seções de um template"""
        template = self.get_template(template_id)
        return template.get('sections') if template else None
    
    def get_template_assets(self, template_id: str, section_name: str = None) -> Optional[Dict]:
        """Retorna os assets de um template ou seção específica"""
        template = self.get_template(template_id)
        if not template:
            return None
        
        if section_name:
            sections = template.get('sections', {})
            section = sections.get(section_name)
            return section.get('assets') if section else None
        
        # Retorna todos os assets do template
        all_assets = {
            'audio_effects': [],
            'video_effects': [],
            'background_music': []
        }
        
        for section_name, section in template.get('sections', {}).items():
            assets = section.get('assets', {})
            for asset_type, asset_list in assets.items():
                if isinstance(asset_list, list):
                    all_assets[asset_type].extend(asset_list)
                elif isinstance(asset_list, str):
                    all_assets[asset_type].append(asset_list)
        
        return all_assets
    
    def get_pauses_strategy(self, template_id: str) -> Optional[Dict]:
        """Retorna a estratégia de pausas de um template"""
        template = self.get_template(template_id)
        return template.get('pauses_strategy') if template else None
    
    def get_visual_settings(self, template_id: str) -> Optional[Dict]:
        """Retorna as configurações visuais de um template"""
        template = self.get_template(template_id)
        return template.get('visual_settings') if template else None
    
    def get_audio_settings(self, template_id: str) -> Optional[Dict]:
        """Retorna as configurações de áudio de um template"""
        template = self.get_template(template_id)
        return template.get('audio_settings') if template else None
    
    def get_script_generation_settings(self, template_id: str) -> Optional[Dict]:
        """Retorna as configurações de geração de roteiro"""
        template = self.get_template(template_id)
        return template.get('script_generation') if template else None
    
    def validate_assets(self, template_id: str) -> Dict[str, List[str]]:
        """Valida se todos os assets do template existem"""
        template = self.get_template(template_id)
        if not template:
            return {'error': ['Template não encontrado']}
        
        missing_assets = {
            'audio_effects': [],
            'video_effects': [],
            'background_music': []
        }
        
        for section_name, section in template.get('sections', {}).items():
            assets = section.get('assets', {})
            for asset_type, asset_list in assets.items():
                if isinstance(asset_list, list):
                    for asset_path in asset_list:
                        if not os.path.exists(asset_path):
                            missing_assets[asset_type].append(asset_path)
                elif isinstance(asset_list, str):
                    if not os.path.exists(asset_list):
                        missing_assets[asset_type].append(asset_list)
        
        return missing_assets
    
    def generate_script_prompt(self, template_id: str, topic: str) -> Optional[str]:
        """Gera o prompt para geração de roteiro baseado no template"""
        script_settings = self.get_script_generation_settings(template_id)
        if not script_settings:
            return None
        
        prompt_template = script_settings.get('prompt_template', '')
        return prompt_template.format(topic=topic)
    
    def apply_template_to_script(self, script: str, template_id: str) -> Dict:
        """Aplica um template a um roteiro existente"""
        template = self.get_template(template_id)
        if not template:
            return {'error': 'Template não encontrado'}
        
        # Estrutura do resultado
        result = {
            'template_id': template_id,
            'template_name': template.get('name'),
            'script': script,
            'sections': {},
            'pauses': template.get('pauses_strategy', {}),
            'visual_settings': template.get('visual_settings', {}),
            'audio_settings': template.get('audio_settings', {}),
            'assets': {}
        }
        
        # Organizar assets por seção
        for section_name, section in template.get('sections', {}).items():
            result['sections'][section_name] = {
                'tone': section.get('tone'),
                'visual_style': section.get('visual_style'),
                'narrative_purpose': section.get('narrative_purpose'),
                'duration': section.get('duration'),
                'assets': section.get('assets', {})
            }
            
            # Adicionar assets à lista geral
            assets = section.get('assets', {})
            for asset_type, asset_list in assets.items():
                if asset_type not in result['assets']:
                    result['assets'][asset_type] = []
                if isinstance(asset_list, list):
                    result['assets'][asset_type].extend(asset_list)
                elif isinstance(asset_list, str):
                    result['assets'][asset_type].append(asset_list)
        
        return result
    
    def get_template_info(self, template_id: str) -> Dict:
        """Retorna informações detalhadas sobre um template"""
        template = self.get_template(template_id)
        if not template:
            return {'error': 'Template não encontrado'}
        
        # Validar assets
        missing_assets = self.validate_assets(template_id)
        
        return {
            'id': template_id,
            'name': template.get('name'),
            'description': template.get('description'),
            'version': template.get('version'),
            'duration_range': template.get('duration_range'),
            'sections_count': len(template.get('sections', {})),
            'pauses_count': sum(len(pauses) for pauses in template.get('pauses_strategy', {}).values()),
            'missing_assets': missing_assets,
            'has_missing_assets': any(missing_assets.values())
        }

def main():
    """Teste do TemplateManager"""
    print("🎬 TESTE DO TEMPLATE MANAGER")
    print("="*50)
    
    # Inicializar gerenciador
    manager = TemplateManager()
    
    # Listar templates
    templates = manager.list_templates()
    print(f"\n📋 TEMPLATES DISPONÍVEIS:")
    for template in templates:
        print(f"   • {template['name']} (v{template['version']})")
        print(f"     {template['description']}")
    
    # Testar template cinematográfico religioso
    template_id = "cinematic_religious"
    print(f"\n🎭 TESTE DO TEMPLATE: {template_id}")
    print("-" * 40)
    
    # Informações do template
    info = manager.get_template_info(template_id)
    if 'error' not in info:
        print(f"   • Nome: {info['name']}")
        print(f"   • Seções: {info['sections_count']}")
        print(f"   • Pausas: {info['pauses_count']}")
        print(f"   • Assets faltando: {info['has_missing_assets']}")
        
        if info['has_missing_assets']:
            print(f"   ⚠️ Assets faltando:")
            for asset_type, missing in info['missing_assets'].items():
                if missing:
                    print(f"      {asset_type}: {len(missing)} arquivos")
    else:
        print(f"   ❌ {info['error']}")
    
    # Testar geração de prompt
    prompt = manager.generate_script_prompt(template_id, "profecia bíblica")
    if prompt:
        print(f"\n📝 PROMPT GERADO:")
        print(f"   {prompt}")
    
    # Testar aplicação de template
    test_script = "Você não vai acreditar no que já estava previsto a séculos..."
    result = manager.apply_template_to_script(test_script, template_id)
    if 'error' not in result:
        print(f"\n✅ TEMPLATE APLICADO COM SUCESSO!")
        print(f"   • Template: {result['template_name']}")
        print(f"   • Seções: {len(result['sections'])}")
        print(f"   • Assets de áudio: {len(result['assets'].get('audio_effects', []))}")
        print(f"   • Assets de vídeo: {len(result['assets'].get('video_effects', []))}")
    else:
        print(f"   ❌ {result['error']}")

if __name__ == "__main__":
    main() 