// Dashboard JS - Real stats, activity, responsive
const API_BASE = '/api/admin';

async function loadStats() {
  const data = await apiFetch('/stats');
  if (!data) return;
  
  document.getElementById('totalUsers').textContent = data.total_users.toLocaleString();
  document.getElementById('totalUnis').textContent = data.total_universities.toLocaleString();
  document.getElementById('totalApps').textContent = data.total_applications.toLocaleString();
  document.getElementById('totalChats').textContent = data.total_chats.toLocaleString();
  document.getElementById('totalFacs').textContent = data.total_faculties.toLocaleString();
  document.getElementById('totalProgs').textContent = data.total_programs.toLocaleString();
  
  // Update charts
  updateChart(data);
}

async function loadRecentActivity() {
  // Mock or real recent - add /api/admin/recent if needed
  const activity = [
    { time: '2 min ago', action: 'University Cairo updated', user: 'Admin' },
    { time: '5 min ago', action: 'New application received', user: 'Ahmed S.' },
    // ...
  ];
  const list = document.getElementById('activityList');
  list.innerHTML = activity.map(a => `<li><strong>${a.user}</strong> ${a.action} <span>${a.time}</span></li>`).join('');
}

function apiFetch(endpoint, options = {}) {
  return ensureAdminToken()
    .then(token => fetch(API_BASE + endpoint, {
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      ...options
    }))
    .then(res => res.status === 401 ? (localStorage.removeItem('token'), null) : res.json().catch(() => null))
    .catch(() => null);
}

function ensureAdminToken() {
  const token = localStorage.getItem('token');
  if (token) return Promise.resolve(token);
  return fetch('/admin-token', { credentials: 'same-origin' })
    .then(res => res.ok ? res.json() : null)
    .then(data => {
      if (!data || !data.token) return null;
      localStorage.setItem('token', data.token);
      return data.token;
    });
}

function toggleTheme() {
  document.body.classList.toggle('dark-theme');
  localStorage.setItem('theme', document.body.classList.contains('dark-theme') ? 'dark' : 'light');
}

document.addEventListener('DOMContentLoaded', () => {
  // Theme
  if (localStorage.getItem('theme') === 'dark') document.body.classList.add('dark-theme');
  
  loadStats();
  loadRecentActivity();
  setInterval(loadStats, 30000); // Auto refresh
  
  document.getElementById('themeToggle').onclick = toggleTheme;
  
  // Side nav toggle mobile
  document.querySelector('.menu-toggle').onclick = () => document.querySelector('.sidebar').classList.toggle('active');
});

function updateChart(data) {
  // Simple canvas pie or bar - placeholder
  const ctx = document.getElementById('statsChart').getContext('2d');
  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Users', 'Unis', 'Apps'],
      datasets: [{ data: [data.total_users, data.total_universities, data.total_applications], backgroundColor: ['#007bff', '#28a745', '#ffc107'] }]
    }
  });
}
