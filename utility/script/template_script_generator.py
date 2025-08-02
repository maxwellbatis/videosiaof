import json
import os
import sys
from typing import Dict, List, Optional
from pathlib import Path

# Adicionar o diretório raiz ao path para importar módulos
sys.path.append(str(Path(__file__).parent.parent.parent))

from utility.templates.template_manager import TemplateManager

class TemplateScriptGenerator:
    """Gerador de roteiro adaptativo baseado em templates"""
    
    def __init__(self):
        self.template_manager = TemplateManager()
        self.script_templates = {
            'cinematic_religious': {
                'intro_patterns': [
                    "Você não vai acreditar no que já estava previsto há séculos.",
                    "Prepare-se para descobrir uma verdade chocante.",
                    "O que você está prestes a ver vai mudar tudo.",
                    "Uma profecia antiga está se cumprindo agora mesmo.",
                    "O que a Bíblia previu está acontecendo diante dos nossos olhos."
                ],
                'development_patterns': [
                    "Em {topic} está escrito que",
                    "A {topic} revela que",
                    "Segundo a {topic},",
                    "A profecia sobre {topic} diz que",
                    "O que {topic} previu está acontecendo agora"
                ],
                'climax_patterns': [
                    "Agora pense comigo sobre isso.",
                    "Mas o que isso significa para nós?",
                    "E se eu te disser que",
                    "O mais assustador é que",
                    "E o pior ainda está por vir."
                ],
                'conclusion_patterns': [
                    "Ou será que já estamos vivendo o início dessa profecia?",
                    "Será que você está preparado para essa verdade?",
                    "O que você vai fazer com essa informação?",
                    "Está na hora de acordar para a realidade.",
                    "A escolha é sua: ignorar ou agir."
                ]
            }
        }
    
    def generate_script_for_template(self, topic: str, template_id: str) -> Dict:
        """Gera um roteiro específico para um template"""
        print(f"🎬 GERANDO ROTEIRO PARA TEMPLATE: {template_id}")
        print(f"📝 Tópico: {topic}")
        print("-" * 50)
        
        # Verificar se o template existe
        template = self.template_manager.get_template(template_id)
        if not template:
            return {'error': f'Template {template_id} não encontrado'}
        
        # Gerar roteiro usando IA se possível, senão usar padrões
        script = self._generate_script_with_ai(topic, template_id)
        if not script:
            script = self._generate_script_from_patterns(topic, template_id)
        
        if not script:
            return {'error': 'Não foi possível gerar o roteiro'}
        
        # Aplicar template ao roteiro gerado
        template_result = self.template_manager.apply_template_to_script(script, template_id)
        
        if 'error' in template_result:
            return template_result
        
        # Combinar resultados
        final_result = {
            'success': True,
            'template_id': template_id,
            'template_name': template.get('name'),
            'topic': topic,
            'script': script,
            'template_data': template_result,
            'estimated_duration': 45  # Duração estimada em segundos
        }
        
        print(f"✅ Roteiro gerado com sucesso!")
        print(f"   • Template: {template.get('name')}")
        print(f"   • Duração estimada: {final_result['estimated_duration']}s")
        print(f"   • Palavras: {len(script.split())}")
        
        return final_result
    
    def _generate_script_with_ai(self, topic: str, template_id: str) -> str:
        """Gera roteiro usando IA (Groq/OpenAI)"""
        try:
            # Verificar se temos API key disponível
            if not os.environ.get("GROQ_API_KEY") and not os.environ.get("OPENAI_KEY"):
                print("⚠️ Nenhuma API key disponível, usando padrões")
                return ""
            
            # Importar módulo de script generator
            from utility.script.script_generator import generate_script
            
            # Gerar script base usando IA
            base_script = generate_script(topic)
            
            # Adaptar para o template específico
            if template_id == 'cinematic_religious':
                adapted_script = self._adapt_for_religious_template(base_script, topic)
                return adapted_script
            
            return base_script
            
        except Exception as e:
            print(f"⚠️ Erro ao gerar script com IA: {e}")
            return ""
    
    def _adapt_for_religious_template(self, base_script: str, topic: str) -> str:
        """Adapta script para template religioso/cinematográfico"""
        # Remover frases muito genéricas e adicionar tom dramático
        dramatic_intro = "Você não vai acreditar no que já estava previsto há séculos."
        
        # Extrair pontos principais do script base
        sentences = base_script.split('.')
        main_points = [s.strip() for s in sentences if len(s.strip()) > 20][:3]
        
        # Criar script dramático
        dramatic_script = f"{dramatic_intro} {topic} revela verdades chocantes que estão acontecendo agora mesmo. "
        
        if main_points:
            dramatic_script += " ".join(main_points) + ". "
        
        dramatic_script += f"Mas o que isso significa para nós? E se eu te disser que o que {topic} previu está se cumprindo diante dos nossos olhos? Será que você está preparado para essa verdade? Ou será que já estamos vivendo o início dessa profecia?"
        
        return dramatic_script
    
    def _generate_script_from_patterns(self, topic: str, template_id: str) -> str:
        """Gera roteiro usando padrões pré-definidos"""
        if template_id not in self.script_templates:
            return ""
        
        patterns = self.script_templates[template_id]
        
        # Selecionar padrões baseados no tópico
        import random
        
        intro = random.choice(patterns['intro_patterns'])
        development = random.choice(patterns['development_patterns']).format(topic=topic)
        climax = random.choice(patterns['climax_patterns'])
        conclusion = random.choice(patterns['conclusion_patterns'])
        
        # Criar roteiro completo mais dinâmico
        script_parts = [
            intro,
            f"E agora está acontecendo bem diante dos nossos olhos.",
            f"{development} grandes mudanças estão por vir.",
            f"O controle total está sendo implementado.",
            f"{climax}",
            f"O que você pensa sobre isso?",
            f"{conclusion}"
        ]
        
        return " ".join(script_parts)
    
    def generate_script_with_pauses(self, topic: str, template_id: str) -> Dict:
        """Gera roteiro com estratégia de pausas aplicada"""
        print(f"🎬 GERANDO ROTEIRO COM PAUSAS: {template_id}")
        print(f"📝 Tópico: {topic}")
        print("-" * 50)
        
        # Primeiro gerar o roteiro básico
        result = self.generate_script_for_template(topic, template_id)
        if 'error' in result:
            return result
        
        # Obter estratégia de pausas do template
        template = self.template_manager.get_template(template_id)
        pauses_strategy = template.get('pauses_strategy', {}) if template else {}
        
        if pauses_strategy:
            # Adicionar informações de pausas ao resultado
            result['pauses_strategy'] = pauses_strategy
            result['pauses_applied'] = True
            
            print(f"\n⏱️ ESTRATÉGIA DE PAUSAS APLICADA:")
            for pause_type, pauses in pauses_strategy.items():
                print(f"   • {pause_type}: {len(pauses)} pausas")
                for pause in pauses:
                    print(f"     - {pause.get('position', 0):.1f}s ({pause.get('duration', 0):.1f}s): {pause.get('description', '')}")
        else:
            print("⚠️ Nenhuma estratégia de pausas encontrada para este template")
        
        return result
    
    def validate_template_assets(self, template_id: str) -> Dict:
        """Valida se todos os assets necessários para o template estão disponíveis"""
        print(f"🔍 VALIDANDO ASSETS DO TEMPLATE: {template_id}")
        print("-" * 40)
        
        template = self.template_manager.get_template(template_id)
        if not template:
            return {'error': f'Template {template_id} não encontrado'}
        
        missing_assets = {
            'audio_effects': [],
            'video_effects': [],
            'background_music': []
        }
        
        # Verificar assets em cada seção
        sections = template.get('sections', {})
        for section_name, section_data in sections.items():
            assets = section_data.get('assets', {})
            
            # Verificar efeitos de áudio
            for effect in assets.get('audio_effects', []):
                if not os.path.exists(effect):
                    missing_assets['audio_effects'].append(effect)
            
            # Verificar efeitos de vídeo
            for effect in assets.get('video_effects', []):
                if not os.path.exists(effect):
                    missing_assets['video_effects'].append(effect)
            
            # Verificar música de fundo
            bg_music = assets.get('background_music', '')
            if bg_music and not os.path.exists(bg_music):
                missing_assets['background_music'].append(bg_music)
        
        total_missing = sum(len(assets) for assets in missing_assets.values())
        
        if total_missing == 0:
            print("✅ Todos os assets estão disponíveis!")
            return {'success': True, 'missing_assets': missing_assets}
        else:
            print(f"⚠️ {total_missing} assets faltando:")
            for asset_type, missing in missing_assets.items():
                if missing:
                    print(f"   • {asset_type}: {len(missing)} arquivos")
                    for asset in missing[:3]:  # Mostrar apenas os primeiros 3
                        print(f"     - {asset}")
                    if len(missing) > 3:
                        print(f"     ... e mais {len(missing) - 3} arquivos")
            
            return {'success': False, 'missing_assets': missing_assets}
    
    def get_template_suggestions(self, topic: str) -> List[Dict]:
        """Sugere templates apropriados para um tópico"""
        templates = self.template_manager.list_templates()
        suggestions = []
        
        # Análise simples baseada em palavras-chave
        topic_lower = topic.lower()
        
        for template in templates:
            score = 0
            reasons = []
            
            # Verificar se é conteúdo religioso/bíblico
            if any(word in topic_lower for word in ['bíblico', 'religioso', 'profecia', 'apocalipse', 'deus', 'jesus', 'bíblia']):
                if 'religioso' in template['name'].lower() or 'cinematográfico' in template['name'].lower():
                    score += 3
                    reasons.append("Conteúdo religioso detectado")
            
            # Verificar se é conteúdo educativo/curioso
            if any(word in topic_lower for word in ['curioso', 'interessante', 'fato', 'descoberta', 'ciência', 'história']):
                if 'curioso' in template['name'].lower() or 'fatos' in template['name'].lower():
                    score += 2
                    reasons.append("Conteúdo educativo detectado")
            
            if score > 0:
                suggestions.append({
                    'template_id': template['id'],
                    'name': template['name'],
                    'description': template['description'],
                    'score': score,
                    'reasons': reasons
                })
        
        # Ordenar por score
        suggestions.sort(key=lambda x: x['score'], reverse=True)
        
        return suggestions
    
    def generate_with_suggestions(self, topic: str) -> Dict:
        """Gera roteiro com sugestão automática de template"""
        print(f"🎯 GERANDO ROTEIRO COM SUGESTÕES")
        print(f"📝 Tópico: {topic}")
        print("-" * 50)
        
        # Obter sugestões de templates
        suggestions = self.get_template_suggestions(topic)
        
        if not suggestions:
            return {'error': 'Nenhum template apropriado encontrado para o tópico'}
        
        # Usar o template com maior score
        best_template = suggestions[0]
        print(f"🎨 Template sugerido: {best_template['name']} (Score: {best_template['score']})")
        
        # Gerar roteiro com o template sugerido
        return self.generate_script_with_pauses(topic, best_template['template_id'])

