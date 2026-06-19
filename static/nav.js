/**
 * PREDIKTA — Navigation Universelle v4.0
 * Corrigé : Langue toujours visible · Home flottant · ↑ dès 80px · Assistant PREDIKTA
 */
(function(){
'use strict';

// ── Services ──────────────────────────────────────────────────────────────
const SERVICES = [
  { href:'/',            icon:'🏠', key:'home',       badge:'' },
  { href:'/analyze',     icon:'⚡', key:'analyze',    badge:'' },
  { href:'/results',     icon:'🎱', key:'results',    badge:'' },
  { href:'/all-results', icon:'🏆', key:'allresults', badge:'' },
  { href:'/predictions', icon:'🎯', key:'predictions', badge:'' },
  { href:'/bizai',       icon:'🚀', key:'bizai',      badge:'' },
  { href:'/archives',    icon:'📁', key:'archives',   badge:'' },
  { href:'/parrainage',  icon:'🎁', key:'referral',   badge:'' },
  { href:'/pro',         icon:'👑', key:'pro',        badge:'PRO' },
  { href:'/account',     icon:'👤', key:'account',    badge:'' },
  { href:'/world-map',   icon:'🗺️', key:'worldmap',   badge:'' },
  { href:'/predikta-tv', icon:'📺', key:'predicktatv', badge:'' },
  { href:'/community',   icon:'💬', key:'community',  badge:'' },
  { href:'/track-record',    icon:'📈', key:'trackrecord', badge:'' },
  { href:'/track-record-4',  icon:'4️⃣', key:'trackrecord4', badge:'' },
  { href:'/accuracy',        icon:'🏅', key:'accuracy',    badge:'' },
  { href:'/pick4-predictions',icon:'4️⃣', key:'pick4',      badge:'NEW' },
  { href:'/cash5',            icon:'💰', key:'cash5',      badge:'NEW' },
];

// ── Traductions ───────────────────────────────────────────────────────────
const NAV_T = {
  fr:{ home:'Accueil', analyze:'Analyser', results:'Résultats', allresults:'Tous Résultats', predictions:'Prédictions',
       bizai:'Business Intelligence', pro:'PRO', archives:'Archives', referral:'Parrainage', account:'Mon Compte', lang:'Langue', theme:'Thème', menu:'Menu',
       tagline:'Loterie & Analyse Prédictive',
       footerCopy:'© 2026 PREDIKTA — Analyses statistiques éducatives, sans garantie de gain. La loterie est un jeu de hasard (18+). Non affilié aux loteries officielles. <a href="/responsible-gaming" style="color:#7888bb">Jeu Responsable</a>.',
       about:'À Propos', faq:'FAQ', contact:'Contact', privacy:'Confidentialité', terms:'CGU', affil:'Affiliés', trackrecord:'Historique des Suggestions', trackrecord4:'Historique Pick 4', respgaming:'Jeu Responsable', accuracy:'Accuracy Score', blog:'Blog',
       worldmap:'Carte du Monde', predicktatv:'PREDIKTA TV', community:'Communauté', pick4:'Pick 4 / Cash 4', cash5:'Cash 5 / Fantasy 5',
       dashboard:'Tableau de Bord', logout:'Se déconnecter', myAccount:'Mon Compte' },
  en:{ home:'Home', analyze:'Analyze', results:'Results', allresults:'All Results', predictions:'Predictions',
       bizai:'Business Intelligence', pro:'PRO', archives:'Archives', referral:'Referral', account:'My Account', lang:'Language', theme:'Theme', menu:'Menu',
       tagline:'Lottery & Predictive Analysis',
       footerCopy:'© 2026 PREDIKTA — Educational statistical analysis, no guaranteed winnings. Lottery is gambling (18+). Not affiliated with any official lottery. <a href="/responsible-gaming" style="color:#7888bb">Responsible Gaming</a>.',
       about:'About', faq:'FAQ', contact:'Contact', privacy:'Privacy', terms:'Terms', affil:'Affiliates', trackrecord:'Track Record', trackrecord4:'Pick 4 Track Record', respgaming:'Responsible Gaming', accuracy:'Accuracy Score', blog:'Blog',
       worldmap:'World Map', predicktatv:'PREDIKTA TV', community:'Community', pick4:'Pick 4 / Cash 4', cash5:'Cash 5 / Fantasy 5',
       dashboard:'Dashboard', logout:'Sign out', myAccount:'My Account' },
  es:{ home:'Inicio', analyze:'Analizar', results:'Resultados', allresults:'Todos', predictions:'Predicciones',
       bizai:'Business Intelligence', pro:'PRO', archives:'Archivos', referral:'Referidos', account:'Mi Cuenta', lang:'Idioma', theme:'Tema', menu:'Menú',
       tagline:'Lotería & Análisis Predictivo',
       footerCopy:'© 2026 PREDIKTA — Análisis estadístico educativo, sin garantía de premio. La lotería es un juego de azar (18+). No afiliado a loterías oficiales. <a href="/responsible-gaming" style="color:#7888bb">Juego Responsable</a>.',
       about:'Acerca de', faq:'FAQ', contact:'Contacto', privacy:'Privacidad', terms:'Términos', affil:'Afiliados', trackrecord:'Historial de Sugerencias', trackrecord4:'Historial Pick 4', respgaming:'Juego Responsable', accuracy:'Accuracy Score', blog:'Blog',
       worldmap:'Mapa Mundial', predicktatv:'PREDIKTA TV', community:'Comunidad', pick4:'Pick 4 / Cash 4', cash5:'Cash 5 / Fantasy 5',
       dashboard:'Panel de Control', logout:'Cerrar sesión', myAccount:'Mi Cuenta' },
  pt:{ home:'Início', analyze:'Analisar', results:'Resultados', allresults:'Todos', predictions:'Previsões',
       bizai:'Business Intelligence', pro:'PRO', archives:'Arquivos', referral:'Indicações', account:'Minha Conta', lang:'Idioma', theme:'Tema', menu:'Menu',
       tagline:'Loteria & Análise Preditiva',
       footerCopy:'© 2026 PREDIKTA — Análise estatística educativa, sem garantia de prêmio. A loteria é um jogo de azar (18+). Não afiliado a loterias oficiais. <a href="/responsible-gaming" style="color:#7888bb">Jogo Responsável</a>.',
       about:'Sobre', faq:'FAQ', contact:'Contato', privacy:'Privacidade', terms:'Termos', affil:'Afiliados', trackrecord:'Histórico de Sugestões', trackrecord4:'Histórico Pick 4', respgaming:'Jogo Responsável', accuracy:'Accuracy Score', blog:'Blog',
       worldmap:'Mapa Mundial', predicktatv:'PREDIKTA TV', community:'Comunidade', pick4:'Pick 4 / Cash 4', cash5:'Cash 5 / Fantasy 5',
       dashboard:'Painel', logout:'Sair', myAccount:'Minha Conta' },
  ht:{ home:'Akèy', analyze:'Analize', results:'Rezilta', allresults:'Tout Rezilta', predictions:'Prediksyon',
       bizai:'Business Intelligence', pro:'PRO', archives:'Achiv', referral:'Parennaj', account:'Kont Mwen', lang:'Lang', theme:'Tèm', menu:'Meni',
       tagline:'Lotri & Analiz Biznis',
       footerCopy:'© 2026 PREDIKTA — Analiz statistik edikatif, san garanti lo. Lotri se jwèt chans (18+). Pa afilye ak lotri ofisyèl. <a href="/responsible-gaming" style="color:#7888bb">Jwe Responsab</a>.',
       about:'Sou nou', faq:'FAQ', contact:'Kontak', privacy:'Konfidans', terms:'Tèm', affil:'Afilye', trackrecord:'Istorik Sijesyon', trackrecord4:'Istorik Pick 4', respgaming:'Jwe Responsab', accuracy:'Accuracy Score', blog:'Blog',
       worldmap:'Kat Mondyal', predicktatv:'PREDIKTA TV', community:'Kominote', pick4:'Pick 4 / Cash 4', cash5:'Cash 5 / Fantasy 5',
       dashboard:'Tablo de Bò', logout:'Dekonekte', myAccount:'Kont Mwen' },
};

// ── Affiliés UTM ──────────────────────────────────────────────────────────
window.PREDIKTA_AFFILIATE = {
  thelotter:   'https://www.thelotter.com/?utm_source=predikta&utm_medium=affiliate&utm_campaign=nav',
  lotterypro:  'https://www.lotterypro.com/?utm_source=predikta&utm_medium=affiliate&utm_campaign=nav',
  jackpot:     'https://www.jackpot.com/?utm_source=predikta&utm_medium=affiliate&utm_campaign=nav',
  lottoagent:  'https://www.lottoagent.com/?utm_source=predikta&utm_medium=affiliate&utm_campaign=nav',
  lottoland:   'https://www.lottoland.com/?utm_source=predikta&utm_medium=affiliate&utm_campaign=nav',
  wintrilions: 'https://www.wintrillions.com/?utm_source=predikta&utm_medium=affiliate&utm_campaign=nav',
  multilotto:  'https://www.multilotto.com/?utm_source=predikta&utm_medium=affiliate&utm_campaign=nav',
  lotto:       'https://www.lotto.com/?utm_source=predikta&utm_medium=affiliate&utm_campaign=nav',
};

// ── Archive (historique des analyses & recherches) ─────────────────────────
// Stockage local (navigateur), aucun compte requis. Rétention par défaut :
// 30 jours (sera différenciée FREE/VIP/ELITE quand le système de comptes
// existera — VIP = 7j, ELITE = 30j).
const ARCHIVE_KEY = 'predikta_archive';
const ARCHIVE_RETENTION_DAYS = parseInt(localStorage.getItem('predikta_archive_days') || '30', 10);
const ARCHIVE_MAX_ENTRIES = 200;

function archivePurge(list){
  const cutoff = Date.now() - ARCHIVE_RETENTION_DAYS * 86400000;
  return list.filter(e => e.ts >= cutoff).slice(0, ARCHIVE_MAX_ENTRIES);
}

function archiveGetAll(){
  let list = [];
  try{ list = JSON.parse(localStorage.getItem(ARCHIVE_KEY) || '[]'); }catch(e){ list = []; }
  const purged = archivePurge(list);
  if(purged.length !== list.length){
    try{ localStorage.setItem(ARCHIVE_KEY, JSON.stringify(purged)); }catch(e){}
  }
  return purged.sort((a,b)=>b.ts-a.ts);
}

function archiveAdd(entry, silent){
  // silent=true → injected from server sync, skip dedup check and server post
  let saved = null;
  try{
    let list = [];
    try{ list = JSON.parse(localStorage.getItem(ARCHIVE_KEY) || '[]'); }catch(e){ list = []; }
    const now = Date.now();
    if(silent){
      // Server entry: add only if id not already present
      if(!list.find(e=>e.id===entry.id)){
        list.unshift(entry);
        list = archivePurge(list);
        localStorage.setItem(ARCHIVE_KEY, JSON.stringify(list));
      }
      return;
    }
    // Évite les doublons rapprochés (même type+state+tod dans les 30s)
    const dup = list.find(e => e.type===entry.type && e.state===entry.state && e.tod===entry.tod && (now - e.ts) < 30000);
    if(dup){ dup.ts = now; saved = dup; }
    else{
      saved = Object.assign({ id: now+'-'+Math.random().toString(36).slice(2,8), ts: now }, entry);
      list.unshift(saved);
    }
    list = archivePurge(list);
    localStorage.setItem(ARCHIVE_KEY, JSON.stringify(list));
  }catch(e){ /* localStorage indisponible (mode privé, etc.) */ }
  // Non-blocking server post (fire-and-forget; 401 = not logged in, ignored)
  if(saved){
    fetch('/api/dashboard/archives/sync', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({entries:[saved]})
    }).catch(()=>{});
  }
}

function archiveRemove(id){
  let list = archiveGetAll().filter(e => e.id !== id);
  try{ localStorage.setItem(ARCHIVE_KEY, JSON.stringify(list)); }catch(e){}
}

function archiveClear(){
  try{ localStorage.removeItem(ARCHIVE_KEY); }catch(e){}
}

window.PredArchive = {
  add: archiveAdd,
  getAll: archiveGetAll,
  remove: archiveRemove,
  clear: archiveClear,
  retentionDays: ARCHIVE_RETENTION_DAYS,
};

// ── Parrainage : capture du code ?ref=XXXX dans l'URL ──────────────────────
// Stocké pour être attaché à la prochaine inscription newsletter, quel que
// soit le point d'entrée du visiteur.
(function(){
  try{
    const params = new URLSearchParams(location.search);
    const ref = params.get('ref');
    if(ref) localStorage.setItem('predikta_ref', ref.trim().toUpperCase());
  }catch(e){}
})();
window.PREDIKTA_REF = (function(){
  try{ return localStorage.getItem('predikta_ref') || ''; }catch(e){ return ''; }
})();

// ── Langue ────────────────────────────────────────────────────────────────
const SUPPORTED = ['fr','en','es','pt','ht'];
const LANG_FLAGS = { fr:'🇫🇷', en:'🇺🇸', es:'🇪🇸', pt:'🇧🇷', ht:'🇭🇹' };

function detectLang(){
  const s = localStorage.getItem('predikta_lang');
  if(s && SUPPORTED.includes(s)) return s;
  const b = (navigator.language||'en').toLowerCase().slice(0,2);
  return {fr:'fr',en:'en',es:'es',pt:'pt'}[b] || 'en';
}
window.PREDIKTA_LANG = detectLang();

function saveLang(l){
  if(!SUPPORTED.includes(l)) return;
  localStorage.setItem('predikta_lang', l);
  window.PREDIKTA_LANG = l;
  document.documentElement.setAttribute('data-lang', l);
  // Update all lang buttons
  document.querySelectorAll('[data-navlang]').forEach(b => {
    b.classList.toggle('active', b.dataset.navlang === l);
  });
  // Refresh nav labels
  document.querySelectorAll('[data-navsvc]').forEach(el => {
    const k = el.dataset.navsvc;
    const lbl = el.querySelector('.nav-svc-label');
    if(lbl) lbl.textContent = (NAV_T[l]||NAV_T.en)[k] || k;
  });
  const tag = document.getElementById('pnav-tagline');
  if(tag) tag.textContent = (NAV_T[l]||NAV_T.en).tagline;
  // Notify page JS (guarded against mutual setLang/saveLang recursion)
  if(typeof window.setLang === 'function' && !window._langSyncGuard){
    window._langSyncGuard = true;
    try{ window.setLang(l); } finally{ window._langSyncGuard = false; }
  }
  // Refresh assistant
  if(window._assistantLangRefresh) window._assistantLangRefresh(l);
  // Server-rendered SEO prediction pages: reload with ?lang= to refresh content
  if(typeof window.setLang !== 'function' && location.pathname.startsWith('/predictions')){
    const url = new URL(location.href);
    if(l === 'fr') url.searchParams.delete('lang');
    else url.searchParams.set('lang', l);
    location.href = url.toString();
  }
}
window.saveLang = saveLang;
function nt(k){ return (NAV_T[window.PREDIKTA_LANG]||NAV_T.en)[k]||k; }

// ── Dark / Light ──────────────────────────────────────────────────────────
let _dark = localStorage.getItem('predikta_theme') !== 'light';
function applyTheme(){
  document.documentElement.setAttribute('data-theme', _dark?'dark':'light');
  document.querySelectorAll('.ptheme-icon').forEach(el => el.textContent = _dark?'☀️':'🌙');
}
function toggleTheme(){
  _dark = !_dark;
  localStorage.setItem('predikta_theme', _dark?'dark':'light');
  applyTheme();
}
window.toggleTheme = toggleTheme;

// ── Favoris ───────────────────────────────────────────────────────────────
function getFavs(){ return JSON.parse(localStorage.getItem('predikta_favs')||'[]'); }
function toggleFav(code){ let f=getFavs(),i=f.indexOf(code); i>=0?f.splice(i,1):f.push(code); localStorage.setItem('predikta_favs',JSON.stringify(f)); return i<0; }
function isFav(code){ return getFavs().includes(code); }
window.PREDIKTA = { toggleFav, isFav, getFavs, affiliate: window.PREDIKTA_AFFILIATE };
function shareContent(text,url){ url=url||location.href; if(navigator.share){navigator.share({title:'PREDIKTA',text,url}).catch(()=>{});}else{window.open(`https://wa.me/?text=${encodeURIComponent(text+'\n'+url)}`,'_blank');} }
window.shareContent = shareContent;

// ── Mobile menu ───────────────────────────────────────────────────────────
function toggleMobileMenu(){
  document.getElementById('pnav-mobile')?.classList.toggle('open');
  document.getElementById('pnav-overlay')?.classList.toggle('open');
  document.body.style.overflow = document.getElementById('pnav-mobile')?.classList.contains('open') ? 'hidden' : '';
}
function closeMobileMenu(){
  document.getElementById('pnav-mobile')?.classList.remove('open');
  document.getElementById('pnav-overlay')?.classList.remove('open');
  document.body.style.overflow = '';
}
window.toggleMobileMenu = toggleMobileMenu;
window.closeMobileMenu  = closeMobileMenu;
document.addEventListener('keydown', e => { if(e.key==='Escape'){ closeMobileMenu(); closeAssistant(); }});

// ═══════════════════════════════════════════════════════════════════
// ASSISTANT MULTILINGUE
// ═══════════════════════════════════════════════════════════════════
const ASSIST_T = {
  fr:{
    title:'Assistant PREDIKTA',
    subtitle:'Je suis là pour vous aider !',
    placeholder:'Posez votre question...',
    greeting:'Bonjour ! 👋 Je suis votre assistant PREDIKTA. Comment puis-je vous aider aujourd\'hui ?',
    quickTitle:'Questions rapides :',
    quick:['Comment voir les résultats ?','Comment analyser un État ?','Qu\'est-ce que Business Intelligence ?','Comment changer la langue ?','Comment s\'abonner PRO ?','Où voir Powerball/Mega ?'],
    notFound:'Je ne comprends pas bien votre question. Essayez : "résultats", "analyser", "langue", "PRO", ou cliquez sur une question rapide ci-dessous.',
    send:'Envoyer',
    close:'Fermer',
  },
  en:{
    title:'PREDIKTA Assistant',
    subtitle:'I\'m here to help!',
    placeholder:'Ask your question...',
    greeting:'Hello! 👋 I\'m your PREDIKTA assistant. How can I help you today?',
    quickTitle:'Quick questions:',
    quick:['How to see results?','How to analyze a state?','What is Business Intelligence?','How to change language?','How to subscribe PRO?','Where to see Powerball/Mega?'],
    notFound:'I didn\'t quite understand. Try: "results", "analyze", "language", "PRO", or click a quick question below.',
    send:'Send',
    close:'Close',
  },
  es:{
    title:'Asistente PREDIKTA',
    subtitle:'¡Estoy aquí para ayudarte!',
    placeholder:'Haz tu pregunta...',
    greeting:'¡Hola! 👋 Soy tu asistente PREDIKTA. ¿Cómo puedo ayudarte hoy?',
    quickTitle:'Preguntas rápidas:',
    quick:['¿Cómo ver resultados?','¿Cómo analizar un estado?','¿Qué es Business Intelligence?','¿Cómo cambiar idioma?','¿Cómo suscribirse PRO?','¿Dónde ver Powerball/Mega?'],
    notFound:'No entendí bien. Prueba: "resultados", "analizar", "idioma", "PRO" o haz clic en una pregunta rápida.',
    send:'Enviar',
    close:'Cerrar',
  },
  pt:{
    title:'Assistente PREDIKTA',
    subtitle:'Estou aqui para ajudar!',
    placeholder:'Faça sua pergunta...',
    greeting:'Olá! 👋 Sou seu assistente PREDIKTA. Como posso ajudá-lo hoje?',
    quickTitle:'Perguntas rápidas:',
    quick:['Como ver resultados?','Como analisar um estado?','O que é Business Intelligence?','Como mudar idioma?','Como assinar PRO?','Onde ver Powerball/Mega?'],
    notFound:'Não entendi bem. Tente: "resultados", "analisar", "idioma", "PRO" ou clique numa pergunta rápida.',
    send:'Enviar',
    close:'Fechar',
  },
  ht:{
    title:'Asistan PREDIKTA',
    subtitle:'Mwen isit la pou ede ou!',
    placeholder:'Poze kesyon ou...',
    greeting:'Bonjou! 👋 Mwen se asistan PREDIKTA ou. Kijan mwen ka ede ou jodi a?',
    quickTitle:'Kesyon rapid:',
    quick:['Kijan pou wè rezilta?','Kijan pou analize yon eta?','Sa Business Intelligence ye?','Kijan pou chanje lang?','Kijan pou abòne PRO?','Kote pou wè Powerball/Mega?'],
    notFound:'Mwen pa konprann. Eseye: "rezilta", "analize", "lang", "PRO" oswa klike sou yon kesyon rapid.',
    send:'Voye',
    close:'Fèmen',
  },
};

// Knowledge base — responses by language
const KB = {
  fr:[
    { kw:['résultat','résultats','tirage','aujourd','dernier','yesterday','aujourd\'hui'],
      answer:'Pour voir les résultats du jour :\n\n🎱 <a href="/results" style="color:#4f6eff">Hub Résultats (Pick3)</a> — tous les 44 États\n🏆 <a href="/all-results" style="color:#4f6eff">Tous les Jeux</a> — Pick2, Pick4, Lotto, Powerball...',
      quick:[{t:'Voir Hub Résultats',href:'/results'},{t:'Voir Tous les Jeux',href:'/all-results'}] },
    { kw:['analyser','analyse','prédiction','prédire','analyse','pick3','cash3','numéro','chiffre'],
      answer:'Pour analyser et obtenir des prédictions :\n\n⚡ <a href="/analyze" style="color:#4f6eff">Analyseur Prédictif Loterie</a>\n→ Sélectionnez votre État (NY, GA, TX, FL...)\n→ Choisissez la période (3 mois à 5 ans)\n→ Cliquez ⚡ Analyser\n\n7 algorithmes génèrent vos prédictions en quelques secondes.',
      quick:[{t:'Ouvrir l\'Analyseur',href:'/analyze'}] },
    { kw:['business','entreprise','projet','startup','pme','marketing','lancer','marché','niche'],
      answer:'PREDIKTA Business Intelligence analyse votre projet en 4 étapes :\n\n🚀 <a href="/bizai" style="color:#4f6eff">Ouvrir Business Intelligence</a>\n→ Étape 1 : Nom, secteur, stade\n→ Étape 2 : Produit, prix, audience\n→ Étape 3 : Géographie, langues\n→ Étape 4 : Budget, objectifs\n\nRapport 12 sections généré en 30 secondes !',
      quick:[{t:'Lancer Business Intelligence',href:'/bizai'}] },
    { kw:['langue','langage','traduire','translation','french','english','español','créole','kreyol','ht','fr','en','es','pt'],
      answer:'Pour changer la langue, utilisez les boutons en haut à droite de chaque page :\n\n🇫🇷 FR · 🇺🇸 EN · 🇪🇸 ES · 🇧🇷 PT · 🇭🇹 HT\n\nLa langue est sauvegardée automatiquement sur toutes les pages.',
      quick:SUPPORTED.map(l=>({t:LANG_FLAGS[l]+' '+l.toUpperCase(),fn:`saveLang('${l}')`})) },
    { kw:['pro','elite','abonnement','payer','prix','tarif','subscribe','forfait','plan'],
      answer:'Nos plans :\n\n👑 PRO — $19.99/mois (4 États, 1 analyse/jour, 3 jours d\'essai)\n💎 VIP — $49.99/mois (20 États, 7 analyses/jour, 7 jours d\'essai)\n⭐ PREMIUM — $99.99/mois (Tous les États, analyses illimitées, 7 jours d\'essai)\n\nUn compte et un abonnement actif sont requis pour lancer des analyses.',
      quick:[{t:'Voir les Plans',href:'/register'}] },
    { kw:['powerball','mega','million','jackpot','lotto','pick4','pick5','pick2','tous jeux','all'],
      answer:'Pour voir Powerball, Mega Millions et TOUS les jeux :\n\n🏆 <a href="/all-results" style="color:#4f6eff">Page Tous les Résultats</a>\n→ Sélectionnez votre État (NY, GA, TX, FL...)\n→ Tous les jeux s\'affichent : Pick2, Pick3, Pick4, Pick5, Lotto, Powerball, Mega Millions',
      quick:[{t:'Voir Tous les Jeux',href:'/all-results'}] },
    { kw:['accueil','home','retour','page principale','début'],
      answer:'Pour revenir à la page d\'accueil :\n\n🏠 Cliquez sur le logo <strong>PREDIKTA</strong> en haut à gauche\n🏠 Ou cliquez sur le bouton <strong>🏠</strong> flottant en bas à gauche\n🏠 Ou allez sur <a href="/" style="color:#4f6eff">predikta.io</a>',
      quick:[{t:'Aller à l\'Accueil',href:'/'}] },
    { kw:['état','state','new york','georgia','texas','florida','ny','ga','tx','fl'],
      answer:'PREDIKTA couvre 44 États US + Puerto Rico :\n\n🗽 New York · 🍑 Georgia · ⭐ Texas · 🌴 Florida · ☀️ California...\n\nDans l\'Analyseur, utilisez le sélecteur d\'État en haut pour choisir votre État.',
      quick:[{t:'Voir les États',href:'/results'}] },
    { kw:['installer','pwa','app','mobile','téléphone','android','iphone'],
      answer:'PREDIKTA est une PWA — installez-la sur votre téléphone !\n\n📱 Android : Menu ⋮ → "Ajouter à l\'écran d\'accueil"\n🍎 iPhone : Bouton Partager → "Sur l\'écran d\'accueil"\n\nFonctionne comme une vraie app, sans App Store !',
      quick:[] },
  ],
  en:[
    { kw:['result','results','draw','today','latest','yesterday'],
      answer:'To see today\'s results:\n\n🎱 <a href="/results" style="color:#4f6eff">Results Hub (Pick3)</a> — all 44 states\n🏆 <a href="/all-results" style="color:#4f6eff">All Games</a> — Pick2, Pick4, Lotto, Powerball...',
      quick:[{t:'Results Hub',href:'/results'},{t:'All Games',href:'/all-results'}] },
    { kw:['analyze','predict','prediction','pick3','cash3','number','digit'],
      answer:'To analyze and get predictions:\n\n⚡ <a href="/analyze" style="color:#4f6eff">Predictive Lottery Analyzer</a>\n→ Select your State (NY, GA, TX, FL...)\n→ Choose period (3 months to 5 years)\n→ Click ⚡ Analyze\n\n7 algorithms generate predictions in seconds.',
      quick:[{t:'Open Analyzer',href:'/analyze'}] },
    { kw:['business','project','startup','marketing','launch','market','niche'],
      answer:'PREDIKTA Business Intelligence analyzes your project in 4 steps:\n\n🚀 <a href="/bizai" style="color:#4f6eff">Open Business Intelligence</a>\n→ 12-section report in 30 seconds\n→ Market analysis · Target audience · 11 marketing channels\n→ 30-60-90 day action plan',
      quick:[{t:'Launch Business Intelligence',href:'/bizai'}] },
    { kw:['language','translate','french','english','spanish','creole','lang'],
      answer:'To change language, use the buttons at the top right of every page:\n\n🇫🇷 FR · 🇺🇸 EN · 🇪🇸 ES · 🇧🇷 PT · 🇭🇹 HT\n\nYour language preference is saved automatically.',
      quick:SUPPORTED.map(l=>({t:LANG_FLAGS[l]+' '+l.toUpperCase(),fn:`saveLang('${l}')`})) },
    { kw:['pro','elite','subscription','price','plan','subscribe','pay'],
      answer:'Our plans:\n\n👑 PRO — $19.99/mo (4 states, 1 analysis/day, 3-day trial)\n💎 VIP — $49.99/mo (20 states, 7 analyses/day, 7-day trial)\n⭐ PREMIUM — $99.99/mo (All states, unlimited analyses, 7-day trial)\n\nAn account with an active subscription is required to run analyses.',
      quick:[{t:'See Plans',href:'/register'}] },
    { kw:['powerball','mega','million','jackpot','lotto','pick4','pick5','all games'],
      answer:'For Powerball, Mega Millions and ALL games:\n\n🏆 <a href="/all-results" style="color:#4f6eff">All Results Page</a>\n→ Select your State\n→ All games shown: Pick2, Pick3, Pick4, Pick5, Lotto, Powerball, Mega Millions',
      quick:[{t:'See All Games',href:'/all-results'}] },
    { kw:['home','back','main page','start'],
      answer:'To go back home:\n\n🏠 Click the <strong>PREDIKTA</strong> logo (top left)\n🏠 Or click the floating <strong>🏠</strong> button (bottom left)\n🏠 Or visit <a href="/" style="color:#4f6eff">predikta.io</a>',
      quick:[{t:'Go Home',href:'/'}] },
  ],
};
// ES/PT/HT share similar structure - simplified
KB.es = KB.en.map(r=>({...r}));
KB.pt = KB.en.map(r=>({...r}));
KB.ht = KB.en.map(r=>({...r}));

function findAnswer(text){
  const lang = window.PREDIKTA_LANG;
  const kb = KB[lang] || KB.en;
  const lower = text.toLowerCase();
  for(const entry of kb){
    if(entry.kw.some(k => lower.includes(k))){
      return entry;
    }
  }
  return null;
}

function buildAssistantHTML(){
  const l = window.PREDIKTA_LANG;
  const T = ASSIST_T[l] || ASSIST_T.en;
  const quick = T.quick.map(q=>`<button class="passt-quick" onclick="passtSend(this.textContent)">${q}</button>`).join('');
  return `
<style>
/* ═══════════════════════════════════
   PREDIKTA ASSISTANT
   ═══════════════════════════════════ */
#passt-bubble{
  position:fixed;bottom:80px;left:22px;z-index:9000;
  width:52px;height:52px;border-radius:50%;
  background:linear-gradient(135deg,#4f6eff,#8855ff);
  display:flex;align-items:center;justify-content:center;
  font-size:1.4rem;cursor:pointer;
  box-shadow:0 4px 20px rgba(79,110,255,.5);
  border:none;transition:transform .25s,box-shadow .25s;
  animation:bubblePulse 3s ease-in-out infinite;
}
#passt-bubble:hover{transform:scale(1.12);box-shadow:0 6px 28px rgba(79,110,255,.7)}
@keyframes bubblePulse{0%,100%{box-shadow:0 4px 20px rgba(79,110,255,.5)}50%{box-shadow:0 4px 30px rgba(136,85,255,.7)}}
#passt-notif{
  position:absolute;top:-4px;right:-4px;width:18px;height:18px;border-radius:50%;
  background:#ff3d2e;color:#fff;font-size:.55rem;font-weight:900;
  display:flex;align-items:center;justify-content:center;
  border:2px solid #04040f;
}
#passt-panel{
  position:fixed;bottom:90px;left:22px;z-index:9001;
  width:min(360px,calc(100vw - 44px));
  background:#07071e;border:1px solid #252560;border-radius:18px;
  overflow:hidden;
  box-shadow:0 12px 50px rgba(0,0,30,.7);
  transform:scale(.8) translateY(20px);transform-origin:bottom left;
  opacity:0;pointer-events:none;
  transition:all .3s cubic-bezier(.34,1.56,.64,1);
}
#passt-panel.open{transform:scale(1) translateY(0);opacity:1;pointer-events:all}

.passt-header{
  padding:14px 16px;
  background:linear-gradient(135deg,rgba(79,110,255,.2),rgba(136,85,255,.15));
  border-bottom:1px solid #1a1a45;
  display:flex;align-items:center;gap:10px;
}
.passt-avatar{
  width:36px;height:36px;border-radius:50%;flex-shrink:0;
  background:linear-gradient(135deg,#4f6eff,#8855ff);
  display:flex;align-items:center;justify-content:center;font-size:1.1rem;
}
.passt-header-text{}
.passt-header-title{font-size:.82rem;font-weight:800;color:#e8eeff;display:block}
.passt-header-sub{font-size:.62rem;color:#22e87a;display:flex;align-items:center;gap:5px}
.passt-header-sub::before{content:'';width:6px;height:6px;border-radius:50%;background:#22e87a;flex-shrink:0}
.passt-close{margin-left:auto;background:none;border:none;color:#7888bb;font-size:1.1rem;cursor:pointer;transition:color .2s}
.passt-close:hover{color:#e8eeff}

.passt-messages{
  height:260px;overflow-y:auto;padding:12px;
  display:flex;flex-direction:column;gap:10px;
  scrollbar-width:thin;scrollbar-color:#1a1a45 transparent;
}
.passt-msg{
  display:flex;gap:8px;align-items:flex-start;max-width:90%;
}
.passt-msg.bot{ align-self:flex-start; }
.passt-msg.user{ align-self:flex-end;flex-direction:row-reverse; }
.passt-msg-avatar{
  width:26px;height:26px;border-radius:50%;flex-shrink:0;
  background:linear-gradient(135deg,#4f6eff,#8855ff);
  display:flex;align-items:center;justify-content:center;font-size:.8rem;
}
.passt-msg-bubble{
  padding:9px 12px;border-radius:12px;font-size:.76rem;line-height:1.6;
}
.passt-msg.bot .passt-msg-bubble{
  background:#0e0e2a;border:1px solid #1a1a45;color:#e8eeff;border-radius:4px 12px 12px 12px;
}
.passt-msg.user .passt-msg-bubble{
  background:linear-gradient(135deg,#4f6eff,#8855ff);color:#fff;border-radius:12px 4px 12px 12px;
}
.passt-msg-bubble a{color:#88aaff}

/* Typing indicator */
.passt-typing{display:flex;gap:4px;padding:8px 12px;background:#0e0e2a;border:1px solid #1a1a45;border-radius:4px 12px 12px 12px;width:fit-content}
.passt-typing span{width:6px;height:6px;border-radius:50%;background:#4f6eff;animation:typingBounce 1.2s infinite}
.passt-typing span:nth-child(2){animation-delay:.2s}
.passt-typing span:nth-child(3){animation-delay:.4s}
@keyframes typingBounce{0%,80%,100%{transform:translateY(0)}40%{transform:translateY(-6px)}}

/* Quick replies inside messages */
.passt-msg-quick{display:flex;flex-wrap:wrap;gap:5px;margin-top:8px}
.passt-msg-qbtn{
  padding:4px 10px;border-radius:8px;font-size:.68rem;font-weight:600;cursor:pointer;
  background:rgba(79,110,255,.15);border:1px solid rgba(79,110,255,.35);color:#88aaff;
  text-decoration:none;transition:all .2s;
}
.passt-msg-qbtn:hover{background:rgba(79,110,255,.3)}

.passt-quick-area{
  padding:8px 12px;border-top:1px solid #1a1a45;
  display:flex;flex-wrap:wrap;gap:5px;max-height:90px;overflow-y:auto;
}
.passt-quick{
  padding:4px 10px;border-radius:8px;font-size:.68rem;font-weight:600;cursor:pointer;
  background:#0e0e2a;border:1px solid #1a1a45;color:#7888bb;transition:all .2s;
}
.passt-quick:hover{border-color:#4f6eff;color:#e8eeff}

.passt-input-area{
  display:flex;gap:8px;padding:10px 12px;border-top:1px solid #1a1a45;background:#060616;
}
#passt-input{
  flex:1;padding:8px 12px;border-radius:20px;border:1px solid #1a1a45;
  background:#0e0e2a;color:#e8eeff;font-size:.78rem;outline:none;
  font-family:'Inter',sans-serif;
}
#passt-input:focus{border-color:#4f6eff}
#passt-input::placeholder{color:#4d5a8a}
#passt-send{
  width:34px;height:34px;border-radius:50%;
  background:linear-gradient(135deg,#4f6eff,#8855ff);
  color:#fff;border:none;cursor:pointer;font-size:.9rem;
  display:flex;align-items:center;justify-content:center;
  transition:transform .2s;flex-shrink:0;
}
#passt-send:hover{transform:scale(1.1)}
</style>

<!-- Bubble -->
<button id="passt-bubble" onclick="toggleAssistant()" title="Assistant PREDIKTA">
  💬
  <span id="passt-notif">1</span>
</button>

<!-- Panel -->
<div id="passt-panel">
  <div class="passt-header">
    <div class="passt-avatar">💬</div>
    <div class="passt-header-text">
      <span class="passt-header-title" id="passt-title">${T.title}</span>
      <span class="passt-header-sub" id="passt-subtitle">${T.subtitle}</span>
    </div>
    <button class="passt-close" onclick="closeAssistant()">✕</button>
  </div>
  <div class="passt-messages" id="passt-messages"></div>
  <div class="passt-quick-area" id="passt-quick">${quick}</div>
  <div class="passt-input-area">
    <input id="passt-input" type="text" placeholder="${T.placeholder}" onkeydown="if(event.key==='Enter')passtSend()"/>
    <button id="passt-send" onclick="passtSend()">➤</button>
  </div>
</div>`;
}

// ── Assistant functions ────────────────────────────────────────────────────
function toggleAssistant(){
  const panel = document.getElementById('passt-panel');
  if(panel.classList.toggle('open')){
    document.getElementById('passt-notif').style.display = 'none';
    if(!panel.dataset.init){
      panel.dataset.init = '1';
      setTimeout(()=>passtBotMsg(ASSIST_T[window.PREDIKTA_LANG]?.greeting || ASSIST_T.en.greeting), 300);
    }
  }
}
function closeAssistant(){ document.getElementById('passt-panel')?.classList.remove('open'); }
window.toggleAssistant = toggleAssistant;
window.closeAssistant  = closeAssistant;

function passtBotMsg(text, quickLinks=[]){
  const msgs = document.getElementById('passt-messages');
  if(!msgs) return;

  // Typing indicator
  const typing = document.createElement('div');
  typing.className = 'passt-msg bot';
  typing.innerHTML = '<div class="passt-msg-avatar">💬</div><div class="passt-typing"><span></span><span></span><span></span></div>';
  msgs.appendChild(typing);
  msgs.scrollTop = msgs.scrollHeight;

  setTimeout(()=>{
    typing.remove();
    const msg = document.createElement('div');
    msg.className = 'passt-msg bot';

    let quickHtml = '';
    if(quickLinks.length){
      quickHtml = '<div class="passt-msg-quick">' + quickLinks.map(q=>
        q.href ? `<a class="passt-msg-qbtn" href="${q.href}">${q.t}</a>`
               : `<button class="passt-msg-qbtn" onclick="${q.fn};closeAssistant()">${q.t}</button>`
      ).join('') + '</div>';
    }

    msg.innerHTML = `<div class="passt-msg-avatar">💬</div>
      <div class="passt-msg-bubble">${text.replace(/\n/g,'<br>')}${quickHtml}</div>`;
    msgs.appendChild(msg);
    msgs.scrollTop = msgs.scrollHeight;
  }, 800);
}

function passtUserMsg(text){
  const msgs = document.getElementById('passt-messages');
  if(!msgs) return;
  const msg = document.createElement('div');
  msg.className = 'passt-msg user';
  msg.innerHTML = `<div class="passt-msg-bubble">${text}</div>`;
  msgs.appendChild(msg);
  msgs.scrollTop = msgs.scrollHeight;
}

function passtSend(text){
  const input = document.getElementById('passt-input');
  const txt = (text || input?.value || '').trim();
  if(!txt) return;
  if(input) input.value = '';

  passtUserMsg(txt);

  const entry = findAnswer(txt);
  const T = ASSIST_T[window.PREDIKTA_LANG] || ASSIST_T.en;

  if(entry){
    passtBotMsg(entry.answer, entry.quick || []);
  } else {
    passtBotMsg(T.notFound, []);
  }
}
window.passtSend = passtSend;

// Refresh assistant on language change
window._assistantLangRefresh = function(l){
  const T = ASSIST_T[l] || ASSIST_T.en;
  const title = document.getElementById('passt-title');
  const sub   = document.getElementById('passt-subtitle');
  const input = document.getElementById('passt-input');
  if(title) title.textContent = T.title;
  if(sub)   sub.textContent   = T.subtitle;
  if(input) input.placeholder = T.placeholder;
  const qa = document.getElementById('passt-quick');
  if(qa) qa.innerHTML = T.quick.map(q=>`<button class="passt-quick" onclick="passtSend(this.textContent)">${q}</button>`).join('');
};

// ═══════════════════════════════════════════════════════════════════
// FLOATING BUTTONS (Home + ↑)
// ═══════════════════════════════════════════════════════════════════
function buildFloatingButtons(){
  return `
<style>
/* Home flottant */
#pfloat-home{
  position:fixed;bottom:22px;left:84px;z-index:8000;
  width:46px;height:46px;border-radius:12px;
  background:linear-gradient(135deg,#0e0e2a,#1a1a40);
  border:1px solid #252560;color:#e8eeff;
  font-size:1.2rem;cursor:pointer;
  display:flex;align-items:center;justify-content:center;
  box-shadow:0 4px 16px rgba(0,0,30,.5);
  transition:all .25s;text-decoration:none;
}
#pfloat-home:hover{background:linear-gradient(135deg,#4f6eff,#8855ff);border-color:#4f6eff;transform:translateY(-3px);box-shadow:0 6px 20px rgba(79,110,255,.4)}
#pfloat-home .pfh-tooltip{
  position:absolute;bottom:110%;left:50%;transform:translateX(-50%);
  background:#1a1a40;border:1px solid #252560;color:#e8eeff;
  padding:4px 10px;border-radius:6px;font-size:.62rem;font-weight:700;
  white-space:nowrap;pointer-events:none;
  opacity:0;transition:opacity .2s;
}
#pfloat-home:hover .pfh-tooltip{opacity:1}

/* Back to top */
#predikta-btt{
  position:fixed;bottom:22px;right:22px;z-index:8000;
  width:46px;height:46px;border-radius:12px;
  background:linear-gradient(135deg,#4f6eff,#8855ff);
  color:#fff;font-size:1.1rem;font-weight:900;border:none;cursor:pointer;
  opacity:0;transform:translateY(16px);transition:all .3s;
  box-shadow:0 4px 16px rgba(79,110,255,.4);
  display:flex;align-items:center;justify-content:center;
}
#predikta-btt.visible{opacity:1;transform:translateY(0)}
#predikta-btt:hover{box-shadow:0 6px 24px rgba(79,110,255,.6);transform:translateY(-3px)}

/* Notifications flottant */
#pfloat-notif{
  position:fixed;bottom:22px;left:138px;z-index:8000;
  width:46px;height:46px;border-radius:12px;
  background:linear-gradient(135deg,#0e0e2a,#1a1a40);
  border:1px solid #252560;color:#e8eeff;
  font-size:1.2rem;cursor:pointer;
  display:flex;align-items:center;justify-content:center;
  box-shadow:0 4px 16px rgba(0,0,30,.5);
  transition:all .25s;
}
#pfloat-notif:hover{background:linear-gradient(135deg,#4f6eff,#8855ff);border-color:#4f6eff;transform:translateY(-3px);box-shadow:0 6px 20px rgba(79,110,255,.4)}
#pfloat-notif.subscribed{background:linear-gradient(135deg,#22e87a,#0e9e55);border-color:#22e87a;color:#04200f}
#pfloat-notif .pfn-tooltip{
  position:absolute;bottom:110%;left:50%;transform:translateX(-50%);
  background:#1a1a40;border:1px solid #252560;color:#e8eeff;
  padding:4px 10px;border-radius:6px;font-size:.62rem;font-weight:700;
  white-space:nowrap;pointer-events:none;
  opacity:0;transition:opacity .2s;
}
#pfloat-notif:hover .pfn-tooltip{opacity:1}
</style>

<a id="pfloat-home" href="/" title="Accueil / Home">
  🏠
  <span class="pfh-tooltip">Accueil</span>
</a>

<button id="pfloat-notif" title="Activer les alertes">
  🔔
  <span class="pfn-tooltip" id="pfn-tooltip">Activer les alertes</span>
</button>

<button id="predikta-btt" onclick="window.scrollTo({top:0,behavior:'smooth'})" title="Retour en haut">↑</button>
`;
}

function initFloating(){
  const btt = document.getElementById('predikta-btt');
  if(!btt) return;
  window.addEventListener('scroll', ()=>{
    btt.classList.toggle('visible', window.scrollY > 80); // visible dès 80px
  }, { passive: true });
}

// ═══════════════════════════════════════════════════════════════════
// PUSH NOTIFICATIONS
// ═══════════════════════════════════════════════════════════════════
function urlBase64ToUint8Array(base64String){
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding).replace(/-/g,'+').replace(/_/g,'/');
  const raw = atob(base64);
  const arr = new Uint8Array(raw.length);
  for(let i=0;i<raw.length;i++) arr[i] = raw.charCodeAt(i);
  return arr;
}

