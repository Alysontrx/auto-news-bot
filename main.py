import os
from fetch_news import get_trending_news
from generate_content import rewrite_news
from publish import publish_post

def main():
    print("Iniciando Agente de Postagem...\n")
    
    # 1. Busca notícias
    news_list = get_trending_news(limit=10)
    
    if not news_list:
        print("Nenhuma notícia encontrada.")
        return

    for i, news in enumerate(news_list):
        print(f"\n--- Processando Notícia {i+1} ---")
        safe_title = news['title'].encode('cp1252', errors='ignore').decode('cp1252')
        print(f"Original: {safe_title}")
        
        # 2. Gera novo conteúdo (Gemini)
        content = rewrite_news(news['title'], news['summary'])
        safe_new_title = content['catchy_title'].encode('cp1252', errors='ignore').decode('cp1252')
        print(f"Novo Título: {safe_new_title}")
        
        import time
        import requests
        
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
        success = publish_post(title=content['catchy_title'], content=content['short_text'], media_path=dummy_image_path, chapeu=news.get('category', 'Notícias'))
        
        if success:
            print("\n--------------------------------------------------")
            safe_pub_title = content['catchy_title'].encode('cp1252', errors='ignore').decode('cp1252')
            print(f"Título publicado: {safe_pub_title}")
            print("--------------------------------------------------\n")
            print("Robô executou a tentativa de postagem com sucesso!")
        else:
            print("Falha na execução do robô.")
            
        print("Aguardando 10 segundos antes da próxima postagem...")
        time.sleep(10)
        
if __name__ == "__main__":
    main()