def main():
    """Teste do TemplateScriptGenerator"""
    print("🎬 TESTE DO TEMPLATE SCRIPT GENERATOR")
    print("="*60)
    
    generator = TemplateScriptGenerator()
    
    # Testar geração de script
    print("\n📝 TESTANDO GERAÇÃO DE SCRIPT:")
    result = generator.generate_script_with_pauses("profecia bíblica do apocalipse", "cinematic_religious")
    
    if 'error' not in result:
        print(f"✅ Script gerado com sucesso!")
        print(f"   • Template: {result['template_name']}")
        print(f"   • Palavras: {len(result['script'].split())}")
        print(f"   • Pausas aplicadas: {result.get('pauses_applied', False)}")
        print(f"\n📄 Script:")
        print(f"   {result['script'][:200]}...")
    else:
        print(f"❌ Erro: {result['error']}")
    
    # Testar validação de assets
    print("\n🔍 TESTANDO VALIDAÇÃO DE ASSETS:")
    validation = generator.validate_template_assets("cinematic_religious")
    if 'error' not in validation:
        print(f"   • Sucesso: {validation['success']}")
        if not validation['success']:
            print(f"   • Assets faltando: {sum(len(assets) for assets in validation['missing_assets'].values())}")
    else:
        print(f"   ❌ Erro: {validation['error']}")
    
    # Testar sugestões
    print("\n🎯 TESTANDO SUGESTÕES:")
    suggestions = generator.get_template_suggestions("profecia bíblica do apocalipse")
    for suggestion in suggestions:
        print(f"   • {suggestion['name']} (Score: {suggestion['score']})")
        for reason in suggestion['reasons']:
            print(f"     - {reason}")

if __name__ == "__main__":
    main() 