const PUSH_LABELS = {
  fr: { ask:'Activer les alertes', on:'Alertes activées ✓', unsupported:'Notifications non supportées', denied:'Notifications bloquées — vérifie les réglages du navigateur' },
  en: { ask:'Enable alerts', on:'Alerts enabled ✓', unsupported:'Notifications not supported', denied:'Notifications blocked — check browser settings' },
  es: { ask:'Activar alertas', on:'Alertas activadas ✓', unsupported:'Notificaciones no soportadas', denied:'Notificaciones bloqueadas — revisa la configuración' },
  pt: { ask:'Ativar alertas', on:'Alertas ativados ✓', unsupported:'Notificações não suportadas', denied:'Notificações bloqueadas — verifique as configurações' },
  ht: { ask:'Aktive alèt yo', on:'Alèt aktive ✓', unsupported:'Notifikasyon pa sipòte', denied:'Notifikasyon bloke — tcheke paramèt navigatè a' },
};

async function initPushNotif(){
  const btn = document.getElementById('pfloat-notif');
  if(!btn) return;
  const l = (window.PREDIKTA_LANG && PUSH_LABELS[window.PREDIKTA_LANG]) ? window.PREDIKTA_LANG : 'fr';
  const T = PUSH_LABELS[l] || PUSH_LABELS.fr;
  const tooltip = document.getElementById('pfn-tooltip');

  if(!('serviceWorker' in navigator) || !('PushManager' in window) || !('Notification' in window)){
    btn.style.display = 'none';
    return;
  }

  const setState = (subscribed) => {
    btn.classList.toggle('subscribed', subscribed);
    if(tooltip) tooltip.textContent = subscribed ? T.on : T.ask;
  };

  try{
    const reg = await navigator.serviceWorker.ready;
    const existing = await reg.pushManager.getSubscription();
    setState(!!existing && Notification.permission === 'granted');
  }catch(e){}

  btn.addEventListener('click', async () => {
    try{
      if(Notification.permission === 'denied'){
        if(tooltip) tooltip.textContent = T.denied;
        return;
      }
      const reg = await navigator.serviceWorker.ready;
      const existing = await reg.pushManager.getSubscription();

      if(existing && Notification.permission === 'granted'){
        // Already subscribed — unsubscribe
        await fetch('/api/push/unsubscribe', {
          method:'POST', headers:{'Content-Type':'application/json'},
          body: JSON.stringify({ endpoint: existing.endpoint })
        }).catch(()=>{});
        await existing.unsubscribe();
        setState(false);
        return;
      }

      const perm = await Notification.requestPermission();
      if(perm !== 'granted'){
        if(tooltip) tooltip.textContent = T.denied;
        return;
      }

      const keyRes = await fetch('/api/push/vapid-public-key');
      if(!keyRes.ok){ if(tooltip) tooltip.textContent = T.unsupported; return; }
      const { key } = await keyRes.json();

      const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(key),
      });

      await fetch('/api/push/subscribe', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ subscription: sub.toJSON() })
      });

      setState(true);
    }catch(e){
      console.warn('Push subscription failed', e);
    }
  });
}

