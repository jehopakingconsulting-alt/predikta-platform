/**
 * ZYNORIQ COPILOT™ — MVP v1.0
 * Floating AI assistant with 4 modes, contextual suggestions, i18n
 */
(function(){
'use strict';

// ── i18n ─────────────────────────────────────────────────────────────────
const T = {
  fr:{
    title:'ZYNORIQ Copilot™',
    subtitle:'Intelligence au-delà de la prédiction',
    placeholder:'Posez votre question...',
    greeting:'Bonjour ! Je suis **ZYNORIQ Copilot™**, votre assistant IA. Choisissez un mode et posez vos questions.',
    send:'Envoyer',
    close:'Fermer',
    clear:'Effacer',
    thinking:'Copilot réfléchit...',
    disclaimer:'⚠️ Les analyses de ZYNORIQ sont statistiques et éducatives. Aucun résultat n\'est garanti. Les loteries demeurent des jeux de hasard.',
    modes:{
      lottery:'🎯 Lottery AI',
      business:'🚀 Business AI',
      analyst:'📊 Data Analyst',
      coach:'🏆 Coach',
    },
    modeDesc:{
      lottery:'Analyse prédictive des loteries',
      business:'Intelligence d\'affaires & stratégie',
      analyst:'Exploration & visualisation de données',
      coach:'Coaching & conseils personnalisés',
    },
    suggestions:{
      lottery:['Pourquoi ces numéros ?','Montre les tendances','Analyse les 30 derniers jours','Quels chiffres sont en retard ?'],
      business:['Analyse ce projet','Crée un plan 30-60-90 jours','Identifie les risques','Évalue le marché'],
      analyst:['Explique ce score','Compare avec l\'historique','Tendances par position','Distribution des sommes'],
      coach:['Comment améliorer ma stratégie ?','Quelle approche recommandes-tu ?','Explique le Box vs Straight','Guide-moi étape par étape'],
      '/analyze':['Pourquoi ces numéros ?','Montre les tendances','Analyse les 30 derniers jours'],
      '/results':['Quels États ont tiré aujourd\'hui ?','Montre les chiffres chauds','Compare Midi vs Soir'],
      '/accuracy':['Explique ce score','Compare avec l\'historique','Que signifie cette performance ?'],
      '/bizai':['Analyse ce projet','Crée un plan 30-60-90 jours','Identifie les risques'],
    },
  },
  en:{
    title:'ZYNORIQ Copilot™',
    subtitle:'Intelligence Beyond Prediction',
    placeholder:'Ask your question...',
    greeting:'Hello! I\'m **ZYNORIQ Copilot™**, your AI assistant. Choose a mode and ask away.',
    send:'Send',
    close:'Close',
    clear:'Clear',
    thinking:'Copilot is thinking...',
    disclaimer:'⚠️ ZYNORIQ analyses are statistical and educational. No result is guaranteed. Lotteries remain games of chance.',
    modes:{
      lottery:'🎯 Lottery AI',
      business:'🚀 Business AI',
      analyst:'📊 Data Analyst',
      coach:'🏆 Coach',
    },
    modeDesc:{
      lottery:'Predictive lottery analysis',
      business:'Business intelligence & strategy',
      analyst:'Data exploration & visualization',
      coach:'Coaching & personalized advice',
    },
    suggestions:{
      lottery:['Why these numbers?','Show trends','Analyze last 30 days','Which digits are overdue?'],
      business:['Analyze this project','Create 30-60-90 day plan','Identify risks','Evaluate the market'],
      analyst:['Explain this score','Compare with history','Trends by position','Sum distribution'],
      coach:['How to improve my strategy?','What approach do you recommend?','Explain Box vs Straight','Guide me step by step'],
      '/analyze':['Why these numbers?','Show trends','Analyze last 30 days'],
      '/results':['Which states drew today?','Show hot digits','Compare Midday vs Evening'],
      '/accuracy':['Explain this score','Compare with history','What does this performance mean?'],
      '/bizai':['Analyze this project','Create 30-60-90 day plan','Identify risks'],
    },
  },
  es:{
    title:'ZYNORIQ Copilot™',
    subtitle:'Inteligencia más allá de la predicción',
    placeholder:'Haz tu pregunta...',
    greeting:'¡Hola! Soy **ZYNORIQ Copilot™**, tu asistente IA. Elige un modo y pregunta.',
    send:'Enviar',
    close:'Cerrar',
    clear:'Borrar',
    thinking:'Copilot está pensando...',
    disclaimer:'⚠️ Los análisis de ZYNORIQ son estadísticos y educativos. Ningún resultado está garantizado. Las loterías siguen siendo juegos de azar.',
    modes:{
      lottery:'🎯 Lottery AI',
      business:'🚀 Business AI',
      analyst:'📊 Data Analyst',
      coach:'🏆 Coach',
    },
    modeDesc:{
      lottery:'Análisis predictivo de loterías',
      business:'Inteligencia de negocios y estrategia',
      analyst:'Exploración y visualización de datos',
      coach:'Coaching y consejos personalizados',
    },
    suggestions:{
      lottery:['¿Por qué estos números?','Muestra tendencias','Analiza los últimos 30 días','¿Qué dígitos están atrasados?'],
      business:['Analiza este proyecto','Crea plan 30-60-90 días','Identifica riesgos','Evalúa el mercado'],
      analyst:['Explica este puntaje','Compara con historial','Tendencias por posición','Distribución de sumas'],
      coach:['¿Cómo mejorar mi estrategia?','¿Qué enfoque recomiendas?','Explica Box vs Straight','Guíame paso a paso'],
      '/analyze':['¿Por qué estos números?','Muestra tendencias','Analiza los últimos 30 días'],
      '/results':['¿Qué estados sortearon hoy?','Muestra dígitos calientes','Compara Mediodía vs Noche'],
      '/accuracy':['Explica este puntaje','Compara con historial','¿Qué significa este rendimiento?'],
      '/bizai':['Analiza este proyecto','Crea plan 30-60-90 días','Identifica riesgos'],
    },
  },
  pt:{
    title:'ZYNORIQ Copilot™',
    subtitle:'Inteligência além da previsão',
    placeholder:'Faça sua pergunta...',
    greeting:'Olá! Sou o **ZYNORIQ Copilot™**, seu assistente IA. Escolha um modo e pergunte.',
    send:'Enviar',
    close:'Fechar',
    clear:'Limpar',
    thinking:'Copilot está pensando...',
    disclaimer:'⚠️ As análises da ZYNORIQ são estatísticas e educativas. Nenhum resultado é garantido. As loterias continuam sendo jogos de azar.',
    modes:{ lottery:'🎯 Lottery AI', business:'🚀 Business AI', analyst:'📊 Data Analyst', coach:'🏆 Coach' },
    modeDesc:{ lottery:'Análise preditiva de loterias', business:'Inteligência de negócios', analyst:'Exploração de dados', coach:'Coaching personalizado' },
    suggestions:{
      lottery:['Por que esses números?','Mostre tendências','Analise os últimos 30 dias','Quais dígitos estão atrasados?'],
      business:['Analise este projeto','Crie plano 30-60-90 dias','Identifique riscos','Avalie o mercado'],
      analyst:['Explique esta pontuação','Compare com histórico','Tendências por posição','Distribuição de somas'],
      coach:['Como melhorar minha estratégia?','Que abordagem recomenda?','Explique Box vs Straight','Guie-me passo a passo'],
      '/analyze':['Por que esses números?','Mostre tendências','Analise os últimos 30 dias'],
      '/results':['Quais estados sortearam hoje?','Mostre dígitos quentes','Compare Meio-dia vs Noite'],
      '/accuracy':['Explique esta pontuação','Compare com histórico','O que significa esse desempenho?'],
      '/bizai':['Analise este projeto','Crie plano 30-60-90 dias','Identifique riscos'],
    },
  },
  ht:{
    title:'ZYNORIQ Copilot™',
    subtitle:'Entèlijans pi lwen pase prediksyon',
    placeholder:'Poze kesyon ou...',
    greeting:'Bonjou! Mwen se **ZYNORIQ Copilot™**, asistan IA ou. Chwazi yon mòd epi poze kesyon ou.',
    send:'Voye',
    close:'Fèmen',
    clear:'Efase',
    thinking:'Copilot ap reflechi...',
    disclaimer:'⚠️ Analiz ZYNORIQ se estatistik ak edikasyon. Pa gen okenn rezilta garanti. Lotri yo rete jwèt aza.',
    modes:{ lottery:'🎯 Lottery AI', business:'🚀 Business AI', analyst:'📊 Data Analyst', coach:'🏆 Coach' },
    modeDesc:{ lottery:'Analiz prediksyon lotri', business:'Entèlijans biznis', analyst:'Eksplorasyon done', coach:'Coaching pèsonalize' },
    suggestions:{
      lottery:['Poukisa nimewo sa yo?','Montre tandans','Analize 30 dènye jou yo','Ki chif ki an reta?'],
      business:['Analize pwojè sa a','Kreye plan 30-60-90 jou','Idantifye risk','Evalye mache a'],
      analyst:['Eksplike nòt sa a','Konpare ak istwa','Tandans pa pozisyon','Distribisyon sòm'],
      coach:['Kijan pou amelyore estrateji mwen?','Ki apwòch ou rekòmande?','Eksplike Box vs Straight','Gide mwen etap pa etap'],
      '/analyze':['Poukisa nimewo sa yo?','Montre tandans','Analize 30 dènye jou yo'],
      '/results':['Ki eta ki tire jodi a?','Montre chif cho','Konpare Midi vs Swa'],
      '/accuracy':['Eksplike nòt sa a','Konpare ak istwa','Kisa pèfòmans sa a vle di?'],
      '/bizai':['Analize pwojè sa a','Kreye plan 30-60-90 jou','Idantifye risk'],
    },
  },
};

function t(k){ return (T[window.PREDIKTA_LANG] || T.en)[k] || (T.en)[k] || k; }
function tMode(k){ return (t('modes')|| {})[k] || k; }
function tModeDesc(k){ return (t('modeDesc')|| {})[k] || ''; }

// ── State ────────────────────────────────────────────────────────────────
let _open = false;
let _mode = 'lottery';
let _messages = [];
let _thinking = false;

// ── Detect page context ──────────────────────────────────────────────────
function getPageContext(){
  const p = location.pathname;
  if(p.startsWith('/analyze') || p === '/') return '/analyze';
  if(p.startsWith('/results')) return '/results';
  if(p.startsWith('/accuracy') || p.startsWith('/track-record')) return '/accuracy';
  if(p.startsWith('/bizai') || p.startsWith('/business')) return '/bizai';
  return null;
}

function getSuggestions(){
  const sug = t('suggestions') || {};
  const page = getPageContext();
  if(page && sug[page]) return sug[page];
  return sug[_mode] || sug.lottery || [];
}

// ── Render helpers ───────────────────────────────────────────────────────
function md(text){
  return text
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>');
}

function renderMessages(){
  const c = document.getElementById('copilot-messages');
  if(!c) return;
  c.innerHTML = _messages.map(m => `
    <div class="cp-msg cp-msg-${m.role}">
      <div class="cp-msg-avatar">${m.role === 'bot' ? '🤖' : '👤'}</div>
      <div class="cp-msg-bubble">${md(m.text)}</div>
    </div>
  `).join('');
  if(_thinking){
    c.innerHTML += `<div class="cp-msg cp-msg-bot"><div class="cp-msg-avatar">🤖</div><div class="cp-msg-bubble cp-thinking"><span></span><span></span><span></span></div></div>`;
  }
  c.scrollTop = c.scrollHeight;
}

function renderSuggestions(){
  const c = document.getElementById('copilot-suggestions');
  if(!c) return;
  const sugs = getSuggestions();
  c.innerHTML = sugs.map(s => `<button class="cp-sug-btn" onclick="window._cpSend('${s.replace(/'/g,"\\'")}')">${s}</button>`).join('');
}

function renderModes(){
  const c = document.getElementById('copilot-modes');
  if(!c) return;
  const modes = ['lottery','business','analyst','coach'];
  c.innerHTML = modes.map(m => `
    <button class="cp-mode-btn ${m === _mode ? 'active' : ''}" onclick="window._cpSetMode('${m}')" title="${tModeDesc(m)}">
      ${tMode(m)}
    </button>
  `).join('');
}

// ── Inject DOM ───────────────────────────────────────────────────────────
function inject(){
  if(document.getElementById('copilot-fab')) return;

  // FAB button
  const fab = document.createElement('button');
  fab.id = 'copilot-fab';
  fab.innerHTML = '<span class="cp-fab-icon">🤖</span><span class="cp-fab-label">Copilot</span>';
  fab.onclick = toggle;
  document.body.appendChild(fab);

  // Panel
  const panel = document.createElement('div');
  panel.id = 'copilot-panel';
  panel.className = 'cp-closed';
  panel.innerHTML = `
    <div class="cp-header">
      <div class="cp-header-left">
        <div class="cp-logo">🤖</div>
        <div>
          <div class="cp-title">${t('title')}</div>
          <div class="cp-subtitle">${t('subtitle')}</div>
        </div>
      </div>
      <div class="cp-header-actions">
        <button class="cp-btn-icon" onclick="window._cpClear()" title="${t('clear')}">🗑️</button>
        <button class="cp-btn-icon" onclick="window._cpToggle()" title="${t('close')}">✕</button>
      </div>
    </div>
    <div id="copilot-modes" class="cp-modes"></div>
    <div id="copilot-agents" class="cp-agents"></div>
    <div id="copilot-messages" class="cp-messages"></div>
    <div id="copilot-suggestions" class="cp-suggestions"></div>
    <div class="cp-actions-bar">
      <button class="cp-action-btn" onclick="window._cpGenerateReport()" id="cp-report-btn">📄 PDF Report</button>
      <button class="cp-action-btn" onclick="window._cpCopySummary()">📋 Copy</button>
    </div>
    <div class="cp-input-bar">
      <input type="text" id="copilot-input" placeholder="${t('placeholder')}" autocomplete="off"/>
      <button id="copilot-send" onclick="window._cpSendInput()">${t('send')}</button>
    </div>
    <div class="cp-disclaimer">${t('disclaimer')}</div>
  `;
  document.body.appendChild(panel);

  // Enter key
  document.getElementById('copilot-input').addEventListener('keydown', e => {
    if(e.key === 'Enter' && !e.shiftKey){ e.preventDefault(); window._cpSendInput(); }
  });

  // Init
  _messages = [{ role:'bot', text: t('greeting') }];
  renderModes();
  renderMessages();
  renderSuggestions();
  loadAgents();
}

// ── Agents ───────────────────────────────────────────────────────────────
let _agents = [];
let _activeAgent = null;

function loadAgents(){
  fetch('/api/agents?lang='+(window.PREDIKTA_LANG||'fr'))
    .then(r=>r.json())
    .then(data=>{
      _agents = data.agents || [];
      renderAgents();
    }).catch(()=>{});
}

function renderAgents(){
  const c = document.getElementById('copilot-agents');
  if(!c || !_agents.length) return;
  c.innerHTML = _agents.map(a => `
    <button class="cp-agent-btn ${_activeAgent===a.id?'active':''}" onclick="window._cpSetAgent('${a.id}')" title="${a.description}">
      ${a.icon} ${a.name}
    </button>
  `).join('');
}

window._cpSetAgent = function(id){
  if(_activeAgent === id){ _activeAgent = null; } else { _activeAgent = id; }
  renderAgents();
  if(_activeAgent){
    const a = _agents.find(x=>x.id===id);
    if(a) _messages.push({role:'bot', text:`**${a.icon} ${a.name}** active. Posez votre question, cet agent specialise va analyser vos donnees.`});
  } else {
    _messages.push({role:'bot', text:'Agent desactive. Retour au mode Copilot standard.'});
  }
  renderMessages();
};

// ── Actions ──────────────────────────────────────────────────────────────
function toggle(){
  _open = !_open;
  const p = document.getElementById('copilot-panel');
  const f = document.getElementById('copilot-fab');
  if(p) p.className = _open ? 'cp-open' : 'cp-closed';
  if(f) f.classList.toggle('cp-fab-hidden', _open);
}

window._cpToggle = toggle;

window._cpSetMode = function(m){
  _mode = m;
  renderModes();
  renderSuggestions();
  const lang = T[window.PREDIKTA_LANG] || T.en;
  const desc = (lang.modeDesc || {})[m] || '';
  _messages.push({ role:'bot', text: `**${tMode(m)}** — ${desc}` });
  renderMessages();
};

window._cpClear = function(){
  _messages = [{ role:'bot', text: t('greeting') }];
  renderMessages();
  renderSuggestions();
};

// ── Context Gathering Service ─────────────────────────────────────────
function gatherPageContext(){
  const ctx = {};
  const p = location.pathname;

  // State detection
  const stateEl = document.querySelector('[data-state]');
  if(stateEl) ctx.state = stateEl.dataset.state;
  if(!ctx.state && window._allData){
    const keys = Object.keys(window._allData);
    if(keys.length === 1) ctx.state = keys[0];
  }
  // From URL param
  const urlState = new URLSearchParams(location.search).get('state');
  if(urlState) ctx.state = urlState;

  // Game / TOD detection
  const todEl = document.querySelector('.tod-active, [data-tod].active');
  if(todEl) ctx.tod = todEl.dataset.tod || todEl.textContent.trim();

  // Predictions on page (from consensus cards)
  const predCards = document.querySelectorAll('.combo-card, .pred-card, [data-combo]');
  if(predCards.length){
    ctx.predictions = Array.from(predCards).slice(0,5).map((c,i) => ({
      combo: c.dataset.combo || c.querySelector('.combo-text,.combo')?.textContent?.trim() || '',
      confidence: parseFloat(c.querySelector('.conf-pct,.pct')?.textContent) || 0,
      rank: i+1,
    }));
  }

  // Hot/cold digits
  const hotEl = document.querySelectorAll('.digit-hot, .hot-digit');
  const coldEl = document.querySelectorAll('.digit-cold, .cold-digit');
  if(hotEl.length) ctx.hot_digits = Array.from(hotEl).map(e => e.textContent.trim()).join(', ');
  if(coldEl.length) ctx.cold_digits = Array.from(coldEl).map(e => e.textContent.trim()).join(', ');

  // Accuracy data
  const accEl = document.querySelector('[data-straight-rate]');
  if(accEl) ctx.accuracy = {
    straight_rate: accEl.dataset.straightRate,
    box_rate: accEl.dataset.boxRate,
  };

  // Active filters
  const activeFilters = document.querySelectorAll('.qf-btn.active, .filter-btn.active');
  if(activeFilters.length){
    ctx.filters = Array.from(activeFilters).map(b => b.textContent.trim());
  }

  // Business AI project
  const bizName = document.querySelector('#projectName, [data-project-name]');
  const bizScore = document.querySelector('#projectScore, [data-project-score]');
  if(bizName) ctx.business = {
    name: bizName.value || bizName.textContent?.trim(),
    score: bizScore?.textContent?.trim() || '',
  };

  return ctx;
}

window._cpSend = function(text){
  if(!text || _thinking) return;
  _messages.push({ role:'user', text });
  _thinking = true;
  renderMessages();
  renderSuggestions();

  const ctx = gatherPageContext();
  const lang = window.PREDIKTA_LANG || 'fr';
  const hist = _messages.slice(-10).map(m => ({role: m.role === 'bot' ? 'assistant' : 'user', content: m.text}));

  // Route to Agent or Copilot
  const endpoint = _activeAgent ? '/api/agents/run' : '/api/copilot';
  const payload = _activeAgent
    ? { agent: _activeAgent, message: text, page: location.pathname, lang, history: hist, context: ctx }
    : { message: text, mode: _mode, page: location.pathname, lang, history: hist, context: ctx };

  fetch(endpoint, {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify(payload),
  })
  .then(r => r.json())
  .then(data => {
    _thinking = false;
    const prefix = data.agent_icon ? `${data.agent_icon} **${data.agent_name}**\n\n` : '';
    _messages.push({ role:'bot', text: prefix + (data.reply || data.error || 'Erreur.') });
    if(data.disclaimer){
      _messages.push({ role:'bot', text: t('disclaimer') });
    }
    // Show quota remaining
    if(data.quota && data.quota.remaining <= 3 && data.quota.remaining > 0){
      _messages.push({ role:'bot', text: `⚠️ ${data.quota.remaining}/${data.quota.limit} questions restantes aujourd'hui.` });
    }
    renderMessages();
  })
  .catch(() => {
    _thinking = false;
    _messages.push({ role:'bot', text: '❌ Erreur de connexion. Réessayez.' });
    renderMessages();
  });
};

window._cpSendInput = function(){
  const inp = document.getElementById('copilot-input');
  if(!inp) return;
  const text = inp.value.trim();
  if(!text) return;
  inp.value = '';
  window._cpSend(text);
};

// ── PDF Report Generation ────────────────────────────────────────────────
window._cpGenerateReport = function(){
  const btn = document.getElementById('cp-report-btn');
  if(!btn || btn.disabled) return;
  btn.disabled = true;
  btn.textContent = '⏳ ...';

  const ctx = gatherPageContext();
  const lastBotMsg = _messages.filter(m => m.role === 'bot').slice(-1)[0];
  const analysis = lastBotMsg ? lastBotMsg.text : '';

  // Detect report type from mode
  const typeMap = {lottery:'prediction', business:'business', analyst:'accuracy', coach:'trend'};
  const reportType = typeMap[_mode] || 'prediction';

  fetch('/api/copilot/report', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({
      report_type: reportType,
      lang: window.PREDIKTA_LANG || 'fr',
      page: location.pathname,
      context: ctx,
      analysis: analysis,
    }),
  })
  .then(r => r.json())
  .then(data => {
    btn.disabled = false;
    btn.textContent = '📄 PDF Report';
    if(data.error === 'quota_exceeded'){
      _messages.push({ role:'bot', text: `⚠️ Limite de rapports atteinte (${data.limit}/mois). Passe au plan supérieur.` });
    } else if(data.download_url){
      _messages.push({ role:'bot', text: `✅ **Rapport PDF généré !**\n\n[📥 Télécharger le rapport](${data.download_url})\n\nQuota: ${data.quota.remaining}/${data.quota.limit} rapports restants ce mois.` });
      // Auto-download
      const a = document.createElement('a');
      a.href = data.download_url;
      a.download = '';
      document.body.appendChild(a);
      a.click();
      a.remove();
    } else {
      _messages.push({ role:'bot', text: '❌ Erreur lors de la génération du rapport.' });
    }
    renderMessages();
  })
  .catch(() => {
    btn.disabled = false;
    btn.textContent = '📄 PDF Report';
    _messages.push({ role:'bot', text: '❌ Erreur de connexion.' });
    renderMessages();
  });
};

// ── Copy Summary ─────────────────────────────────────────────────────────
window._cpCopySummary = function(){
  const botMsgs = _messages.filter(m => m.role === 'bot').map(m => m.text);
  const text = botMsgs.join('\n\n');
  if(navigator.clipboard){
    navigator.clipboard.writeText(text).then(() => {
      _messages.push({ role:'bot', text: '✅ Résumé copié dans le presse-papiers.' });
      renderMessages();
    });
  }
};

// ── Refresh on lang change ───────────────────────────────────────────────
window._copilotLangRefresh = function(){
  const p = document.getElementById('copilot-panel');
  if(!p) return;
  p.querySelector('.cp-title').textContent = t('title');
  p.querySelector('.cp-subtitle').textContent = t('subtitle');
  p.querySelector('.cp-disclaimer').textContent = t('disclaimer');
  document.getElementById('copilot-input').placeholder = t('placeholder');
  document.getElementById('copilot-send').textContent = t('send');
  renderModes();
  renderSuggestions();
};

// ── CSS ──────────────────────────────────────────────────────────────────
function injectCSS(){
  const style = document.createElement('style');
  style.textContent = `
/* ── ZYNORIQ COPILOT™ ──────────────────────────────────────── */
#copilot-fab{
  position:fixed;bottom:24px;right:24px;z-index:9999;
  display:flex;align-items:center;gap:8px;
  padding:14px 22px;border-radius:50px;border:1px solid #1a1a45;
  background:linear-gradient(135deg,#0b0b22,#111135);
  color:#e8eeff;font-size:.82rem;font-weight:700;
  cursor:pointer;box-shadow:0 8px 32px rgba(20,121,255,.3),0 0 0 1px rgba(20,121,255,.15);
  transition:all .3s;font-family:'Inter',sans-serif;
}
#copilot-fab:hover{
  box-shadow:0 8px 40px rgba(20,121,255,.5),0 0 0 1px rgba(20,121,255,.3);
  transform:translateY(-2px);
}
#copilot-fab.cp-fab-hidden{
  transform:translateY(100px);opacity:0;pointer-events:none;
}
.cp-fab-icon{font-size:1.2rem}
.cp-fab-label{letter-spacing:.5px}

/* Panel */
#copilot-panel{
  position:fixed;bottom:0;right:0;z-index:10000;
  width:420px;max-width:100vw;height:85vh;max-height:700px;
  background:#08081f;border:1px solid #1a1a45;
  border-radius:20px 20px 0 0;
  display:flex;flex-direction:column;
  box-shadow:0 -8px 60px rgba(0,0,0,.6),0 0 0 1px rgba(20,121,255,.1);
  font-family:'Inter',sans-serif;
  transition:transform .35s cubic-bezier(.4,0,.2,1),opacity .25s;
}
#copilot-panel.cp-closed{
  transform:translateY(110%);opacity:0;pointer-events:none;
}
#copilot-panel.cp-open{
  transform:translateY(0);opacity:1;
}

/* Header */
.cp-header{
  display:flex;align-items:center;justify-content:space-between;
  padding:16px 20px;border-bottom:1px solid #1a1a45;
  background:linear-gradient(135deg,#0d0d2e,#111140);
  border-radius:20px 20px 0 0;flex-shrink:0;
}
.cp-header-left{display:flex;align-items:center;gap:12px}
.cp-logo{font-size:1.6rem}
.cp-title{
  font-size:.92rem;font-weight:800;letter-spacing:.5px;
  background:linear-gradient(135deg,#1479FF,#ffd700);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
}
.cp-subtitle{font-size:.65rem;color:#4d5a8a;margin-top:2px}
.cp-header-actions{display:flex;gap:6px}
.cp-btn-icon{
  width:32px;height:32px;border-radius:8px;border:1px solid #1a1a45;
  background:transparent;color:#4d5a8a;font-size:.9rem;cursor:pointer;
  display:flex;align-items:center;justify-content:center;transition:all .2s;
}
.cp-btn-icon:hover{background:#1a1a45;color:#e8eeff}

/* Modes */
.cp-modes{
  display:flex;gap:6px;padding:12px 16px;flex-shrink:0;overflow-x:auto;
  border-bottom:1px solid rgba(26,26,69,.6);
}
.cp-mode-btn{
  padding:6px 14px;border-radius:20px;font-size:.68rem;font-weight:700;
  border:1px solid #1a1a45;background:transparent;color:#4d5a8a;
  cursor:pointer;white-space:nowrap;transition:all .2s;
}
.cp-mode-btn:hover{border-color:#1479FF;color:#e8eeff}
.cp-mode-btn.active{
  background:linear-gradient(135deg,#1479FF,#004DFF);
  border-color:#1479FF;color:#fff;
}

/* Agents */
.cp-agents{
  display:flex;gap:4px;padding:6px 16px;flex-shrink:0;overflow-x:auto;
  border-bottom:1px solid rgba(26,26,69,.4);
}
.cp-agent-btn{
  padding:4px 10px;border-radius:14px;font-size:.62rem;font-weight:700;
  border:1px solid rgba(255,215,0,.2);background:rgba(255,215,0,.05);
  color:#8892b0;cursor:pointer;white-space:nowrap;transition:all .2s;
}
.cp-agent-btn:hover{border-color:#ffd700;color:#ffd700}
.cp-agent-btn.active{
  background:linear-gradient(135deg,rgba(255,215,0,.2),rgba(255,170,0,.15));
  border-color:#ffd700;color:#ffd700;
}

/* Messages */
.cp-messages{
  flex:1;overflow-y:auto;padding:16px;
  display:flex;flex-direction:column;gap:12px;
}
.cp-msg{display:flex;gap:10px;max-width:92%}
.cp-msg-bot{align-self:flex-start}
.cp-msg-user{align-self:flex-end;flex-direction:row-reverse}
.cp-msg-avatar{
  width:28px;height:28px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  font-size:.85rem;flex-shrink:0;
  background:rgba(20,121,255,.15);border:1px solid rgba(20,121,255,.3);
}
.cp-msg-user .cp-msg-avatar{
  background:rgba(255,215,0,.15);border-color:rgba(255,215,0,.3);
}
.cp-msg-bubble{
  padding:10px 14px;border-radius:14px;font-size:.8rem;line-height:1.6;color:#e8eeff;
  background:#0e0e2a;border:1px solid #1a1a45;
}
.cp-msg-user .cp-msg-bubble{
  background:linear-gradient(135deg,rgba(20,121,255,.15),rgba(0,77,255,.1));
  border-color:rgba(20,121,255,.3);
}
.cp-msg-bubble strong{color:#1479FF}

/* Thinking animation */
.cp-thinking{display:flex;gap:4px;padding:12px 18px}
.cp-thinking span{
  width:8px;height:8px;border-radius:50%;background:#1479FF;
  animation:cpDot 1.2s ease-in-out infinite;
}
.cp-thinking span:nth-child(2){animation-delay:.2s}
.cp-thinking span:nth-child(3){animation-delay:.4s}
@keyframes cpDot{0%,100%{opacity:.3;transform:scale(.8)}50%{opacity:1;transform:scale(1.1)}}

/* Suggestions */
.cp-suggestions{
  display:flex;flex-wrap:wrap;gap:6px;padding:8px 16px;flex-shrink:0;
  border-top:1px solid rgba(26,26,69,.6);
}
.cp-sug-btn{
  padding:6px 12px;border-radius:16px;font-size:.68rem;font-weight:600;
  border:1px solid rgba(20,121,255,.3);background:rgba(20,121,255,.08);
  color:#88aaff;cursor:pointer;transition:all .2s;white-space:nowrap;
}
.cp-sug-btn:hover{background:rgba(20,121,255,.2);color:#e8eeff;border-color:#1479FF}

/* Input bar */
.cp-input-bar{
  display:flex;gap:8px;padding:12px 16px;flex-shrink:0;
  border-top:1px solid #1a1a45;background:rgba(8,8,31,.95);
}
#copilot-input{
  flex:1;padding:10px 14px;border-radius:12px;
  border:1px solid #1a1a45;background:#0c0c28;
  color:#e8eeff;font-size:.82rem;outline:none;
  font-family:'Inter',sans-serif;transition:border-color .2s;
}
#copilot-input:focus{border-color:#1479FF}
#copilot-input::placeholder{color:#4d5a8a}
#copilot-send{
  padding:10px 18px;border-radius:12px;font-size:.78rem;font-weight:700;
  background:linear-gradient(135deg,#1479FF,#004DFF);
  color:#fff;border:none;cursor:pointer;transition:opacity .2s;
  white-space:nowrap;
}
#copilot-send:hover{opacity:.85}

/* Actions bar */
.cp-actions-bar{
  display:flex;gap:6px;padding:8px 16px;flex-shrink:0;
  border-top:1px solid rgba(26,26,69,.6);
}
.cp-action-btn{
  flex:1;padding:8px 12px;border-radius:10px;font-size:.72rem;font-weight:700;
  border:1px solid rgba(20,121,255,.3);background:rgba(20,121,255,.08);
  color:#88aaff;cursor:pointer;transition:all .2s;text-align:center;
}
.cp-action-btn:hover{background:rgba(20,121,255,.2);color:#e8eeff;border-color:#1479FF}
.cp-action-btn:disabled{opacity:.5;cursor:wait}

/* Disclaimer */
.cp-disclaimer{
  padding:8px 16px 10px;font-size:.6rem;color:#334155;
  text-align:center;flex-shrink:0;line-height:1.5;
  border-top:1px solid rgba(26,26,69,.3);
}

/* Links in messages */
.cp-msg-bubble a{color:#1479FF;text-decoration:underline}

/* Scrollbar */
.cp-messages::-webkit-scrollbar{width:4px}
.cp-messages::-webkit-scrollbar-track{background:transparent}
.cp-messages::-webkit-scrollbar-thumb{background:#1a1a45;border-radius:4px}

/* ── Responsive ─────────────────────────────────────── */
@media(max-width:480px){
  #copilot-panel{width:100vw;height:100vh;max-height:100vh;border-radius:0}
  #copilot-fab{bottom:80px;right:12px;padding:12px 16px;font-size:.75rem}
  .cp-header{border-radius:0}
  .cp-fab-label{display:none}
}
@media(min-width:481px) and (max-width:768px){
  #copilot-panel{width:380px;height:80vh}
  #copilot-fab{bottom:80px;right:16px}
}
`;
  document.head.appendChild(style);
}

// ── Memory™ Activity Tracking ────────────────────────────────────────────
function trackPageVisit(){
  try {
    const ctx = gatherPageContext();
    fetch('/api/memory/track', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({
        type: 'page_visit',
        page: location.pathname,
        state: ctx.state || null,
        game: ctx.game || null,
      }),
    }).catch(()=>{});
  } catch(e){}
}

// ── Init ─────────────────────────────────────────────────────────────────
function init(){
  injectCSS();
  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', ()=>{ inject(); trackPageVisit(); });
  } else {
    inject();
    trackPageVisit();
  }
}

init();

})();
