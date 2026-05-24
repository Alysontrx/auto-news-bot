from apscheduler.schedulers.background import BackgroundScheduler
from database import get_schedules
from main import run_bot
import logging

# Configuração de log para o scheduler
logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)

scheduler = BackgroundScheduler()

def job_runner(limit):
    """Função que será executada nos horários agendados"""
    import subprocess
    try:
        subprocess.Popen(["python", "main.py", str(limit)])
    except Exception as e:
        print(f"Erro no job_runner: {e}")

def reload_jobs():
    """Lê do banco e recarrega todos os jobs no scheduler"""
    scheduler.remove_all_jobs()
    schedules = get_schedules()
    
    for s in schedules:
        time_str = s['time'] # formato HH:MM
        limit = s['limit']
        
        if not s.get('active', True):
            print(f"Ignorando (Pausado): {time_str} ({limit} posts)")
            continue
            
        try:
            hour, minute = time_str.split(':')
            job_id = f"job_{s['id']}"
            scheduler.add_job(
                func=job_runner,
                trigger='cron',
                hour=int(hour),
                minute=int(minute),
                args=[limit],
                id=job_id,
                replace_existing=True
            )
            print(f"Agendado: {time_str} ({limit} posts) - Job ID: {job_id}")
        except Exception as e:
            print(f"Erro ao agendar {time_str}: {e}")

def init_scheduler():
    reload_jobs()
    if not scheduler.running:
        scheduler.start()
