import feedparser
from config import RSS_FEED_URL

def get_trending_news(limit=5):
    """
    Busca as notícias mais recentes e em alta do Google News RSS.
    Retorna uma lista de dicionários com 'title', 'link' e 'summary'.
    """
    print(f"Buscando as {limit} notícias mais em alta do Brasil...")
    feed = feedparser.parse(RSS_FEED_URL)
    
    from playwright.sync_api import sync_playwright
    import re
    
    def get_article_image(url):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                # Acessa a url (Google News fará o redirect)
                page.goto(url, wait_until='domcontentloaded', timeout=30000)
                
                # Aguarda um pouco para JS redirecionar
                page.wait_for_timeout(3000)
                
                # Opcional: tenta pegar o og:image do head
                img_url = page.locator('meta[property="og:image"], meta[name="og:image"]').get_attribute('content', timeout=2000)
                
                if not img_url:
                    # Alternativa, tentar achar alguma imagem grande na página
                    img_url = page.locator('img').first.get_attribute('src', timeout=1000)
                
                # Se for URL relativa, completa com o domínio atual
                if img_url and img_url.startswith('/'):
                    from urllib.parse import urlparse
                    parsed = urlparse(page.url)
                    img_url = f"{parsed.scheme}://{parsed.netloc}{img_url}"
                
                browser.close()
                return img_url
        except Exception as e:
            print("Erro ao extrair imagem da notícia:", e)
        return None

    # Lista de palavras para evitar (assuntos polêmicos/política)
    blocked_keywords = [
        'lula', 'bolsonaro', 'stf', 'moraes', 'pt', 'pl', 'política', 
        'eleições', 'governo', 'haddad', 'milei', 'maduro', 'pacheco',
        'deputado', 'senador', 'congresso', 'câmara', 'stj'
    ]

    news_items = []
    for entry in feed.entries:
        title_lower = entry.title.lower()
        
        # Pula a notícia se tiver palavra bloqueada
        if any(kw in title_lower for kw in blocked_keywords):
            continue
            
        # Tenta extrair a imagem real do site da notícia
        safe_title = entry.title[:30].encode('cp1252', errors='ignore').decode('cp1252')
        print(f"Buscando imagem para: {safe_title}...")
        image_url = get_article_image(entry.link)
        
        news_items.append({
            "title": entry.title,
            "url": entry.link,
            "summary": entry.get("summary", ""),
            "published": entry.get("published", ""),
            "image_url": image_url,
            "category": entry.get("category", "Notícias")
        })
        
        # Para quando atingir o limite
        if len(news_items) >= limit:
            break
        
    return news_items

if __name__ == "__main__":
    # Teste simples
    noticias = get_trending_news(2)
    for n in noticias:
        safe_t = n['title'].encode('cp1252', errors='ignore').decode('cp1252')
        print(f"- {safe_t}\n  Link: {n['url']}\n")