// ═══════════════════════════════════════════════════════════════════
// NAV HTML
// ═══════════════════════════════════════════════════════════════════
function buildNav(){
  const path = location.pathname;
  const l    = window.PREDIKTA_LANG;

  // Prédictions / Archives / Parrainage retirés du header (manque de place) —
  // déplacés en gros boutons sur la page d'accueil. Restent accessibles via
  // le menu mobile et le footer (SERVICES complet).
  const HEADER_HIDDEN = ['predictions','archives','referral','worldmap','predicktatv','community','trackrecord','trackrecord4','accuracy','pick4','cash5'];
  const svcLinks = SERVICES.filter(s=>!HEADER_HIDDEN.includes(s.key)).map(s=>{
    const active = s.href==='/' ? path==='/' : path.startsWith(s.href) && s.href !== '/';
    const label  = (NAV_T[l]||NAV_T.en)[s.key] || s.key;
    const badge  = s.badge ? `<span style="margin-left:3px;padding:1px 5px;border-radius:4px;font-size:.5rem;font-weight:900;background:${s.badge==='PRO'?'linear-gradient(90deg,#ffd700,#ff9900)':'rgba(34,232,122,.35)'};color:${s.badge==='PRO'?'#000':'#22e87a'}">${s.badge}</span>` : '';
    // account link gets a wrapper so initUserMenu() can replace it with a dropdown
    if(s.key === 'account'){
      return `<span id="pnav-acct-wrap"><a href="${s.href}" class="pnav-svc${active?' active':''}" data-navsvc="${s.key}">
        <span>${s.icon}</span><span class="nav-svc-label">${label}</span>${badge}
      </a></span>`;
    }
    return `<a href="${s.href}" class="pnav-svc${active?' active':''}" data-navsvc="${s.key}">
      <span>${s.icon}</span><span class="nav-svc-label">${label}</span>${badge}
    </a>`;
  }).join('');

  // Language buttons — ALWAYS visible (compact on mobile)
  const langBtns = SUPPORTED.map(ll=>
    `<button class="plang-btn${ll===l?' active':''}" data-navlang="${ll}" onclick="saveLang('${ll}')" title="${LANG_FLAGS[ll]}">
      <span class="plang-flag">${LANG_FLAGS[ll]}</span><span class="plang-code">${ll.toUpperCase()}</span>
    </button>`
  ).join('');

  const mobileSvcs = SERVICES.map(s=>{
    const active = s.href==='/' ? path==='/' : path.startsWith(s.href) && s.href !== '/';
    const label  = (NAV_T[l]||NAV_T.en)[s.key] || s.key;
    return `<a href="${s.href}" class="pmob-svc${active?' active':''}" onclick="closeMobileMenu()">${s.icon} ${label}</a>`;
  }).join('');

  return `
<style>
/* ══════════════════════════════════════
   PREDIKTA GLOBAL POLISH — scroll, reveal, responsive
   ══════════════════════════════════════ */
html{scroll-behavior:smooth}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
.pr-reveal{opacity:0;transform:translateY(18px);transition:opacity .6s ease,transform .6s ease}
.pr-reveal.pr-in{opacity:1;transform:translateY(0)}
@media(prefers-reduced-motion:reduce){
  .pr-reveal,.pr-reveal.pr-in{opacity:1;transform:none;transition:none}
}
.pr-table-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch}
.pr-table-wrap table{min-width:560px}

/* Tap/press micro-interaction for buttons, links-as-buttons and cards */
button,a[class*="btn"],a[class*="-cta"],.state-card,.plan-card,.card{-webkit-tap-highlight-color:transparent}
button:active,a[class*="btn"]:active,a[class*="-cta"]:active{transform:scale(.97)}
.state-card:active,.plan-card:active,.card:active{transform:scale(.985)}
@media(prefers-reduced-motion:reduce){
  button:active,a[class*="btn"]:active,a[class*="-cta"]:active,.state-card:active,.plan-card:active,.card:active{transform:none}
}

/* ══════════════════════════════════════
   PREDIKTA NAV v4.0 — Langue toujours visible
   ══════════════════════════════════════ */
#predikta-nav{
  position:sticky;top:0;z-index:1000;
  background:rgba(4,4,20,.97);
  border-bottom:1px solid #1a1a45;
  backdrop-filter:blur(24px);
  -webkit-backdrop-filter:blur(24px);
  font-family:'Inter',sans-serif;
}
.pnav-top{max-width:1440px;margin:0 auto;display:flex;align-items:center;height:56px;padding:0 16px;gap:8px}

/* Logo HOME */
.pnav-home{
  display:flex;align-items:center;gap:9px;text-decoration:none;flex-shrink:0;
  padding-right:14px;border-right:1px solid #1a1a45;margin-right:8px;height:100%;
}
.pnav-logo-svg{width:32px;height:32px}
.pnav-logo-name{
  font-family:'Orbitron',monospace;font-size:.9rem;font-weight:900;letter-spacing:2px;
  background:linear-gradient(135deg,#4f6eff,#8855ff,#ffd700);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
  display:block;line-height:1;white-space:nowrap;
}
.pnav-logo-tag{font-size:.48rem;color:#4d5a8a;letter-spacing:.5px;display:block;margin-top:2px}

/* Services */
.pnav-services{
  display:flex;align-items:center;gap:1px;flex:1;
  overflow-x:auto;scrollbar-width:none;
}
.pnav-services::-webkit-scrollbar{display:none}
.pnav-svc{
  position:relative;
  display:flex;align-items:center;gap:4px;
  padding:6px 10px;border-radius:7px;
  text-decoration:none;color:#7888bb;font-size:.73rem;font-weight:600;
  border:1px solid transparent;white-space:nowrap;transition:all .18s;flex-shrink:0;
}
.pnav-svc::after{
  content:'';position:absolute;left:10px;right:10px;bottom:-1px;height:2px;border-radius:2px;
  background:linear-gradient(135deg,#4f6eff,#8855ff);
  transform:scaleX(0);transition:transform .18s;
}
.pnav-svc:hover{color:#e8eeff;background:rgba(255,255,255,.05);border-color:#1a1a45}
.pnav-svc:hover::after{transform:scaleX(1)}
.pnav-svc.active{background:#4f6eff;color:#fff;border-color:#4f6eff}
.pnav-svc.active::after{transform:scaleX(1);background:#ffd700}

/* RIGHT CONTROLS */
.pnav-right{display:flex;align-items:center;gap:5px;flex-shrink:0;padding-left:10px;border-left:1px solid #1a1a45;margin-left:4px}

/* LANG — TOUJOURS VISIBLE */
.plang-switcher{display:flex;gap:3px;align-items:center}
.plang-btn{
  display:flex;align-items:center;gap:2px;
  padding:4px 7px;border-radius:6px;font-size:.6rem;font-weight:800;
  cursor:pointer;border:1px solid #1a1a45;background:transparent;color:#4d5a8a;
  transition:all .18s;white-space:nowrap;
}
.plang-btn.active,.plang-btn:hover{background:#4f6eff;border-color:#4f6eff;color:#fff}
.plang-flag{font-size:.85rem}
.plang-code{display:none} /* masqué par défaut, visible sur desktop */

/* Theme */
.ptheme-btn{
  width:30px;height:30px;border-radius:7px;
  border:1px solid #1a1a45;background:transparent;
  cursor:pointer;transition:all .2s;
}
.ptheme-btn:hover{background:#1a1a45}
.ptheme-icon{font-size:.85rem}

/* Hamburger */
.pnav-hamburger{
  display:none;flex-direction:column;gap:4px;cursor:pointer;
  padding:6px 8px;border:1px solid #1a1a45;border-radius:7px;background:transparent;
}
.pnav-hamburger span{display:block;width:16px;height:2px;background:#e8eeff;border-radius:1px}

/* ─── Desktop : afficher code langue ─── */
@media(min-width:901px){
  .plang-code{display:inline}
  .plang-btn{padding:4px 8px;gap:3px}
}
/* ─── Mobile : masquer services, afficher hamburger ─── */
@media(max-width:900px){
  .pnav-services{display:none}
  .pnav-hamburger{display:flex}
  .pnav-home .pnav-logo-tag{display:none}
  .pnav-logo-svg{width:38px;height:38px}
  .pnav-logo-name{font-size:1.15rem;letter-spacing:2.5px}
  /* LANGUE reste visible en mode flags seulement */
}

/* ─── Mobile overlay & menu ─── */
#pnav-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:1001}
#pnav-overlay.open{display:block}
#pnav-mobile{
  position:fixed;top:0;right:0;width:min(310px,92vw);height:100vh;
  background:#07071e;border-left:1px solid #1a1a45;z-index:1002;overflow-y:auto;
  display:flex;flex-direction:column;
  transform:translateX(100%);transition:transform .3s cubic-bezier(.4,0,.2,1);
}
#pnav-mobile.open{transform:translateX(0)}
.pmob-header{display:flex;align-items:center;justify-content:space-between;padding:16px 18px;border-bottom:1px solid #1a1a45;flex-shrink:0}
.pmob-logo{font-family:'Orbitron',monospace;font-size:.9rem;font-weight:900;background:linear-gradient(135deg,#4f6eff,#8855ff,#ffd700);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.pmob-close{width:30px;height:30px;border-radius:50%;background:rgba(255,255,255,.06);border:1px solid #1a1a45;cursor:pointer;color:#e8eeff;font-size:.9rem;display:flex;align-items:center;justify-content:center;transition:background .2s}
.pmob-close:hover{background:rgba(255,61,46,.2)}
.pmob-section{padding:12px 16px;border-bottom:1px solid #1a1a45;flex-shrink:0}
.pmob-section-title{font-size:.58rem;font-weight:800;color:#4d5a8a;text-transform:uppercase;letter-spacing:2px;margin-bottom:10px}
.pmob-svc{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:9px;text-decoration:none;color:#7888bb;font-size:.82rem;font-weight:600;border:1px solid transparent;transition:all .2s;margin-bottom:4px}
.pmob-svc:hover,.pmob-svc.active{color:#e8eeff;background:rgba(79,110,255,.15);border-color:#1a1a45}
.pmob-svc.active{background:#4f6eff;color:#fff}
.pmob-lang{display:flex;gap:5px;flex-wrap:wrap}
.pmob-lang .plang-btn{padding:8px 12px;font-size:.72rem;flex:1;text-align:center;justify-content:center}
.pmob-lang .plang-code{display:inline}
.pmob-footer{padding:14px 16px;display:flex;flex-wrap:wrap;gap:10px;margin-top:auto}
.pmob-footer a{font-size:.68rem;color:#4d5a8a;text-decoration:none;transition:color .2s}
.pmob-footer a:hover{color:#e8eeff}

/* ─── User account dropdown ─── */
.pnav-user{position:relative;display:inline-flex;flex-shrink:0}
.pnav-user-btn{
  display:flex;align-items:center;gap:5px;
  padding:5px 10px;border-radius:7px;
  background:transparent;border:1px solid #1a1a45;
  color:#7888bb;font-size:.73rem;font-weight:600;
  cursor:pointer;white-space:nowrap;transition:all .18s;font-family:'Inter',sans-serif;
}
.pnav-user-btn:hover{color:#e8eeff;background:rgba(255,255,255,.05);border-color:#4f6eff}
.pnav-user-avatar{
  width:22px;height:22px;border-radius:50%;
  background:linear-gradient(135deg,#4f6eff,#8855ff);
  color:#fff;font-size:.65rem;font-weight:800;
  display:flex;align-items:center;justify-content:center;flex-shrink:0;
}
.pnav-user-chevron{font-size:.55rem;transition:transform .2s;color:#4d5a8a}
.pnav-user.open .pnav-user-chevron{transform:rotate(180deg)}
.pnav-user-menu{
  position:absolute;top:calc(100% + 8px);right:0;
  min-width:190px;
  background:#0d0d28;border:1px solid #1a1a45;border-radius:10px;
  box-shadow:0 8px 32px rgba(0,0,0,.6);
  overflow:hidden;z-index:2000;
  opacity:0;transform:translateY(-6px) scale(.97);
  pointer-events:none;transition:opacity .18s,transform .18s;
}
.pnav-user.open .pnav-user-menu{opacity:1;transform:translateY(0) scale(1);pointer-events:auto}
.pnav-user-info{
  padding:10px 14px 8px;border-bottom:1px solid #1a1a45;
  font-size:.7rem;color:#4d5a8a;line-height:1.4;
}
.pnav-user-info strong{display:block;color:#e8eeff;font-size:.78rem;margin-bottom:1px}
.pnav-user-menu a,.pnav-user-menu button{
  display:flex;align-items:center;gap:9px;
  width:100%;padding:10px 14px;
  font-size:.78rem;font-weight:600;color:#c0ccee;
  text-decoration:none;background:transparent;border:none;
  cursor:pointer;font-family:'Inter',sans-serif;
  transition:background .15s,color .15s;text-align:left;
}
.pnav-user-menu a:hover,.pnav-user-menu button:hover{background:rgba(79,110,255,.12);color:#e8eeff}
.pnav-user-menu .pnav-logout{color:#ff6b6b}
.pnav-user-menu .pnav-logout:hover{background:rgba(255,61,46,.12);color:#ff4444}
.pnav-user-menu-sep{height:1px;background:#1a1a45;margin:4px 0}

/* ─── Footer ─── */
.predikta-footer{background:#050514;border-top:1px solid #1a1a45;padding:30px 24px;font-family:'Inter',sans-serif;position:relative;z-index:5}
.pf-inner{max-width:1200px;margin:0 auto}
.pf-top{display:grid;grid-template-columns:repeat(4,1fr);gap:20px;margin-bottom:24px}
.pf-col-title{font-size:.6rem;font-weight:800;color:#4d5a8a;text-transform:uppercase;letter-spacing:2px;margin-bottom:10px}
.pf-link{display:block;font-size:.72rem;color:#7888bb;text-decoration:none;margin-bottom:7px;transition:color .2s}
.pf-link:hover{color:#e8eeff}
.pf-affil-btn{display:inline-block;padding:5px 12px;border-radius:6px;font-size:.68rem;font-weight:700;background:linear-gradient(135deg,#4f6eff,#8855ff);color:#fff;text-decoration:none;margin-bottom:5px;transition:opacity .2s}
.pf-affil-btn:hover{opacity:.85}
.pf-bottom{display:flex;align-items:center;justify-content:space-between;padding-top:18px;border-top:1px solid #1a1a45;flex-wrap:wrap;gap:10px}
.pf-logo{font-family:'Orbitron',monospace;font-size:.82rem;font-weight:900;background:linear-gradient(135deg,#4f6eff,#8855ff,#ffd700);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
#pfooter-copy{font-size:.6rem;color:#2d3055}
.pf-lang-mini{display:flex;gap:3px;flex-wrap:wrap}
@media(max-width:700px){.pf-top{grid-template-columns:1fr 1fr}}
@media(max-width:420px){.pf-top{grid-template-columns:1fr}}
</style>

<nav id="predikta-nav">
  <div class="pnav-top">
    <a class="pnav-home" href="/">
      <svg class="pnav-logo-svg" viewBox="0 0 48 48" fill="none">
        <defs>
          <linearGradient id="nlg" x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stop-color="#4f6eff"/><stop offset="50%" stop-color="#8855ff"/><stop offset="100%" stop-color="#ffd700"/>
          </linearGradient>
          <linearGradient id="nlg2" x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stop-color="#ffd700"/><stop offset="100%" stop-color="#ff9900"/>
          </linearGradient>
        </defs>
        <circle cx="24" cy="24" r="22" stroke="url(#nlg)" stroke-width="1.5" fill="none" opacity=".5"/>
        <circle cx="24" cy="24" r="15" stroke="url(#nlg)" stroke-width="1" fill="none" opacity=".3"/>
        <circle cx="24" cy="24" r="7" fill="url(#nlg)" opacity=".9"/>
        <line x1="24" y1="2" x2="24" y2="9" stroke="url(#nlg)" stroke-width="1.5" stroke-linecap="round"/>
        <line x1="24" y1="39" x2="24" y2="46" stroke="url(#nlg)" stroke-width="1.5" stroke-linecap="round"/>
        <line x1="2" y1="24" x2="9" y2="24" stroke="url(#nlg)" stroke-width="1.5" stroke-linecap="round"/>
        <line x1="39" y1="24" x2="46" y2="24" stroke="url(#nlg)" stroke-width="1.5" stroke-linecap="round"/>
        <path d="M24 19l1.4 2.8h2.8l-2.3 1.8.9 2.9L24 24.9l-2.8 1.6.9-2.9-2.3-1.8h2.8z" fill="url(#nlg2)"/>
      </svg>
      <div>
        <span class="pnav-logo-name">PREDIKTA</span>
        <span class="pnav-logo-tag" id="pnav-tagline">${nt('tagline')}</span>
      </div>
    </a>

    <div class="pnav-services">${svcLinks}</div>

    <div class="pnav-right">
      <!-- LANGUE — TOUJOURS VISIBLE -->
      <div class="plang-switcher">${langBtns}</div>
      <!-- THEME -->
      <button class="ptheme-btn" onclick="toggleTheme()" title="Dark/Light"><span class="ptheme-icon">${_dark?'☀️':'🌙'}</span></button>
      <!-- HAMBURGER -->
      <button class="pnav-hamburger" onclick="toggleMobileMenu()" aria-label="Menu">
        <span></span><span></span><span></span>
      </button>
    </div>
  </div>
</nav>

<div id="pnav-overlay" onclick="closeMobileMenu()"></div>

<div id="pnav-mobile">
  <div class="pmob-header">
    <div class="pmob-logo">PREDIKTA</div>
    <button class="pmob-close" onclick="closeMobileMenu()">✕</button>
  </div>
  <div class="pmob-section">
    <div class="pmob-section-title">🌐 ${nt('lang')}</div>
    <div class="pmob-lang">${SUPPORTED.map(ll=>`<button class="plang-btn${ll===l?' active':''}" data-navlang="${ll}" onclick="saveLang('${ll}');closeMobileMenu()">${LANG_FLAGS[ll]} ${ll.toUpperCase()}</button>`).join('')}</div>
  </div>
  <div id="pmob-user-section" style="display:none;padding:12px 16px;border-bottom:1px solid #1a1a45"></div>
  <div class="pmob-section">
    <div class="pmob-section-title">🚀 Navigation</div>
    ${mobileSvcs}
  </div>
  <div class="pmob-section" style="display:flex;gap:8px">
    <button style="flex:1;padding:10px;border-radius:9px;border:1px solid #1a1a45;background:transparent;color:#7888bb;font-size:.74rem;font-weight:600;cursor:pointer" onclick="toggleTheme();closeMobileMenu()">${_dark?'☀️ Mode Clair':'🌙 Mode Sombre'}</button>
    <button style="flex:1;padding:10px;border-radius:9px;border:1px solid rgba(79,110,255,.3);background:rgba(79,110,255,.1);color:#88aaff;font-size:.74rem;font-weight:600;cursor:pointer" onclick="closeAssistant();window.setTimeout(()=>toggleAssistant(),100);closeMobileMenu()">💬 Assistant</button>
  </div>
  <div class="pmob-footer">
    <a href="/about">À Propos</a><a href="/faq">FAQ</a>
    <a href="/contact">Contact</a><a href="/privacy">Confidentialité</a><a href="/terms">CGU</a>
  </div>
</div>
`;
}

