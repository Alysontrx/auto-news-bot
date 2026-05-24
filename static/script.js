document.addEventListener('DOMContentLoaded', () => {
    loadSchedules();
    loadLogs();
    loadStats();
    
    // Atualiza os logs e stats a cada 30 segundos
    setInterval(() => {
        loadLogs();
        loadStats();
    }, 30000);
});

// Busca as estatísticas
async function loadStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        document.getElementById('stat-today').innerText = data.today_posts;
        document.getElementById('stat-success').innerText = data.total_success;
        document.getElementById('stat-rate').innerText = data.success_rate + '%';
    } catch(e) {
        console.error("Erro ao carregar stats", e);
    }
}

// Busca os horários agendados
async function loadSchedules() {
    try {
        const res = await fetch('/api/schedules');
        const data = await res.json();
        
        const tbody = document.querySelector('#schedules-table tbody');
        tbody.innerHTML = '';
        
        if(data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color: var(--text-secondary)">Nenhum horário agendado</td></tr>';
            return;
        }

        data.forEach(item => {
            const tr = document.createElement('tr');
            tr.style.opacity = item.active ? '1' : '0.5';
            
            const toggleBtnText = item.active ? 'Pausar' : 'Retomar';
            const toggleBtnColor = item.active ? '#fbbf24' : '#10b981';
            
            tr.innerHTML = `
                <td><strong>${item.time}</strong></td>
                <td>${item.limit} notícias</td>
                <td>
                    <button class="btn" style="background: ${toggleBtnColor}; color: #000; padding: 0.4rem 0.8rem; font-size: 0.8rem; margin-right: 5px;" onclick="toggleSchedule(${item.id}, ${!item.active})">${toggleBtnText}</button>
                    <button class="btn btn-danger" onclick="deleteSchedule(${item.id})">Remover</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch(e) {
        console.error("Erro ao carregar horários", e);
    }
}

async function toggleSchedule(id, active) {
    try {
        await fetch(`/api/schedules/${id}/toggle`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ active: active })
        });
        loadSchedules();
    } catch(e) {
        alert("Erro ao alterar status");
    }
}

// Adiciona um novo agendamento
async function addSchedule(e) {
    e.preventDefault();
    const time = document.getElementById('time').value;
    const limit = document.getElementById('limit').value;
    
    try {
        const res = await fetch('/api/schedules', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ time, limit })
        });
        
        if(res.ok) {
            document.getElementById('time').value = '';
            document.getElementById('limit').value = '5';
            loadSchedules();
        }
    } catch(e) {
        alert("Erro ao adicionar");
    }
}

// Remove agendamento
async function deleteSchedule(id) {
    if(!confirm("Certeza que deseja remover este horário?")) return;
    
    try {
        await fetch(`/api/schedules/${id}`, { method: 'DELETE' });
        loadSchedules();
    } catch(e) {
        alert("Erro ao remover");
    }
}

// Busca histórico de postagens
async function loadLogs() {
    try {
        const res = await fetch('/api/logs');
        const data = await res.json();
        
        const tbody = document.querySelector('#logs-table tbody');
        tbody.innerHTML = '';
        
        if(data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color: var(--text-secondary)">Nenhuma postagem realizada ainda</td></tr>';
            return;
        }

        data.forEach(item => {
            const tr = document.createElement('tr');
            const statusClass = item.status.toLowerCase() === 'sucesso' ? 'status-success' : 'status-error';
            tr.innerHTML = `
                <td style="color: var(--text-secondary)">${item.date_posted}</td>
                <td style="max-width: 300px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${item.title}">${item.title}</td>
                <td>${item.category}</td>
                <td><span class="status-badge ${statusClass}">${item.status}</span></td>
            `;
            tbody.appendChild(tr);
        });
    } catch(e) {
        console.error("Erro ao carregar logs", e);
    }
}

// Força execução agora
async function runBotNow() {
    const btn = document.getElementById('btn-run-now');
    btn.disabled = true;
    btn.innerHTML = '⏳ Iniciando...';
    
    try {
        const res = await fetch('/api/run', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ limit: 1 }) // Roda só 1 por padrão no botão manual
        });
        
        if(res.ok) {
            alert("Robô iniciado em segundo plano! Ele publicará 1 notícia em breve.");
            // Atualiza os logs para mostrar quando terminar
            setTimeout(loadLogs, 15000); 
        }
    } catch(e) {
        alert("Erro ao acionar o robô");
    } finally {
        btn.disabled = false;
        btn.innerHTML = '🚀 Executar Agora (1 Post)';
    }
}
