import os
from fetch_news import get_trending_news
from generate_content import rewrite_news
from publish import publish_post
from database import log_post, init_db
import time
import requests

def run_bot(limit=5):
    print(f"Iniciando Agente de Postagem (Limite: {limit})...\n")
    
    # 1. Busca notícias
    news_list = get_trending_news(limit=limit)
    
    if not news_list:
        print("Nenhuma notícia encontrada.")
        return []

    logs = []
    
    for i, news in enumerate(news_list):
        print(f"\n--- Processando Notícia {i+1} ---")
        safe_title = news['title'].encode('cp1252', errors='ignore').decode('cp1252')
        print(f"Original: {safe_title}")
        
        # 2. Gera novo conteúdo (Gemini)
        content = rewrite_news(news['title'], news['summary'])
        safe_new_title = content['catchy_title'].encode('cp1252', errors='ignore').decode('cp1252')
        print(f"Novo Título: {safe_new_title}")
        
        # Garante que a pasta images existe
        os.makedirs(os.path.join(os.getcwd(), "images"), exist_ok=True)
        dummy_image_path = os.path.join(os.getcwd(), "images", "capa.jpg")
        
        img_url = news.get('image_url')
        if not img_url:
            img_url = f"https://picsum.photos/800/400?random={int(time.time())}"
            
        print(f"Baixando imagem de capa (JPG) da notícia...")
        try:
            response = requests.get(img_url, verify=False, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            with open(dummy_image_path, "wb") as f:
                f.write(response.content)
        except Exception as e:
            print("Erro ao baixar imagem, usando genérica...", e)
            try:
                response = requests.get(f"https://picsum.photos/800/400?random={int(time.time())}", verify=False)
                with open(dummy_image_path, "wb") as f:
                    f.write(response.content)
            except:
                pass

        # 3. Publica (Playwright) passando a imagem de teste
        print("Publicando no site...")
        category = news.get('category', 'Notícias')
        success = publish_post(title=content['catchy_title'], content=content['short_text'], media_path=dummy_image_path, chapeu=category)
        
        status = "Sucesso" if success else "Falha"
        log_post(content['catchy_title'], category, status)
        logs.append({"title": content['catchy_title'], "status": status})
        
        if success:
            from database import mark_url_posted
            mark_url_posted(news['url'])
            print(f"Robô executou a tentativa de postagem com sucesso!")
        else:
            print("Falha na execução do robô.")
            
        if i < len(news_list) - 1:
            print("Aguardando 10 segundos antes da próxima postagem...")
            time.sleep(10)
            
    return logs

if __name__ == "__main__":
    import sys
    limit = 1
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            pass
            
    init_db()
    run_bot(limit=limit)

