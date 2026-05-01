// State Management
let currentUser = null;
let currentChatId = null;
let latestCvExtractedText = '';
let latestCvAnalysis = null;

// Auth Forms
const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');
const logoutBtn = document.getElementById('logout-btn');

// Sections
const authSection = document.getElementById('auth-section');
const appNav = document.getElementById('app-nav');
const userInfo = document.getElementById('user-info');
const usernameDisplay = document.getElementById('username-display');
const pages = document.querySelectorAll('.page');

// Profile Form
const resultsForm = document.getElementById('results-form');
const publicFields = document.getElementById('public-fields');
const americanFields = document.getElementById('american-fields');
const privateFields = document.getElementById('private-fields');
const regSchoolType = document.getElementById('reg-school-type');

// Matching & Search
const findMatchesBtn = document.getElementById('find-matches-btn');
const matchesList = document.getElementById('matches-list');

// Chat
const chatMessages = document.getElementById('chat-messages');
const chatInputText = document.getElementById('chat-input-text');
const sendChatBtn = document.getElementById('send-chat-btn');
const cvAnalyzerForm = document.getElementById('cv-analyzer-form');
const cvFileInput = document.getElementById('cv-file');
const targetUniversityInput = document.getElementById('target-university');
const cvActions = document.getElementById('cv-actions');
const cvAnalysisOutput = document.getElementById('cv-analysis-output');
const cvImprovedOutput = document.getElementById('cv-improved-output');
const improveCvBtn = document.getElementById('improve-cv-btn');
const generateTemplateBtn = document.getElementById('generate-template-btn');

// --- Navigation ---
function showTab(tab) {
    if (tab === 'login') {
        loginForm.classList.remove('hidden');
        registerForm.classList.add('hidden');
        document.querySelectorAll('.tab-btn')[0].classList.add('active');
        document.querySelectorAll('.tab-btn')[1].classList.remove('active');
    } else {
        loginForm.classList.add('hidden');
        registerForm.classList.remove('hidden');
        document.querySelectorAll('.tab-btn')[0].classList.remove('active');
        document.querySelectorAll('.tab-btn')[1].classList.add('active');
    }
}

function navigateTo(pageId) {
    // Hide all pages
    pages.forEach(page => page.classList.add('hidden'));
    
    // Show requested page
    const targetPage = document.getElementById(`${pageId}-page`);
    if (targetPage) {
        targetPage.classList.remove('hidden');
    }

    // Update active state in nav
    document.querySelectorAll('.nav-link').forEach(link => {
        if (link.innerText.toLowerCase().includes(pageId)) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });

    // Load specific data if needed
    if (pageId === 'dashboard') loadApplications();
    if (pageId === 'search') findMatchesBtn.click(); // Auto-refresh matches when visiting search
}

// --- Auth ---
loginForm.onsubmit = async (e) => {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
const data = await response.json();
        if (response.ok) {
            localStorage.setItem('token', data.token);
            currentUser = data;
            if (data.role === 'admin') {
                window.location.href = '/admin';
                return;
            }
            loginSuccess();
        } else {
            alert(data.message);
        }
    } catch (err) {
        console.error('Login failed:', err);
    }
};

registerForm.onsubmit = async (e) => {
    e.preventDefault();
    const name = document.getElementById('reg-name').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;
    const school_type = document.getElementById('reg-school-type').value;

    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password, school_type })
        });
        const data = await response.json();
        if (response.ok) {
            alert('Registration successful! Please login.');
            showTab('login');
        } else {
            alert(data.message);
        }
    } catch (err) {
        console.error('Registration failed:', err);
    }
};

function loginSuccess() {
    authSection.classList.add('hidden');
    appNav.classList.remove('hidden');
    userInfo.classList.remove('hidden');
    usernameDisplay.innerText = `User ID: ${currentUser.user_id}`;
    
    // Show correct fields based on school type
    publicFields.classList.add('hidden');
    americanFields.classList.add('hidden');
    privateFields.classList.add('hidden');
    
    const type = currentUser.school_type || 'public';
    if (type === 'public') publicFields.classList.remove('hidden');
    else if (type === 'american') americanFields.classList.remove('hidden');
    else if (type === 'private') privateFields.classList.remove('hidden');
    
    navigateTo('dashboard');
}

