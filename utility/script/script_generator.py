import os
from openai import OpenAI
import json

if os.environ.get("GROQ_API_KEY") and len(os.environ.get("GROQ_API_KEY")) > 30:
    from groq import Groq
    model = "llama3-70b-8192"
    client = Groq(
        api_key=os.environ.get("GROQ_API_KEY"),
        )
else:
    OPENAI_API_KEY = os.getenv('OPENAI_KEY')
    model = "gpt-4o"
    client = OpenAI(api_key=OPENAI_API_KEY)

def generate_script(topic):
    prompt = (
        """Você é um escritor experiente para um canal de YouTube Shorts, especializado em vídeos de fatos curiosos. 
        Seus vídeos são concisos, cada um durando menos de 50 segundos (aproximadamente 140 palavras). 
        Eles são incrivelmente envolventes e originais. Quando um usuário solicita um tipo específico de fatos, você criará o conteúdo.

        IMPORTANTE: Sempre responda em PORTUGUÊS BRASILEIRO.

        Por exemplo, se o usuário pedir:
        Fatos estranhos
        Você produziria conteúdo assim:

        Fatos estranhos que você não conhece:
        - Bananas são bagas, mas morangos não são.
        - Uma única nuvem pode pesar mais de um milhão de libras.
        - Existe uma espécie de água-viva que é biologicamente imortal.
        - O mel nunca estraga; arqueólogos encontraram potes de mel em tumbas egípcias antigas com mais de 3.000 anos e ainda comestíveis.
        - A guerra mais curta da história foi entre a Grã-Bretanha e Zanzibar em 27 de agosto de 1896. Zanzibar se rendeu após 38 minutos.
        - Polvos têm três corações e sangue azul.

        Você agora tem a tarefa de criar o melhor roteiro curto baseado no tipo de 'fatos' solicitado pelo usuário.

        Mantenha breve, altamente interessante e único.
        SEMPRE USE PORTUGUÊS BRASILEIRO.

        Forneça estritamente o roteiro em formato JSON como abaixo, e apenas forneça um objeto JSON analisável com a chave 'script'.

        # Saída
        {"script": "Aqui está o roteiro ..."}
        """
    )

    response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": topic}
            ]
        )
    content = response.choices[0].message.content
    try:
        # Limpar caracteres de controle e quebras de linha
        content = content.replace('\n', ' ').replace('\r', ' ')
        # Remover aspas duplas extras que podem causar problemas
        content = content.replace('""', '"')
        script = json.loads(content)["script"]
    except Exception as e:
        # Tentar extrair JSON da resposta
        json_start_index = content.find('{')
        json_end_index = content.rfind('}')
        if json_start_index != -1 and json_end_index != -1:
            content = content[json_start_index:json_end_index+1]
            content = content.replace('\n', ' ').replace('\r', ' ')
            content = content.replace('""', '"')
            try:
                script = json.loads(content)["script"]
            except:
                # Se ainda falhar, retornar o conteúdo limpo
                script = content.replace('{"script": "', '').replace('"}', '')
        else:
            # Se não encontrar JSON, retornar o conteúdo como está
            script = content
    return script
