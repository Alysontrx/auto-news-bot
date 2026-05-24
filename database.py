import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.getcwd(), 'bot_database.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabela de Agendamentos (Ex: 08:00 -> 5 postagens)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time TEXT NOT NULL,
        limit_posts INTEGER NOT NULL,
        active INTEGER DEFAULT 1
    )
    ''')
    
    # Se a tabela schedules já existir mas não tiver a coluna active, vamos tentar adicionar
    try:
        cursor.execute('ALTER TABLE schedules ADD COLUMN active INTEGER DEFAULT 1')
    except:
        pass
    
    # Tabela de Configurações (Chave/Valor)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    ''')
    
    # Tabela de Logs de Notícias Postadas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT,
        date_posted TEXT NOT NULL,
        status TEXT NOT NULL
    )
    ''')
    
    # Tabela de URLs já postadas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS posted_urls (
        url TEXT PRIMARY KEY,
        date_posted TEXT NOT NULL
    )
    ''')
    
    # Popula configurações padrão se não existirem
    default_settings = [
        ('gemini_key', ''),
        ('site_user', 'Alyson'),
        ('site_pass', ''),
        ('wpp_link', 'https://wa.me/5511961161382'),
        ('blocked_words', 'lula, bolsonaro, stf, moraes, pt, pl, política, eleições, governo, haddad, milei, maduro, pacheco, deputado, senador, congresso, câmara, stj'),
        ('admin_password', 'admin123')
    ]
    for k, v in default_settings:
        cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', (k, v))
        
    conn.commit()
    conn.close()

def get_setting(key, default_value=''):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
    row = cursor.fetchone()
    conn.close()
    
    val = row[0] if row else ''
    
    # Fallback supremo para o servidor Render (que apaga o banco de dados quando reinicia)
    if not val:
        env_map = {
            'gemini_key': 'GEMINI_API_KEY',
            'site_user': 'SITE_USERNAME',
            'site_pass': 'SITE_PASSWORD',
            'wpp_link': 'WPP_LINK'
        }
        env_key = env_map.get(key)
        if env_key:
            val = os.getenv(env_key, '')
            
    return val if val else default_value

def update_setting(key, value):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET value = ? WHERE key = ?", (value, key))
    conn.commit()
    conn.close()

def get_all_settings():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    settings = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    return settings

def is_url_posted(url):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM posted_urls WHERE url = ?", (url,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def mark_url_posted(url):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT OR IGNORE INTO posted_urls (url, date_posted) VALUES (?, ?)", (url, now))
    conn.commit()
    conn.close()

def get_schedules():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, time, limit_posts, active FROM schedules ORDER BY time ASC')
    schedules = [{'id': row[0], 'time': row[1], 'limit': row[2], 'active': bool(row[3])} for row in cursor.fetchall()]
    conn.close()
    return schedules

def add_schedule(time_str, limit):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO schedules (time, limit_posts, active) VALUES (?, ?, 1)', (time_str, limit))
    conn.commit()
    conn.close()

def delete_schedule(schedule_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM schedules WHERE id = ?', (schedule_id,))
    conn.commit()
    conn.close()

def toggle_schedule(schedule_id, active):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE schedules SET active = ? WHERE id = ?', (int(active), schedule_id))
    conn.commit()
    conn.close()

def log_post(title, category, status="Sucesso"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('INSERT INTO logs (title, category, date_posted, status) VALUES (?, ?, ?, ?)', 
                   (title, category, now, status))
    conn.commit()
    conn.close()

def delete_log(log_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Busca o title antes de deletar
    cursor.execute('SELECT title FROM logs WHERE id = ?', (log_id,))
    row = cursor.fetchone()
    title = row[0] if row else None
    
    if title:
        cursor.execute('DELETE FROM logs WHERE id = ?', (log_id,))
        conn.commit()
        
    conn.close()
    return title

def get_logs(limit=50):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, category, date_posted, status FROM logs ORDER BY id DESC LIMIT ?', (limit,))
    logs = [{'id': row[0], 'title': row[1], 'category': row[2], 'date_posted': row[3], 'status': row[4]} for row in cursor.fetchall()]
    conn.close()
    return logs

def get_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute("SELECT COUNT(*) FROM logs WHERE date_posted LIKE ?", (f"{today}%",))
    today_posts = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM logs WHERE status = 'Sucesso'")
    success_posts = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM logs")
    total_posts = cursor.fetchone()[0]
    
    success_rate = 0
    if total_posts > 0:
        success_rate = int((success_posts / total_posts) * 100)
        
    conn.close()
    return {
        "today_posts": today_posts,
        "total_success": success_posts,
        "success_rate": success_rate
    }
