import os
from datetime import datetime

# Tenta importar psycopg2, se não conseguir vai de sqlite3
try:
    import psycopg2
except ImportError:
    psycopg2 = None
import sqlite3

DB_PATH = os.path.join(os.getcwd(), 'bot_database.db')
# Pega a URL do banco (padrão de serviços como Render, Heroku, Neon)
DATABASE_URL = os.getenv('DATABASE_URL')
IS_POSTGRES = bool(DATABASE_URL and DATABASE_URL.startswith("postgres"))

def get_conn():
    if IS_POSTGRES:
        if not psycopg2:
            raise Exception("psycopg2-binary não está instalado. Adicione no requirements.txt.")
        return psycopg2.connect(DATABASE_URL)
    return sqlite3.connect(DB_PATH)

def execute_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    conn = get_conn()
    cursor = conn.cursor()
    
    # Adapta a query para o PostgreSQL se necessário
    if IS_POSTGRES:
        # Troca ? por %s
        query = query.replace('?', '%s')
        
    try:
        cursor.execute(query, params)
        if commit:
            conn.commit()
            
        if fetchone:
            result = cursor.fetchone()
            return result
        if fetchall:
            result = cursor.fetchall()
            return result
    finally:
        cursor.close()
        conn.close()

def init_db():
    conn = get_conn()
    cursor = conn.cursor()
    
    if IS_POSTGRES:
        # POSTGRESQL SCHEMAS
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedules (
            id SERIAL PRIMARY KEY,
            time TEXT NOT NULL,
            limit_posts INTEGER NOT NULL,
            active INTEGER DEFAULT 1
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            category TEXT,
            date_posted TEXT NOT NULL,
            status TEXT NOT NULL
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS posted_urls (
            url TEXT PRIMARY KEY,
            date_posted TEXT NOT NULL
        )
        ''')
    else:
        # SQLITE SCHEMAS
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time TEXT NOT NULL,
            limit_posts INTEGER NOT NULL,
            active INTEGER DEFAULT 1
        )
        ''')
        try:
            cursor.execute('ALTER TABLE schedules ADD COLUMN active INTEGER DEFAULT 1')
        except:
            pass
            
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT,
            date_posted TEXT NOT NULL,
            status TEXT NOT NULL
        )
        ''')
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
        if IS_POSTGRES:
            cursor.execute('INSERT INTO settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO NOTHING', (k, v))
        else:
            cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', (k, v))
        
    conn.commit()
    cursor.close()
    conn.close()

def get_setting(key, default_value=''):
    row = execute_query('SELECT value FROM settings WHERE key = ?', (key,), fetchone=True)
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
    execute_query("UPDATE settings SET value = ? WHERE key = ?", (value, key), commit=True)

def get_all_settings():
    rows = execute_query("SELECT key, value FROM settings", fetchall=True)
    return {row[0]: row[1] for row in rows} if rows else {}

def is_url_posted(url):
    row = execute_query("SELECT 1 FROM posted_urls WHERE url = ?", (url,), fetchone=True)
    return row is not None

def mark_url_posted(url):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if IS_POSTGRES:
        execute_query("INSERT INTO posted_urls (url, date_posted) VALUES (?, ?) ON CONFLICT (url) DO NOTHING", (url, now), commit=True)
    else:
        execute_query("INSERT OR IGNORE INTO posted_urls (url, date_posted) VALUES (?, ?)", (url, now), commit=True)

def get_schedules():
    rows = execute_query('SELECT id, time, limit_posts, active FROM schedules ORDER BY time ASC', fetchall=True)
    return [{'id': row[0], 'time': row[1], 'limit': row[2], 'active': bool(row[3])} for row in (rows or [])]

def add_schedule(time_str, limit):
    execute_query('INSERT INTO schedules (time, limit_posts, active) VALUES (?, ?, 1)', (time_str, limit), commit=True)

def delete_schedule(schedule_id):
    execute_query('DELETE FROM schedules WHERE id = ?', (schedule_id,), commit=True)

def toggle_schedule(schedule_id, active):
    execute_query('UPDATE schedules SET active = ? WHERE id = ?', (int(active), schedule_id), commit=True)

def log_post(title, category, status="Sucesso"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    execute_query('INSERT INTO logs (title, category, date_posted, status) VALUES (?, ?, ?, ?)', 
                   (title, category, now, status), commit=True)

def delete_log(log_id):
    row = execute_query('SELECT title FROM logs WHERE id = ?', (log_id,), fetchone=True)
    title = row[0] if row else None
    
    if title:
        execute_query('DELETE FROM logs WHERE id = ?', (log_id,), commit=True)
        
    return title

def get_logs(limit=50):
    rows = execute_query('SELECT id, title, category, date_posted, status FROM logs ORDER BY id DESC LIMIT ?', (limit,), fetchall=True)
    return [{'id': row[0], 'title': row[1], 'category': row[2], 'date_posted': row[3], 'status': row[4]} for row in (rows or [])]

def get_stats():
    today = datetime.now().strftime("%Y-%m-%d")
    
    today_posts_row = execute_query("SELECT COUNT(*) FROM logs WHERE date_posted LIKE ?", (f"{today}%",), fetchone=True)
    today_posts = today_posts_row[0] if today_posts_row else 0
    
    success_posts_row = execute_query("SELECT COUNT(*) FROM logs WHERE status = 'Sucesso'", fetchone=True)
    success_posts = success_posts_row[0] if success_posts_row else 0
    
    total_posts_row = execute_query("SELECT COUNT(*) FROM logs", fetchone=True)
    total_posts = total_posts_row[0] if total_posts_row else 0
    
    success_rate = 0
    if total_posts > 0:
        success_rate = int((success_posts / total_posts) * 100)
        
    return {
        "today_posts": today_posts,
        "total_success": success_posts,
        "success_rate": success_rate
    }
