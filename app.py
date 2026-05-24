from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
from database import init_db, get_schedules, add_schedule, delete_schedule, toggle_schedule, get_logs, get_all_settings, update_setting, get_setting, get_stats
from scheduler import init_scheduler, reload_jobs, job_runner
import threading
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Decorator de proteção
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        admin_pass = get_setting('admin_password', 'admin123')
        if password == admin_pass:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Senha incorreta")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/settings', methods=['GET'])
@login_required
def settings():
    return render_template('settings.html')

# --- API ESTATÍSTICAS ---
@app.route('/api/stats', methods=['GET'])
@login_required
def api_get_stats():
    return jsonify(get_stats())

# --- API CONFIGURAÇÕES ---
@app.route('/api/settings', methods=['GET'])
@login_required
def api_get_settings():
    return jsonify(get_all_settings())

@app.route('/api/settings', methods=['POST'])
@login_required
def api_save_settings():
    data = request.json
    for k, v in data.items():
        update_setting(k, v)
    return jsonify({"success": True})

# --- API HORÁRIOS ---
@app.route('/api/schedules', methods=['GET'])
@login_required
def api_get_schedules():
    return jsonify(get_schedules())

@app.route('/api/schedules', methods=['POST'])
@login_required
def api_add_schedule():
    data = request.json
    time_str = data.get('time')
    limit = int(data.get('limit', 5))
    
    if time_str and limit:
        add_schedule(time_str, limit)
        reload_jobs()
        return jsonify({"success": True, "message": "Agendamento adicionado"})
    return jsonify({"success": False, "message": "Dados inválidos"}), 400

@app.route('/api/schedules/<int:sched_id>', methods=['DELETE'])
@login_required
def api_delete_schedule(sched_id):
    delete_schedule(sched_id)
    reload_jobs()
    return jsonify({"success": True})

@app.route('/api/schedules/<int:sched_id>/toggle', methods=['POST'])
@login_required
def api_toggle_schedule(sched_id):
    active = request.json.get('active', True)
    toggle_schedule(sched_id, active)
    reload_jobs()
    return jsonify({"success": True})

# --- API LOGS ---
@app.route('/api/logs', methods=['GET'])
@login_required
def api_get_logs():
    return jsonify(get_logs(limit=50))

# --- FORÇAR EXECUÇÃO ---
@app.route('/api/run', methods=['POST'])
@login_required
def api_run_now():
    data = request.json
    limit = int(data.get('limit', 1))
    
    thread = threading.Thread(target=job_runner, args=(limit,))
    thread.start()
    
    return jsonify({"success": True, "message": f"Iniciado para {limit} postagem(ns)"})

if __name__ == '__main__':
    init_db()
    init_scheduler()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
