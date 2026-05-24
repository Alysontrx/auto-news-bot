from google import genai
from database import get_setting
import json

def rewrite_news(news_title, news_summary):
    """
    Usa o Gemini para gerar um título chamativo e um texto curto/explicativo.
    """
    GEMINI_API_KEY = get_setting('gemini_key', '')
    
    if not GEMINI_API_KEY:
        print("AVISO: GEMINI_API_KEY não configurada no banco de dados. Retornando texto de fallback.")
        return {
            "catchy_title": f"{news_title}",
            "short_text": f"{news_title}\n\nConfira os detalhes sobre esta notícia de tecnologia."
        }

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        prompt = f"""
Você é um redator de um portal de notícias regional e nacional focado em gerar engajamento.
Eu vou te passar o título e um resumo de uma notícia em alta.
Você deve me retornar um JSON estrito com 2 campos:
1. "catchy_title": Um título chamativo (mas não mentiroso/clickbait falso).
2. "short_text": Um texto longo e aprofundado, com pelo menos 3 a 4 parágrafos bem desenvolvidos. Use tags HTML como <p> para separar os parágrafos e <strong> para destacar partes importantes.

Notícia Original: {news_title}
Resumo Original: {news_summary}

Retorne APENAS o JSON válido. Exemplo:
{{
  "catchy_title": "Título Aqui",
  "short_text": "<p>Primeiro parágrafo...</p><p>Segundo parágrafo...</p>"
}}
"""
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        
        text_response = response.text
        # Remove possíveis blocos de código ```json ... ```
        if text_response.startswith("```json"):
            text_response = text_response.strip("```json").strip("```").strip()
            
        data = json.loads(text_response)
        
        import os
        import base64
        
        ad_html = "<hr><h3>🏡 Oportunidade: Apartamento Familiar à Venda</h3>"
        
        # Tenta carregar a imagem do anúncio que o usuário enviou
        ad_image_path = os.path.join(os.getcwd(), "images", "anuncio.jpg")
        if os.path.exists(ad_image_path):
            try:
                with open(ad_image_path, "rb") as img_file:
                    encoded_string = base64.b64encode(img_file.read()).decode('utf-8')
                    # Adiciona o link do WhatsApp envolvendo a imagem
                    wpp_link = get_setting('wpp_link', 'https://wa.me/5511961161382')
                    ad_html += f'<br><a href="{wpp_link}" target="_blank"><img src="data:image/jpeg;base64,{encoded_string}" style="max-width: 100%; border-radius: 8px;" /></a><br>'
            except Exception as img_e:
                print("Erro ao carregar a imagem do anúncio:", img_e)
        else:
            # Se não achar a imagem, coloca um aviso pra gente
            ad_html += "<p><em>[A imagem do anúncio aparecerá aqui assim que o arquivo anuncio.jpg for salvo na pasta images]</em></p>"
            
        texto_final = data.get("short_text", "Texto gerado automaticamente.") + ad_html

        return {
            "catchy_title": data.get("catchy_title", news_title),
            "short_text": texto_final
        }
        
    except Exception as e:
        print(f"Erro ao gerar conteúdo com Gemini: {e}")
        
        import os
        import base64
        
        ad_html = "<hr><h3>🏡 Oportunidade: Apartamento Familiar à Venda</h3>"
        ad_image_path = os.path.join(os.getcwd(), "images", "anuncio.jpg")
        if os.path.exists(ad_image_path):
            try:
                with open(ad_image_path, "rb") as img_file:
                    encoded_string = base64.b64encode(img_file.read()).decode('utf-8')
                    wpp_link = get_setting('wpp_link', 'https://wa.me/5511961161382')
                    ad_html += f'<br><a href="{wpp_link}" target="_blank"><img src="data:image/jpeg;base64,{encoded_string}" style="max-width: 100%; border-radius: 8px;" /></a><br>'
            except:
                pass
        else:
            ad_html += "<p><em>[A imagem do anúncio aparecerá aqui assim que o arquivo anuncio.jpg for salvo na pasta images]</em></p>"
            
        return {
            "catchy_title": news_title,
            "short_text": f"<p>Erro temporário ao reescrever a notícia original: {news_title}</p>" + ad_html
        }