logoutBtn.onclick = () => {
    localStorage.removeItem('token');
    currentUser = null;
    location.reload();
};

// --- Profile ---
resultsForm.onsubmit = async (e) => {
    e.preventDefault();
    const schoolType = currentUser.school_type || 'public';
    let payload = {
        student_id: currentUser.user_id,
        school_type: schoolType
    };

    if (schoolType === 'public') {
        payload.national_exam_score = parseFloat(document.getElementById('national-score').value);
        payload.exam_year = document.getElementById('exam-year').value;
    } else if (schoolType === 'american') {
        payload.gpa = parseFloat(document.getElementById('gpa').value);
        payload.sat_score = parseInt(document.getElementById('sat-score').value);
    } else if (schoolType === 'private') {
        payload.curriculum = document.getElementById('curriculum').value;
        payload.ib_score = parseFloat(document.getElementById('ib-score').value);
    }

    try {
        const response = await fetch('/api/profile/results', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        alert(data.message);
        // Refresh matches if on search page
        if (!document.getElementById('search-page').classList.contains('hidden')) {
            findMatchesBtn.click();
        }
    } catch (err) {
        console.error('Update results failed:', err);
    }
};

// --- Matching ---
findMatchesBtn.onclick = async () => {
    try {
        const response = await fetch('/api/search/match', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ student_id: currentUser.user_id })
        });
        const data = await response.json();
        displayMatches(data);
    } catch (err) {
        console.error('Matching failed:', err);
    }
};

function displayMatches(matches) {
    matchesList.innerHTML = '';
    if (matches.length === 0) {
        matchesList.innerHTML = '<p>No matches found yet. Try updating your results.</p>';
        return;
    }

    matches.forEach(match => {
        const div = document.createElement('div');
        div.className = 'match-card';
        div.innerHTML = `
            <h4>${match.name}</h4>
            <p>Location: ${match.location} | Type: ${match.type}</p>
            <ul>
                ${match.programs.map(p => `
                    <li><strong>${p.name}</strong> - ${p.faculty} (Fees: ${p.fees} EGP) 
                    <button onclick="applyNow(${match.uni_id}, ${p.program_id})">Apply</button></li>
                `).join('')}
            </ul>
            <button onclick="startChat(${match.uni_id})">Chat with Rep</button>
        `;
        matchesList.appendChild(div);
    });
}

// --- Application ---
async function applyNow(uniId, programId) {
    try {
        const response = await fetch('/api/application/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                student_id: currentUser.user_id,
                uni_id: uniId,
                program_id: programId,
                notes: 'Applied via EDU Portal'
            })
        });
        const data = await response.json();
        alert(data.message);
        loadApplications();
    } catch (err) {
        console.error('Application failed:', err);
    }
}

async function loadApplications() {
    try {
        const response = await fetch(`/api/application/status/${currentUser.user_id}`);
        const data = await response.json();
        const appList = document.getElementById('applications-list');
        appList.innerHTML = data.map(app => `
            <div class="match-card">
                <p><strong>${app.uni_name}</strong> - ${app.program_name}</p>
                <p>Status: <span class="status-${app.status}">${app.status}</span></p>
                <p>Date: ${new Date(app.submitted_at).toLocaleDateString()}</p>
            </div>
        `).join('') || '<p>No applications submitted yet.</p>';
    } catch (err) {
        console.error('Load applications failed:', err);
    }
}

// --- Chat ---
async function startChat(uniId) {
    try {
        const response = await fetch('/api/chat/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ student_id: currentUser.user_id, uni_id: uniId })
        });
        const data = await response.json();
        currentChatId = data.chat_id;
        chatMessages.innerHTML = '<div class="message bot-msg">Connected to University Support. How can we help?</div>';
    } catch (err) {
        console.error('Chat start failed:', err);
    }
}

sendChatBtn.onclick = async () => {
    const text = chatInputText.value;
    if (!text || !currentChatId) return;

    addMessage(text, 'student-msg');
    chatInputText.value = '';

    try {
        const response = await fetch('/api/chat/message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                chat_id: currentChatId,
                sender_id: currentUser.user_id,
                content: text
            })
        });
        const data = await response.json();
        if (data.bot_response) {
            addMessage(data.bot_response, 'bot-msg');
        }
    } catch (err) {
        console.error('Send message failed:', err);
    }
};

