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
    <div id="copilot-messages" class="cp-messages"></div>
    <div id="copilot-suggestions" class="cp-suggestions"></div>
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
}

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

window._cpSend = function(text){
  if(!text || _thinking) return;
  _messages.push({ role:'user', text });
  _thinking = true;
  renderMessages();
  renderSuggestions();

  fetch('/api/copilot', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({
      message: text,
      mode: _mode,
      page: location.pathname,
      lang: window.PREDIKTA_LANG || 'fr',
      history: _messages.slice(-10).map(m => ({role: m.role === 'bot' ? 'assistant' : 'user', content: m.text})),
    }),
  })
  .then(r => r.json())
  .then(data => {
    _thinking = false;
    _messages.push({ role:'bot', text: data.reply || data.error || 'Erreur.' });
    if(data.disclaimer){
      _messages.push({ role:'bot', text: t('disclaimer') });
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

/* Disclaimer */
.cp-disclaimer{
  padding:8px 16px 10px;font-size:.6rem;color:#334155;
  text-align:center;flex-shrink:0;line-height:1.5;
  border-top:1px solid rgba(26,26,69,.3);
}

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

// ── Init ─────────────────────────────────────────────────────────────────
function init(){
  injectCSS();
  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', inject);
  } else {
    inject();
  }
}

init();

})();
