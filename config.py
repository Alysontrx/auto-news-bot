import os
from dotenv import load_dotenv

load_dotenv()

# Configurações do site
SITE_ADMIN_URL = "https://leiasb.com.br/admin/"
SITE_USERNAME = os.getenv("SITE_USERNAME", "")
SITE_PASSWORD = os.getenv("SITE_PASSWORD", "")

# Chave da API do Gemini (AI)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Google News RSS (Tecnologia - Brasil)
RSS_FEED_URL = "https://news.google.com/rss/search?q=tecnologia&hl=pt-BR&gl=BR&ceid=BR:pt-419"