function buildFooter(){
  const l = window.PREDIKTA_LANG;
  const T = NAV_T[l] || NAV_T.en;
  return `
<footer class="predikta-footer">
  <div class="pf-inner">
    <div class="pf-top">
      <div>
        <div class="pf-col-title">🚀 Services</div>
        ${SERVICES.filter(s=>!['worldmap','community','trackrecord','trackrecord4','accuracy','pick4','cash5'].includes(s.key)).map(s=>`<a class="pf-link" href="${s.href}">${s.icon} ${(NAV_T[l]||NAV_T.en)[s.key]}</a>`).join('')}
      </div>
      <div>
        <div class="pf-col-title">📋 Informations</div>
        <a class="pf-link" href="/about">${T.about}</a>
        <a class="pf-link" href="/faq">${T.faq}</a>
        <a class="pf-link" href="/blog">${T.blog}</a>
        <a class="pf-link" href="/track-record">📈 ${T.trackrecord}</a>
        <a class="pf-link" href="/track-record-4">4️⃣ ${T.trackrecord4||'Pick 4 Track Record'}</a>
        <a class="pf-link" href="/accuracy">🏅 ${T.accuracy}</a>
        <a class="pf-link" href="/pick4-predictions">4️⃣ ${T.pick4||'Pick 4 / Cash 4'}</a>
        <a class="pf-link" href="/cash5">💰 ${T.cash5||'Cash 5 / Fantasy 5'}</a>
        <a class="pf-link" href="/world-map">🗺️ ${T.worldmap}</a>
        <a class="pf-link" href="/community">💬 ${T.community}</a>
        <a class="pf-link" href="/contact">${T.contact}</a>
        <a class="pf-link" href="/privacy">${T.privacy}</a>
        <a class="pf-link" href="/terms">${T.terms}</a>
        <a class="pf-link" href="/responsible-gaming">${T.respgaming}</a>
      </div>
      <div>
        <div class="pf-col-title">💼 ${T.affil}</div>
        <a class="pf-affil-btn" href="${window.PREDIKTA_AFFILIATE.thelotter}" target="_blank" rel="noopener">🎰 TheLotter</a><br>
        <a class="pf-affil-btn" href="${window.PREDIKTA_AFFILIATE.lotterypro}" target="_blank" rel="noopener" style="background:linear-gradient(135deg,#22cc88,#4499ff)">📊 LotteryPro</a><br>
        <a class="pf-affil-btn" href="${window.PREDIKTA_AFFILIATE.jackpot}" target="_blank" rel="noopener" style="background:linear-gradient(135deg,#ff9900,#ff6600)">🏆 Jackpot.com</a><br>
        <a class="pf-affil-btn" href="${window.PREDIKTA_AFFILIATE.lottoagent}" target="_blank" rel="noopener" style="background:linear-gradient(135deg,#ffcc00,#ff9900)">🌍 LottoAgent</a><br>
        <a class="pf-affil-btn" href="${window.PREDIKTA_AFFILIATE.lottoland}" target="_blank" rel="noopener" style="background:linear-gradient(135deg,#e63946,#c1121f)">🗺️ LottoLand</a><br>
        <a class="pf-affil-btn" href="${window.PREDIKTA_AFFILIATE.wintrilions}" target="_blank" rel="noopener" style="background:linear-gradient(135deg,#00b4d8,#0077b6)">💎 WinTrillions</a><br>
        <a class="pf-affil-btn" href="${window.PREDIKTA_AFFILIATE.multilotto}" target="_blank" rel="noopener" style="background:linear-gradient(135deg,#2dc653,#1a7431)">🎯 Multilotto</a><br>
        <a class="pf-affil-btn" href="${window.PREDIKTA_AFFILIATE.lotto}" target="_blank" rel="noopener" style="background:linear-gradient(135deg,#7b2d8b,#4f1a6e)">⭐ Lotto.com</a>
      </div>
      <div>
        <div class="pf-col-title">🌐 ${T.lang}</div>
        <div class="pf-lang-mini" style="margin-bottom:14px">
          ${SUPPORTED.map(ll=>`<button class="plang-btn${ll===l?' active':''}" data-navlang="${ll}" onclick="saveLang('${ll}')" style="padding:5px 10px">${LANG_FLAGS[ll]} ${ll.toUpperCase()}</button>`).join('')}
        </div>
        <div class="pf-col-title" style="margin-top:10px">👑 Plans</div>
        <a class="pf-link" href="/register?plan=pro" style="color:#6688ff;font-weight:700">PRO — $19.99/mois</a>
        <a class="pf-link" href="/register?plan=vip" style="color:#ffd700;font-weight:700">VIP — $49.99/mois</a>
        <a class="pf-link" href="/register?plan=elite" style="color:#ff9900;font-weight:700">PREMIUM — $99.99/mois</a>
        <a class="pf-link" href="/api/health" target="_blank" style="color:#22e87a">● API Status</a>
      </div>
    </div>
    <div class="pf-bottom">
      <div class="pf-logo">PREDIKTA</div>
      <div id="pfooter-copy">${(NAV_T[l]||NAV_T.en).footerCopy}</div>
      <div style="font-size:.6rem;color:#2d3055">v4.0 · ${new Date().getFullYear()}</div>
    </div>
  </div>
</footer>`;
}

