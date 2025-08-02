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
                    "Você não vai acreditar no que já estava previsto a séculos.",
                    "Prepare-se para descobrir uma verdade chocante.",
                    "O que você está prestes a ver vai mudar tudo."
                ],
                'development_patterns': [
                    "Em {topic} está escrito que",
                    "A {topic} revela que",
                    "Segundo a {topic},"
                ],
                'climax_patterns': [
                    "Agora pense comigo sobre isso.",
                    "Mas o que isso significa para nós?",
                    "E se eu te disser que"
                ],
                'conclusion_patterns': [
                    "Ou será que já estamos vivendo o início dessa profecia?",
                    "Será que você está preparado para essa verdade?",
                    "O que você vai fazer com essa informação?"
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
        
        # Gerar roteiro usando padrões do template
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
        
        # Criar roteiro completo
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
        # Primeiro gerar o roteiro básico
        result = self.generate_script_for_template(topic, template_id)
        if 'error' in result:
            return result
        
        # Obter estratégia de pausas do template
        pauses_strategy = self.template_manager.get_pauses_strategy(template_id)
        if not pauses_strategy:
            return result  # Retornar resultado sem pausas se não houver estratégia
        
        # Adicionar informações de pausas ao resultado
        result['pauses_strategy'] = pauses_strategy
        result['pauses_applied'] = True
        
        print(f"\n⏱️ ESTRATÉGIA DE PAUSAS APLICADA:")
        for pause_type, pauses in pauses_strategy.items():
            print(f"   • {pause_type}: {len(pauses)} pausas")
            for pause in pauses:
                print(f"     - {pause.get('position', 0):.1f}s ({pause.get('duration', 0):.1f}s): {pause.get('description', '')}")
        
        return result
    
    def validate_template_assets(self, template_id: str) -> Dict:
        """Valida se todos os assets necessários para o template estão disponíveis"""
        print(f"🔍 VALIDANDO ASSETS DO TEMPLATE: {template_id}")
        print("-" * 40)
        
        missing_assets = self.template_manager.validate_assets(template_id)
        
        if 'error' in missing_assets:
            return missing_assets
        
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
        
        print(f"🎨 TEMPLATES SUGERIDOS:")
        for i, suggestion in enumerate(suggestions[:3], 1):
            print(f"   {i}. {suggestion['name']} (Score: {suggestion['score']})")
            print(f"      {suggestion['description']}")
            for reason in suggestion['reasons']:
                print(f"      • {reason}")
        
        # Usar o template com maior score
        best_template = suggestions[0]
        print(f"\n✅ Usando template: {best_template['name']}")
        
        # Gerar roteiro com o template escolhido
        return self.generate_script_with_pauses(topic, best_template['template_id'])

def main():
    """Teste do TemplateScriptGenerator"""
    print("🎬 TESTE DO TEMPLATE SCRIPT GENERATOR")
    print("="*60)
    
    generator = TemplateScriptGenerator()
    
    # Testar validação de assets
    print("\n🔍 VALIDANDO ASSETS:")
    validation = generator.validate_template_assets("cinematic_religious")
    if validation.get('success'):
        print("✅ Template pronto para uso!")
    else:
        print("⚠️ Alguns assets estão faltando, mas o template pode ser usado")
    
    # Testar sugestões de templates
    print("\n🎯 TESTANDO SUGESTÕES:")
    suggestions = generator.get_template_suggestions("profecia bíblica do apocalipse")
    for suggestion in suggestions:
        print(f"   • {suggestion['name']} (Score: {suggestion['score']})")
    
    # Testar geração com sugestões
    print("\n📝 GERANDO ROTEIRO COM SUGESTÕES:")
    result = generator.generate_with_suggestions("profecia bíblica do apocalipse")
    
    if 'error' in result:
        print(f"❌ Erro: {result['error']}")
    else:
        print(f"✅ Roteiro gerado com sucesso!")
        print(f"   • Template: {result['template_name']}")
        print(f"   • Tópico: {result['topic']}")
        print(f"   • Pausas aplicadas: {result.get('pauses_applied', False)}")
        
        # Mostrar parte do roteiro
        script = result['script']
        if len(script) > 100:
            script = script[:100] + "..."
        print(f"   • Roteiro: {script}")

if __name__ == "__main__":
    main() 