function addMessage(text, type) {
    const div = document.createElement('div');
    div.className = `message ${type}`;
    div.innerHTML = text; // Changed from innerText to innerHTML to render links
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function loadInitialData() {
    loadApplications();
}

// --- CV Analyzer ---
cvAnalyzerForm.onsubmit = async (e) => {
    e.preventDefault();
    const file = cvFileInput.files[0];
    if (!file) {
        alert('Please choose a file first.');
        return;
    }

    const payload = new FormData();
    payload.append('file', file);
    payload.append('university_name', targetUniversityInput.value || '');

    cvAnalysisOutput.innerHTML = '<p>Analyzing file, please wait...</p>';
    cvImprovedOutput.innerHTML = '';
    cvActions.classList.add('hidden');

    try {
        const response = await fetch('/api/document-ai/analyze', {
            method: 'POST',
            body: payload
        });
        const data = await response.json();
        if (!response.ok) {
            cvAnalysisOutput.innerHTML = `<p>${data.message || 'Analysis failed.'}</p>`;
            return;
        }

        latestCvExtractedText = data.extracted_text || '';
        latestCvAnalysis = data.analysis || null;
        renderCvAnalysis(data.analysis, data.file_name);
        cvActions.classList.remove('hidden');
    } catch (err) {
        console.error('CV analysis failed:', err);
        cvAnalysisOutput.innerHTML = '<p>Analysis failed due to a network error.</p>';
    }
};

improveCvBtn.onclick = async () => {
    if (!latestCvExtractedText) {
        alert('Analyze a file first.');
        return;
    }

    cvImprovedOutput.innerHTML = '<p>Generating improved CV...</p>';
    try {
        const response = await fetch('/api/document-ai/improve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: latestCvExtractedText,
                university_name: targetUniversityInput.value || ''
            })
        });
        const data = await response.json();
        if (!response.ok) {
            cvImprovedOutput.innerHTML = `<p>${data.message || 'Failed to improve CV.'}</p>`;
            return;
        }

        const validation = (data.improvement?.validation || [])
            .map(item => `<li><strong>${item.problem}:</strong> ${item.how}</li>`)
            .join('');

        cvImprovedOutput.innerHTML = `
            <div class="match-card">
                <h4>Improved CV Draft</h4>
                <pre class="json-output">${escapeHtml(data.improvement?.improved_text || '')}</pre>
                <h4>Fix Validation</h4>
                <ul>${validation || '<li>No fixes applied.</li>'}</ul>
            </div>
        `;
    } catch (err) {
        console.error('Improve CV failed:', err);
        cvImprovedOutput.innerHTML = '<p>Could not generate improved CV.</p>';
    }
};

generateTemplateBtn.onclick = async () => {
    if (!latestCvAnalysis || !Array.isArray(latestCvAnalysis.missing) || latestCvAnalysis.missing.length === 0) {
        alert('No missing sections detected.');
        return;
    }

    try {
        const response = await fetch('/api/document-ai/template', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ missing_sections: latestCvAnalysis.missing })
        });
        const data = await response.json();
        if (!response.ok) {
            alert(data.message || 'Template generation failed.');
            return;
        }

        const templatesHtml = Object.entries(data.templates || {})
            .map(([section, template]) => `
                <div class="match-card">
                    <h4>${section}</h4>
                    <pre class="json-output">${escapeHtml(template)}</pre>
                </div>
            `)
            .join('');

        cvImprovedOutput.innerHTML = templatesHtml || '<p>No templates generated.</p>';
    } catch (err) {
        console.error('Template generation failed:', err);
        alert('Could not generate templates.');
    }
};

function renderCvAnalysis(analysis, filename) {
    const payload = {
        score: analysis?.score ?? 0,
        found: analysis?.found || [],
        missing: analysis?.missing || [],
        weakness: analysis?.weakness || [],
        issues: analysis?.issues || [],
        suggestions: analysis?.suggestions || [],
        specialization_feedback: analysis?.specialization_feedback || '',
        warnings: analysis?.warnings || []
    };

    cvAnalysisOutput.innerHTML = `
        <div class="match-card">
            <h4>Analysis Result: ${filename}</h4>
            <pre class="json-output">${escapeHtml(JSON.stringify(payload, null, 2))}</pre>
        </div>
    `;
}

function escapeHtml(value) {
    return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
}