// ═══════════════════════════════════════════════════════════════════
// POLISH — reveal-on-scroll + responsive tables
// ═══════════════════════════════════════════════════════════════════
function initRevealAnimations(){
  if(window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  if(!('IntersectionObserver' in window)) return;
  const selector = '.page>.hero, .page>.sec, .sec, .card, .plan-card, .state-card, .stat-box, .preview-box, .bottom-cta';
  const els = Array.from(document.querySelectorAll(selector)).filter(el=>{
    if(el.classList.contains('pr-reveal')) return false;
    if(el.closest('#predikta-nav,#pnav-mobile,.predikta-footer,#passt-panel,#passt-bubble')) return false;
    return true;
  });
  if(!els.length) return;
  const io = new IntersectionObserver((entries)=>{
    entries.forEach(entry=>{
      if(entry.isIntersecting){
        entry.target.classList.add('pr-in');
        io.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
  els.forEach((el,i)=>{
    el.classList.add('pr-reveal');
    el.style.transitionDelay = Math.min(i * 40, 240) + 'ms';
    io.observe(el);
  });
  // Safety net: reveal anything already in view immediately, and force-reveal
  // everything after a short delay in case IO never fires (older browsers, headless, etc.)
  requestAnimationFrame(()=>{
    const vh = window.innerHeight || document.documentElement.clientHeight;
    els.forEach(el=>{
      const r = el.getBoundingClientRect();
      if(r.top < vh && r.bottom > 0) el.classList.add('pr-in');
    });
  });
  setTimeout(()=>{ els.forEach(el=>el.classList.add('pr-in')); io.disconnect(); }, 1500);
}

function wrapResponsiveTables(){
  document.querySelectorAll('table').forEach(table=>{
    if(table.closest('.pr-table-wrap')) return;
    const wrap = document.createElement('div');
    wrap.className = 'pr-table-wrap';
    table.parentNode.insertBefore(wrap, table);
    wrap.appendChild(table);
  });
}

// Tables/cards are often rendered after async data fetches — keep polishing
// the page for a few seconds after load to catch them.
function watchDynamicContent(){
  let runs = 0;
  const tick = ()=>{
    wrapResponsiveTables();
    initRevealAnimations();
    runs++;
    if(runs < 6) setTimeout(tick, 600);
  };
  setTimeout(tick, 600);
}

// ═══════════════════════════════════════════════════════════════════
// USER ACCOUNT DROPDOWN
// ═══════════════════════════════════════════════════════════════════
async function initUserMenu(){
  let user = null;
  try{
    const r = await fetch('/api/auth/me');
    const d = await r.json();
    user = d.user || null;
  }catch(e){ return; }
  if(!user) return;  // not logged in — keep plain link

  const l  = window.PREDIKTA_LANG;
  const T  = NAV_T[l] || NAV_T.en;
  const initial = (user.username || user.email || '?')[0].toUpperCase();
  const plan = user.subscription?.plan_label ? ` · ${user.subscription.plan_label}` : '';

  // ── Desktop dropdown ──────────────────────────────────────────────
  const wrap = document.getElementById('pnav-acct-wrap');
  if(wrap){
    wrap.innerHTML = `
<div class="pnav-user" id="pnav-user-dd">
  <button class="pnav-user-btn" onclick="toggleUserMenu(event)" aria-haspopup="true" aria-expanded="false">
    <span class="pnav-user-avatar">${initial}</span>
    <span class="nav-svc-label">${T.myAccount}</span>
    <span class="pnav-user-chevron">▾</span>
  </button>
  <div class="pnav-user-menu" role="menu">
    <div class="pnav-user-info">
      <strong>${user.username || user.email}</strong>
      ${user.email}${plan}
    </div>
    <a href="/account" role="menuitem">👤 ${T.myAccount}</a>
    <a href="/dashboard" role="menuitem">📊 ${T.dashboard}</a>
    <div class="pnav-user-menu-sep"></div>
    <button class="pnav-logout" onclick="doNavLogout()" role="menuitem">🚪 ${T.logout}</button>
  </div>
</div>`;
  }

  // ── Mobile user section ───────────────────────────────────────────
  const mobSec = document.getElementById('pmob-user-section');
  if(mobSec){
    mobSec.style.display = '';
    mobSec.innerHTML = `
<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
  <div style="width:34px;height:34px;border-radius:50%;background:linear-gradient(135deg,#4f6eff,#8855ff);color:#fff;font-size:.85rem;font-weight:800;display:flex;align-items:center;justify-content:center;flex-shrink:0">${initial}</div>
  <div><div style="font-size:.82rem;font-weight:700;color:#e8eeff">${user.username || user.email}</div>
  <div style="font-size:.65rem;color:#4d5a8a">${user.email}${plan}</div></div>
</div>
<a href="/account" onclick="closeMobileMenu()" style="display:flex;align-items:center;gap:10px;padding:9px 10px;border-radius:8px;text-decoration:none;color:#c0ccee;font-size:.8rem;font-weight:600;transition:background .15s;border:1px solid transparent" onmouseover="this.style.background='rgba(79,110,255,.12)'" onmouseout="this.style.background=''">👤 ${T.myAccount}</a>
<a href="/dashboard" onclick="closeMobileMenu()" style="display:flex;align-items:center;gap:10px;padding:9px 10px;border-radius:8px;text-decoration:none;color:#c0ccee;font-size:.8rem;font-weight:600;transition:background .15s;border:1px solid transparent" onmouseover="this.style.background='rgba(79,110,255,.12)'" onmouseout="this.style.background=''">📊 ${T.dashboard}</a>
<button onclick="doNavLogout();closeMobileMenu()" style="display:flex;align-items:center;gap:10px;width:100%;padding:9px 10px;border-radius:8px;background:transparent;border:1px solid rgba(255,61,46,.25);color:#ff6b6b;font-size:.8rem;font-weight:600;cursor:pointer;font-family:'Inter',sans-serif;margin-top:6px">🚪 ${T.logout}</button>`;
  }
}

function toggleUserMenu(e){
  if(e) e.stopPropagation();
  const dd = document.getElementById('pnav-user-dd');
  if(!dd) return;
  const isOpen = dd.classList.toggle('open');
  dd.querySelector('.pnav-user-btn').setAttribute('aria-expanded', isOpen);
}

function doNavLogout(){
  fetch('/api/auth/logout', {method:'POST'})
    .finally(()=>{ location.href = '/'; });
}

// close dropdown on outside click
document.addEventListener('click', function(e){
  const dd = document.getElementById('pnav-user-dd');
  if(dd && dd.classList.contains('open') && !dd.contains(e.target)){
    dd.classList.remove('open');
    const btn = dd.querySelector('.pnav-user-btn');
    if(btn) btn.setAttribute('aria-expanded','false');
  }
});

// ═══════════════════════════════════════════════════════════════════
// INJECT ALL
// ═══════════════════════════════════════════════════════════════════
function inject(){
  document.documentElement.setAttribute('data-lang', window.PREDIKTA_LANG);
  applyTheme();

  // Clean old elements
  ['#predikta-nav','#pnav-overlay','#pnav-mobile','#predikta-btt',
   '#pfloat-home','#pfloat-notif','#passt-bubble','#passt-panel'].forEach(sel=>{
    document.querySelectorAll(sel).forEach(el=>el.remove());
  });

  // 1. Inject NAV
  const navDiv = document.createElement('div');
  navDiv.innerHTML = buildNav();
  document.body.insertBefore(navDiv, document.body.firstChild);

  // 2. Inject FLOATING BUTTONS
  const floatDiv = document.createElement('div');
  floatDiv.innerHTML = buildFloatingButtons();
  document.body.appendChild(floatDiv);
  initFloating();
  initPushNotif();

  // 3. Inject ASSISTANT
  const assistDiv = document.createElement('div');
  assistDiv.innerHTML = buildAssistantHTML();
  document.body.appendChild(assistDiv);

  // 4. Inject FOOTER (replace existing or append)
  const existingFooter = document.querySelector('footer.predikta-footer, footer[data-pfooter]');
  if(existingFooter){
    const newF = document.createElement('div');
    newF.innerHTML = buildFooter();
    existingFooter.replaceWith(newF.firstElementChild);
  } else {
    const fd = document.createElement('div');
    fd.innerHTML = buildFooter();
    document.body.appendChild(fd);
  }

  // 5. POLISH — reveal animations + responsive tables
  wrapResponsiveTables();
  initRevealAnimations();
  watchDynamicContent();

  // 6. USER MENU — async, replaces "Mon Compte" with dropdown if logged in
  initUserMenu();
}

if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded', inject);
} else {
  inject();
}

})();
