/**
 * ZYNORIQ Intelligence™ — Navigation Universelle v5.0
 * Corrigé : Langue toujours visible · Home flottant · ↑ dès 80px · Assistant ZYNORIQ
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
  { href:'/pick5',            icon:'5️⃣', key:'pick5',      badge:'NEW' },
  { href:'/memory',           icon:'🧠', key:'memory',     badge:'NEW' },
  { href:'/founders',         icon:'🏅', key:'founders',   badge:'500' },
  { href:'/ambassadors',      icon:'🤝', key:'ambassadors', badge:'' },
];

// ── Traductions ───────────────────────────────────────────────────────────
const NAV_T = {
  fr:{ home:'Accueil', analyze:'Analyser', results:'Résultats', allresults:'Tous Résultats', predictions:'Prédictions',
       bizai:'Business Intelligence', pro:'PRO', archives:'Archives', referral:'Programme d\'affiliation', account:'Mon Compte', lang:'Langue', theme:'Thème', menu:'Menu',
       tagline:'Intelligence au-delà de la prédiction',
       footerCopy:'© 2026 ZYNORIQ Intelligence™ — Analyses statistiques éducatives, sans garantie de gain. La loterie est un jeu de hasard (18+). Non affilié aux loteries officielles. <a href="/responsible-gaming" style="color:#1479FF">Jeu Responsable</a>.',
       about:'À Propos', faq:'FAQ', contact:'Contact', privacy:'Confidentialité', terms:'CGU', affil:'Affiliés', trackrecord:'Historique des Suggestions', trackrecord4:'Historique Pick 4', respgaming:'Jeu Responsable', accuracy:'Accuracy Score', blog:'Blog',
       worldmap:'Carte du Monde', predicktatv:'ZYNORIQ TV', community:'Communauté', pick4:'Pick 4 / Cash 4', cash5:'Cash 5 / Fantasy 5', pick5:'Pick 5 / Loto 5 Chiffres', memory:'Memory Center', founders:'Fondateurs', ambassadors:'Ambassadeurs',
       dashboard:'Tableau de Bord', logout:'Se déconnecter', login:'Se connecter', myAccount:'Mon Compte' },
  en:{ home:'Home', analyze:'Analyze', results:'Results', allresults:'All Results', predictions:'Predictions',
       bizai:'Business Intelligence', pro:'PRO', archives:'Archives', referral:'Affiliate Program', account:'My Account', lang:'Language', theme:'Theme', menu:'Menu',
       tagline:'Intelligence Beyond Prediction',
       footerCopy:'© 2026 ZYNORIQ Intelligence™ — Educational statistical analysis, no guaranteed winnings. Lottery is gambling (18+). Not affiliated with any official lottery. <a href="/responsible-gaming" style="color:#1479FF">Responsible Gaming</a>.',
       about:'About', faq:'FAQ', contact:'Contact', privacy:'Privacy', terms:'Terms', affil:'Affiliates', trackrecord:'Track Record', trackrecord4:'Pick 4 Track Record', respgaming:'Responsible Gaming', accuracy:'Accuracy Score', blog:'Blog',
       worldmap:'World Map', predicktatv:'ZYNORIQ TV', community:'Community', pick4:'Pick 4 / Cash 4', cash5:'Cash 5 / Fantasy 5', pick5:'Pick 5 / 5-Digit Lotto', memory:'Memory Center', founders:'Founders', ambassadors:'Ambassadors',
       dashboard:'Dashboard', logout:'Sign out', login:'Sign in', myAccount:'My Account' },
  es:{ home:'Inicio', analyze:'Analizar', results:'Resultados', allresults:'Todos', predictions:'Predicciones',
       bizai:'Business Intelligence', pro:'PRO', archives:'Archivos', referral:'Programa de Afiliados', account:'Mi Cuenta', lang:'Idioma', theme:'Tema', menu:'Menú',
       tagline:'Inteligencia Más Allá de la Predicción',
       footerCopy:'© 2026 ZYNORIQ Intelligence™ — Análisis estadístico educativo, sin garantía de premio. La lotería es un juego de azar (18+). No afiliado a loterías oficiales. <a href="/responsible-gaming" style="color:#1479FF">Juego Responsable</a>.',
       about:'Acerca de', faq:'FAQ', contact:'Contacto', privacy:'Privacidad', terms:'Términos', affil:'Afiliados', trackrecord:'Historial de Sugerencias', trackrecord4:'Historial Pick 4', respgaming:'Juego Responsable', accuracy:'Accuracy Score', blog:'Blog',
       worldmap:'Mapa Mundial', predicktatv:'ZYNORIQ TV', community:'Comunidad', pick4:'Pick 4 / Cash 4', cash5:'Cash 5 / Fantasy 5', pick5:'Pick 5 / Lotería 5 Dígitos', memory:'Memory Center', founders:'Fundadores', ambassadors:'Embajadores',
       dashboard:'Panel de Control', logout:'Cerrar sesión', login:'Iniciar sesión', myAccount:'Mi Cuenta' },
  pt:{ home:'Início', analyze:'Analisar', results:'Resultados', allresults:'Todos', predictions:'Previsões',
       bizai:'Business Intelligence', pro:'PRO', archives:'Arquivos', referral:'Programa de Afiliados', account:'Minha Conta', lang:'Idioma', theme:'Tema', menu:'Menu',
       tagline:'Inteligência Além da Previsão',
       footerCopy:'© 2026 ZYNORIQ Intelligence™ — Análise estatística educativa, sem garantia de prêmio. A loteria é um jogo de azar (18+). Não afiliado a loterias oficiais. <a href="/responsible-gaming" style="color:#1479FF">Jogo Responsável</a>.',
       about:'Sobre', faq:'FAQ', contact:'Contato', privacy:'Privacidade', terms:'Termos', affil:'Afiliados', trackrecord:'Histórico de Sugestões', trackrecord4:'Histórico Pick 4', respgaming:'Jogo Responsável', accuracy:'Accuracy Score', blog:'Blog',
       worldmap:'Mapa Mundial', predicktatv:'ZYNORIQ TV', community:'Comunidade', pick4:'Pick 4 / Cash 4', cash5:'Cash 5 / Fantasy 5', pick5:'Pick 5 / Loto 5 Dígitos', memory:'Memory Center', founders:'Fundadores', ambassadors:'Embaixadores',
       dashboard:'Painel', logout:'Sair', login:'Entrar', myAccount:'Minha Conta' },
  ht:{ home:'Akèy', analyze:'Analize', results:'Rezilta', allresults:'Tout Rezilta', predictions:'Prediksyon',
       bizai:'Business Intelligence', pro:'PRO', archives:'Achiv', referral:'Pwogram Afilye', account:'Kont Mwen', lang:'Lang', theme:'Tèm', menu:'Meni',
       tagline:'Entèlijans Anlà Prediksyon',
       footerCopy:'© 2026 ZYNORIQ Intelligence™ — Analiz statistik edikatif, san garanti lo. Lotri se jwèt chans (18+). Pa afilye ak lotri ofisyèl. <a href="/responsible-gaming" style="color:#1479FF">Jwe Responsab</a>.',
       about:'Sou nou', faq:'FAQ', contact:'Kontak', privacy:'Konfidans', terms:'Tèm', affil:'Afilye', trackrecord:'Istorik Sijesyon', trackrecord4:'Istorik Pick 4', respgaming:'Jwe Responsab', accuracy:'Accuracy Score', blog:'Blog',
       worldmap:'Kat Mondyal', predicktatv:'ZYNORIQ TV', community:'Kominote', pick4:'Pick 4 / Cash 4', cash5:'Cash 5 / Fantasy 5', pick5:'Pick 5 / Loto 5 Chif', memory:'Memory Center', founders:'Fondatè', ambassadors:'Anbasadè',
       dashboard:'Tablo de Bò', logout:'Dekonekte', login:'Konekte', myAccount:'Kont Mwen' },
};

// ── Affiliés UTM ──────────────────────────────────────────────────────────
window.PREDIKTA_AFFILIATE = {
  thelotter:   'https://www.thelotter.com/?utm_source=zynoriq&utm_medium=affiliate&utm_campaign=nav',
  lotterypro:  'https://www.lotterypro.com/?utm_source=zynoriq&utm_medium=affiliate&utm_campaign=nav',
  jackpot:     'https://www.jackpot.com/?utm_source=zynoriq&utm_medium=affiliate&utm_campaign=nav',
  lottoagent:  'https://www.lottoagent.com/?utm_source=zynoriq&utm_medium=affiliate&utm_campaign=nav',
  lottoland:   'https://www.lottoland.com/?utm_source=zynoriq&utm_medium=affiliate&utm_campaign=nav',
  wintrilions: 'https://www.wintrillions.com/?utm_source=zynoriq&utm_medium=affiliate&utm_campaign=nav',
  multilotto:  'https://www.multilotto.com/?utm_source=zynoriq&utm_medium=affiliate&utm_campaign=nav',
  lotto:       'https://www.lotto.com/?utm_source=zynoriq&utm_medium=affiliate&utm_campaign=nav',
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
  // Refresh assistant + copilot
  if(window._assistantLangRefresh) window._assistantLangRefresh(l);
  if(window._copilotLangRefresh) window._copilotLangRefresh(l);
  if(_cachedUser) initUserMenu();
  // Rebuild footer in the new language
  const oldFooter = document.querySelector('footer.zynoriq-footer');
  if(oldFooter){
    const tmp = document.createElement('div');
    tmp.innerHTML = buildFooter();
    oldFooter.replaceWith(tmp.firstElementChild);
  }
  // Pages with server-rendered content: reload to refresh translations
  const needsReload = location.pathname === '/' || location.pathname.startsWith('/predictions');
  if(needsReload){
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
window.ZYNORIQ = { toggleFav, isFav, getFavs, affiliate: window.PREDIKTA_AFFILIATE };
function shareContent(text,url){ url=url||location.href; if(navigator.share){navigator.share({title:'ZYNORIQ',text,url}).catch(()=>{});}else{window.open(`https://wa.me/?text=${encodeURIComponent(text+'\n'+url)}`,'_blank');} }
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
    title:'Assistant ZYNORIQ',
    subtitle:'Je suis là pour vous aider !',
    placeholder:'Posez votre question...',
    greeting:'Bonjour ! 👋 Je suis votre Assistant ZYNORIQ. Comment puis-je vous aider aujourd\'hui ?',
    quickTitle:'Questions rapides :',
    quick:['Comment voir les résultats ?','Comment analyser un État ?','Qu\'est-ce que Business Intelligence ?','Comment changer la langue ?','Comment s\'abonner PRO ?','Où voir Powerball/Mega ?'],
    notFound:'Je ne comprends pas bien votre question. Essayez : "résultats", "analyser", "langue", "PRO", ou cliquez sur une question rapide ci-dessous.',
    send:'Envoyer',
    close:'Fermer',
  },
  en:{
    title:'ZYNORIQ Assistant',
    subtitle:'I\'m here to help!',
    placeholder:'Ask your question...',
    greeting:'Hello! 👋 I\'m your ZYNORIQ Assistant. How can I help you today?',
    quickTitle:'Quick questions:',
    quick:['How to see results?','How to analyze a state?','What is Business Intelligence?','How to change language?','How to subscribe PRO?','Where to see Powerball/Mega?'],
    notFound:'I didn\'t quite understand. Try: "results", "analyze", "language", "PRO", or click a quick question below.',
    send:'Send',
    close:'Close',
  },
  es:{
    title:'Asistente ZYNORIQ',
    subtitle:'¡Estoy aquí para ayudarte!',
    placeholder:'Haz tu pregunta...',
    greeting:'¡Hola! 👋 Soy tu Asistente ZYNORIQ. ¿Cómo puedo ayudarte hoy?',
    quickTitle:'Preguntas rápidas:',
    quick:['¿Cómo ver resultados?','¿Cómo analizar un estado?','¿Qué es Business Intelligence?','¿Cómo cambiar idioma?','¿Cómo suscribirse PRO?','¿Dónde ver Powerball/Mega?'],
    notFound:'No entendí bien. Prueba: "resultados", "analizar", "idioma", "PRO" o haz clic en una pregunta rápida.',
    send:'Enviar',
    close:'Cerrar',
  },
  pt:{
    title:'Assistente ZYNORIQ',
    subtitle:'Estou aqui para ajudar!',
    placeholder:'Faça sua pergunta...',
    greeting:'Olá! 👋 Sou seu Assistente ZYNORIQ. Como posso ajudá-lo hoje?',
    quickTitle:'Perguntas rápidas:',
    quick:['Como ver resultados?','Como analisar um estado?','O que é Business Intelligence?','Como mudar idioma?','Como assinar PRO?','Onde ver Powerball/Mega?'],
    notFound:'Não entendi bem. Tente: "resultados", "analisar", "idioma", "PRO" ou clique numa pergunta rápida.',
    send:'Enviar',
    close:'Fechar',
  },
  ht:{
    title:'Asistan ZYNORIQ',
    subtitle:'Mwen isit la pou ede ou!',
    placeholder:'Poze kesyon ou...',
    greeting:'Bonjou! 👋 Mwen se Asistan ZYNORIQ ou. Kijan mwen ka ede ou jodi a?',
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
      answer:'Pour voir les résultats du jour :\n\n🎱 <a href="/results" style="color:#1479FF">Hub Résultats (Pick3)</a> — tous les 44 États\n🏆 <a href="/all-results" style="color:#1479FF">Tous les Jeux</a> — Pick2, Pick4, Lotto, Powerball...',
      quick:[{t:'Voir Hub Résultats',href:'/results'},{t:'Voir Tous les Jeux',href:'/all-results'}] },
    { kw:['analyser','analyse','prédiction','prédire','analyse','pick3','cash3','numéro','chiffre'],
      answer:'Pour analyser et obtenir des prédictions :\n\n⚡ <a href="/analyze" style="color:#1479FF">Analyseur Prédictif Loterie</a>\n→ Sélectionnez votre État (NY, GA, TX, FL...)\n→ Choisissez la période (3 mois à 5 ans)\n→ Cliquez ⚡ Analyser\n\n7 algorithmes génèrent vos prédictions en quelques secondes.',
      quick:[{t:'Ouvrir l\'Analyseur',href:'/analyze'}] },
    { kw:['business','entreprise','projet','startup','pme','marketing','lancer','marché','niche'],
      answer:'ZYNORIQ Business Intelligence analyse votre projet en 4 étapes :\n\n🚀 <a href="/bizai" style="color:#1479FF">Ouvrir Business Intelligence</a>\n→ Étape 1 : Nom, secteur, stade\n→ Étape 2 : Produit, prix, audience\n→ Étape 3 : Géographie, langues\n→ Étape 4 : Budget, objectifs\n\nRapport 12 sections généré en 30 secondes !',
      quick:[{t:'Lancer Business Intelligence',href:'/bizai'}] },
    { kw:['langue','langage','traduire','translation','french','english','español','créole','kreyol','ht','fr','en','es','pt'],
      answer:'Pour changer la langue, utilisez les boutons en haut à droite de chaque page :\n\n🇫🇷 FR · 🇺🇸 EN · 🇪🇸 ES · 🇧🇷 PT · 🇭🇹 HT\n\nLa langue est sauvegardée automatiquement sur toutes les pages.',
      quick:SUPPORTED.map(l=>({t:LANG_FLAGS[l]+' '+l.toUpperCase(),fn:`saveLang('${l}')`})) },
    { kw:['pro','elite','abonnement','payer','prix','tarif','subscribe','forfait','plan'],
      answer:'Nos plans :\n\n👑 PRO — $19/mois (4 États, 1 analyse/jour, 3 jours d\'essai)\n💎 VIP — $49/mois (20 États, 7 analyses/jour, 7 jours d\'essai)\n⭐ PREMIUM — $99/mois (Tous les États, analyses illimitées, 7 jours d\'essai)\n\nUn compte et un abonnement actif sont requis pour lancer des analyses.',
      quick:[{t:'Voir les Plans',href:'/register'}] },
    { kw:['powerball','mega','million','jackpot','lotto','pick4','pick5','pick2','tous jeux','all'],
      answer:'Pour voir Powerball, Mega Millions et TOUS les jeux :\n\n🏆 <a href="/all-results" style="color:#1479FF">Page Tous les Résultats</a>\n→ Sélectionnez votre État (NY, GA, TX, FL...)\n→ Tous les jeux s\'affichent : Pick2, Pick3, Pick4, Pick5, Lotto, Powerball, Mega Millions',
      quick:[{t:'Voir Tous les Jeux',href:'/all-results'}] },
    { kw:['accueil','home','retour','page principale','début'],
      answer:'Pour revenir à la page d\'accueil :\n\n🏠 Cliquez sur le logo <strong>ZYNORIQ</strong> en haut à gauche\n🏠 Ou cliquez sur le bouton <strong>🏠</strong> flottant en bas à gauche\n🏠 Ou allez sur <a href="/" style="color:#1479FF">zynoriq.com</a>',
      quick:[{t:'Aller à l\'Accueil',href:'/'}] },
    { kw:['état','state','new york','georgia','texas','florida','ny','ga','tx','fl'],
      answer:'ZYNORIQ couvre 44 États US + Puerto Rico :\n\n🗽 New York · 🍑 Georgia · ⭐ Texas · 🌴 Florida · ☀️ California...\n\nDans l\'Analyseur, utilisez le sélecteur d\'État en haut pour choisir votre État.',
      quick:[{t:'Voir les États',href:'/results'}] },
    { kw:['installer','pwa','app','mobile','téléphone','android','iphone'],
      answer:'ZYNORIQ est une PWA — installez-la sur votre téléphone !\n\n📱 Android : Menu ⋮ → "Ajouter à l\'écran d\'accueil"\n🍎 iPhone : Bouton Partager → "Sur l\'écran d\'accueil"\n\nFonctionne comme une vraie app, sans App Store !',
      quick:[] },
  ],
  en:[
    { kw:['result','results','draw','today','latest','yesterday'],
      answer:'To see today\'s results:\n\n🎱 <a href="/results" style="color:#1479FF">Results Hub (Pick3)</a> — all 44 states\n🏆 <a href="/all-results" style="color:#1479FF">All Games</a> — Pick2, Pick4, Lotto, Powerball...',
      quick:[{t:'Results Hub',href:'/results'},{t:'All Games',href:'/all-results'}] },
    { kw:['analyze','predict','prediction','pick3','cash3','number','digit'],
      answer:'To analyze and get predictions:\n\n⚡ <a href="/analyze" style="color:#1479FF">Predictive Lottery Analyzer</a>\n→ Select your State (NY, GA, TX, FL...)\n→ Choose period (3 months to 5 years)\n→ Click ⚡ Analyze\n\n7 algorithms generate predictions in seconds.',
      quick:[{t:'Open Analyzer',href:'/analyze'}] },
    { kw:['business','project','startup','marketing','launch','market','niche'],
      answer:'ZYNORIQ Business Intelligence analyzes your project in 4 steps:\n\n🚀 <a href="/bizai" style="color:#1479FF">Open Business Intelligence</a>\n→ 12-section report in 30 seconds\n→ Market analysis · Target audience · 11 marketing channels\n→ 30-60-90 day action plan',
      quick:[{t:'Launch Business Intelligence',href:'/bizai'}] },
    { kw:['language','translate','french','english','spanish','creole','lang'],
      answer:'To change language, use the buttons at the top right of every page:\n\n🇫🇷 FR · 🇺🇸 EN · 🇪🇸 ES · 🇧🇷 PT · 🇭🇹 HT\n\nYour language preference is saved automatically.',
      quick:SUPPORTED.map(l=>({t:LANG_FLAGS[l]+' '+l.toUpperCase(),fn:`saveLang('${l}')`})) },
    { kw:['pro','elite','subscription','price','plan','subscribe','pay'],
      answer:'Our plans:\n\n👑 PRO — $19/mo (4 states, 1 analysis/day, 3-day trial)\n💎 VIP — $49/mo (20 states, 7 analyses/day, 7-day trial)\n⭐ PREMIUM — $99/mo (All states, unlimited analyses, 7-day trial)\n\nAn account with an active subscription is required to run analyses.',
      quick:[{t:'See Plans',href:'/register'}] },
    { kw:['powerball','mega','million','jackpot','lotto','pick4','pick5','all games'],
      answer:'For Powerball, Mega Millions and ALL games:\n\n🏆 <a href="/all-results" style="color:#1479FF">All Results Page</a>\n→ Select your State\n→ All games shown: Pick2, Pick3, Pick4, Pick5, Lotto, Powerball, Mega Millions',
      quick:[{t:'See All Games',href:'/all-results'}] },
    { kw:['home','back','main page','start'],
      answer:'To go back home:\n\n🏠 Click the <strong>ZYNORIQ</strong> logo (top left)\n🏠 Or click the floating <strong>🏠</strong> button (bottom left)\n🏠 Or visit <a href="/" style="color:#1479FF">zynoriq.com</a>',
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
   ZYNORIQ Assistant
   ═══════════════════════════════════ */
#passt-bubble{
  position:fixed;bottom:80px;left:22px;z-index:9000;
  width:52px;height:52px;border-radius:50%;
  background:linear-gradient(135deg,#1479FF,#004DFF);
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
  background:linear-gradient(135deg,#1479FF,#004DFF);
  display:flex;align-items:center;justify-content:center;font-size:1.1rem;
}
.passt-header-text{}
.passt-header-title{font-size:.82rem;font-weight:800;color:#e8eeff;display:block}
.passt-header-sub{font-size:.62rem;color:#22e87a;display:flex;align-items:center;gap:5px}
.passt-header-sub::before{content:'';width:6px;height:6px;border-radius:50%;background:#22e87a;flex-shrink:0}
.passt-close{margin-left:auto;background:none;border:none;color:#1479FF;font-size:1.1rem;cursor:pointer;transition:color .2s}
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
  background:linear-gradient(135deg,#1479FF,#004DFF);
  display:flex;align-items:center;justify-content:center;font-size:.8rem;
}
.passt-msg-bubble{
  padding:9px 12px;border-radius:12px;font-size:.76rem;line-height:1.6;
}
.passt-msg.bot .passt-msg-bubble{
  background:#0e0e2a;border:1px solid #1a1a45;color:#e8eeff;border-radius:4px 12px 12px 12px;
}
.passt-msg.user .passt-msg-bubble{
  background:linear-gradient(135deg,#1479FF,#004DFF);color:#fff;border-radius:12px 4px 12px 12px;
}
.passt-msg-bubble a{color:#88aaff}

/* Typing indicator */
.passt-typing{display:flex;gap:4px;padding:8px 12px;background:#0e0e2a;border:1px solid #1a1a45;border-radius:4px 12px 12px 12px;width:fit-content}
.passt-typing span{width:6px;height:6px;border-radius:50%;background:#1479FF;animation:typingBounce 1.2s infinite}
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
  padding:8px 12px;border-top:1px solid #0D3A7A;
  display:flex;flex-wrap:wrap;gap:5px;max-height:90px;overflow-y:auto;
}
.passt-quick{
  padding:4px 10px;border-radius:8px;font-size:.68rem;font-weight:600;cursor:pointer;
  background:#0e0e2a;border:1px solid #1a1a45;color:#1479FF;transition:all .2s;
}
.passt-quick:hover{border-color:#1479FF;color:#e8eeff}

.passt-input-area{
  display:flex;gap:8px;padding:10px 12px;border-top:1px solid #0D3A7A;background:#060616;
}
#passt-input{
  flex:1;padding:8px 12px;border-radius:20px;border:1px solid #1a1a45;
  background:#0e0e2a;color:#e8eeff;font-size:.78rem;outline:none;
  font-family:'Inter',sans-serif;
}
#passt-input:focus{border-color:#1479FF}
#passt-input::placeholder{color:#4d5a8a}
#passt-send{
  width:34px;height:34px;border-radius:50%;
  background:linear-gradient(135deg,#1479FF,#004DFF);
  color:#fff;border:none;cursor:pointer;font-size:.9rem;
  display:flex;align-items:center;justify-content:center;
  transition:transform .2s;flex-shrink:0;
}
#passt-send:hover{transform:scale(1.1)}
</style>

<!-- Bubble -->
<button id="passt-bubble" onclick="toggleAssistant()" title="Assistant ZYNORIQ">
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
#pfloat-home:hover{background:linear-gradient(135deg,#1479FF,#004DFF);border-color:#1479FF;transform:translateY(-3px);box-shadow:0 6px 20px rgba(79,110,255,.4)}
#pfloat-home .pfh-tooltip{
  position:absolute;bottom:110%;left:50%;transform:translateX(-50%);
  background:#1a1a40;border:1px solid #252560;color:#e8eeff;
  padding:4px 10px;border-radius:6px;font-size:.62rem;font-weight:700;
  white-space:nowrap;pointer-events:none;
  opacity:0;transition:opacity .2s;
}
#pfloat-home:hover .pfh-tooltip{opacity:1}

/* Nav arrows */
.pfloat-nav{
  position:fixed;bottom:22px;z-index:8000;
  width:38px;height:38px;border-radius:10px;
  background:linear-gradient(135deg,#0e0e2a,#1a1a40);
  border:1px solid #252560;color:#e8eeff;
  font-size:.9rem;cursor:pointer;
  display:flex;align-items:center;justify-content:center;
  box-shadow:0 4px 12px rgba(0,0,30,.4);
  transition:all .25s;
}
.pfloat-nav:hover{background:linear-gradient(135deg,#1479FF,#004DFF);border-color:#1479FF;transform:translateY(-2px)}
#pfloat-back{left:22px}
#pfloat-fwd{left:134px}

/* Back to top — positioned above Copilot FAB */
#zynoriq-btt{
  position:fixed;bottom:82px;right:28px;z-index:8000;
  width:42px;height:42px;border-radius:50%;
  background:linear-gradient(135deg,#1479FF,#004DFF);
  color:#fff;font-size:1rem;font-weight:900;border:none;cursor:pointer;
  opacity:0;transform:translateY(16px);transition:all .3s;
  box-shadow:0 4px 16px rgba(79,110,255,.4);
  display:flex;align-items:center;justify-content:center;
}
#zynoriq-btt.visible{opacity:1;transform:translateY(0)}
#zynoriq-btt:hover{box-shadow:0 6px 24px rgba(20,121,255,.6);transform:translateY(-3px)}
@media(max-width:480px){#zynoriq-btt{bottom:140px;right:16px}}

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
#pfloat-notif:hover{background:linear-gradient(135deg,#1479FF,#004DFF);border-color:#1479FF;transform:translateY(-3px);box-shadow:0 6px 20px rgba(79,110,255,.4)}
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

<button id="pfloat-back" class="pfloat-nav" onclick="history.back()" title="Retour / Back">←</button>
<a id="pfloat-home" href="/" title="Accueil / Home">
  🏠
  <span class="pfh-tooltip">Accueil</span>
</a>
<button id="pfloat-fwd" class="pfloat-nav" onclick="history.forward()" title="Suivant / Forward">→</button>

<button id="pfloat-notif" title="Activer les alertes">
  🔔
  <span class="pfn-tooltip" id="pfn-tooltip">Activer les alertes</span>
</button>

<button id="zynoriq-btt" onclick="window.scrollTo({top:0,behavior:'smooth'})" title="Retour en haut">↑</button>
`;
}

function initFloating(){
  const btt = document.getElementById('zynoriq-btt');
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
  const HEADER_HIDDEN = ['results','predictions','archives','referral','worldmap','predicktatv','community','trackrecord','trackrecord4','accuracy','pick4','cash5','pick5','memory','account'];
  const svcLinks = SERVICES.filter(s=>!HEADER_HIDDEN.includes(s.key)).map(s=>{
    const active = s.href==='/' ? path==='/' : path.startsWith(s.href) && s.href !== '/';
    const label  = (NAV_T[l]||NAV_T.en)[s.key] || s.key;
    const badge  = s.badge ? `<span style="margin-left:3px;padding:1px 5px;border-radius:4px;font-size:.5rem;font-weight:900;background:${s.badge==='PRO'?'linear-gradient(90deg,#ffd700,#ff9900)':'rgba(34,232,122,.35)'};color:${s.badge==='PRO'?'#000':'#22e87a'}">${s.badge}</span>` : '';
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
  const langSelect = `<select class="plang-select" onchange="saveLang(this.value)">
    ${SUPPORTED.map(ll=>`<option value="${ll}"${ll===l?' selected':''}>${LANG_FLAGS[ll]} ${ll.toUpperCase()}</option>`).join('')}
  </select>`;

  const mobileSvcs = SERVICES.map(s=>{
    const active = s.href==='/' ? path==='/' : path.startsWith(s.href) && s.href !== '/';
    const label  = (NAV_T[l]||NAV_T.en)[s.key] || s.key;
    return `<a href="${s.href}" class="pmob-svc${active?' active':''}" onclick="closeMobileMenu()">${s.icon} ${label}</a>`;
  }).join('');

  return `
<style>
/* ══════════════════════════════════════
   ZYNORIQ GLOBAL POLISH — scroll, reveal, responsive
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
   ZYNORIQ Intelligence™ NAV v5.0
   ══════════════════════════════════════ */
#predikta-nav{
  position:sticky;top:0;z-index:1000;
  background:rgba(6,26,53,.97);
  border-bottom:1px solid #0D3A7A;
  backdrop-filter:blur(24px);
  -webkit-backdrop-filter:blur(24px);
  font-family:'Poppins','Inter',sans-serif;
}
.pnav-top{max-width:1440px;margin:0 auto;display:flex;align-items:center;height:56px;padding:0 16px;gap:8px}

/* Logo HOME */
.pnav-home{
  display:flex;align-items:center;gap:9px;text-decoration:none;flex-shrink:0;
  padding-right:14px;border-right:1px solid #0D3A7A;margin-right:8px;height:100%;
}
.pnav-logo-svg{width:32px;height:32px}
.pnav-logo-name{
  font-family:'Poppins',sans-serif;font-size:.9rem;font-weight:800;letter-spacing:2.5px;
  background:linear-gradient(135deg,#1479FF,#004DFF);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
  display:block;line-height:1;white-space:nowrap;
}
.pnav-logo-tag{font-size:.44rem;color:#1460A8;letter-spacing:.8px;display:block;margin-top:2px;text-transform:uppercase}

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
  text-decoration:none;color:#1479FF;font-size:.73rem;font-weight:600;
  border:1px solid transparent;white-space:nowrap;transition:all .18s;flex-shrink:0;
}
.pnav-svc::after{
  content:'';position:absolute;left:10px;right:10px;bottom:-1px;height:2px;border-radius:2px;
  background:linear-gradient(135deg,#1479FF,#004DFF);
  transform:scaleX(0);transition:transform .18s;
}
.pnav-svc:hover{color:#e8eeff;background:rgba(255,255,255,.05);border-color:#1a1a45}
.pnav-svc:hover::after{transform:scaleX(1)}
.pnav-svc.active{background:#1479FF;color:#fff;border-color:#1479FF}
.pnav-svc.active::after{transform:scaleX(1);background:#ffd700}

/* RIGHT CONTROLS */
.pnav-right{display:flex;align-items:center;gap:5px;flex-shrink:0;padding-left:10px;border-left:1px solid #1a1a45;margin-left:4px}

/* LANG */
.plang-switcher{display:flex;gap:3px;align-items:center}
.plang-mobile{display:none}
.plang-select{
  background:#0a0e2a;color:#e8eeff;border:1px solid #1a1a45;border-radius:8px;
  padding:5px 8px;font-size:.75rem;font-weight:700;cursor:pointer;
  appearance:auto;-webkit-appearance:auto;
}
.plang-btn{
  display:flex;align-items:center;gap:2px;
  padding:4px 7px;border-radius:6px;font-size:.6rem;font-weight:800;
  cursor:pointer;border:1px solid #1a1a45;background:transparent;color:#4d5a8a;
  transition:all .18s;white-space:nowrap;
}
.plang-btn.active,.plang-btn:hover{background:#1479FF;border-color:#1479FF;color:#fff}
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
  .plang-desktop{display:none}
  .plang-mobile{display:flex;align-items:center}
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
.pmob-logo{font-family:'Poppins',sans-serif;font-size:.9rem;font-weight:800;letter-spacing:2px;background:linear-gradient(135deg,#1479FF,#004DFF);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.pmob-close{width:30px;height:30px;border-radius:50%;background:rgba(255,255,255,.06);border:1px solid #1a1a45;cursor:pointer;color:#e8eeff;font-size:.9rem;display:flex;align-items:center;justify-content:center;transition:background .2s}
.pmob-close:hover{background:rgba(255,61,46,.2)}
.pmob-section{padding:12px 16px;border-bottom:1px solid #1a1a45;flex-shrink:0}
.pmob-section-title{font-size:.58rem;font-weight:800;color:#4d5a8a;text-transform:uppercase;letter-spacing:2px;margin-bottom:10px}
.pmob-svc{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:9px;text-decoration:none;color:#1479FF;font-size:.82rem;font-weight:600;border:1px solid transparent;transition:all .2s;margin-bottom:4px}
.pmob-svc:hover,.pmob-svc.active{color:#e8eeff;background:rgba(79,110,255,.15);border-color:#1a1a45}
.pmob-svc.active{background:#1479FF;color:#fff}
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
  color:#1479FF;font-size:.73rem;font-weight:600;
  cursor:pointer;white-space:nowrap;transition:all .18s;font-family:'Inter',sans-serif;
}
.pnav-user-btn:hover{color:#e8eeff;background:rgba(255,255,255,.05);border-color:#1479FF}
.pnav-user-avatar{
  width:22px;height:22px;border-radius:50%;
  background:linear-gradient(135deg,#1479FF,#004DFF);
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
.zynoriq-footer{background:#04112A;border-top:1px solid #0D3A7A;padding:30px 24px;font-family:'Poppins','Inter',sans-serif;position:relative;z-index:5}
.pf-inner{max-width:1200px;margin:0 auto}
.pf-top{display:grid;grid-template-columns:repeat(4,1fr);gap:20px;margin-bottom:24px}
.pf-col-title{font-size:.6rem;font-weight:800;color:#4d5a8a;text-transform:uppercase;letter-spacing:2px;margin-bottom:10px}
.pf-link{display:block;font-size:.72rem;color:#1479FF;text-decoration:none;margin-bottom:7px;transition:color .2s}
.pf-link:hover{color:#e8eeff}
.pf-affil-btn{display:inline-block;padding:5px 12px;border-radius:6px;font-size:.68rem;font-weight:700;background:linear-gradient(135deg,#1479FF,#004DFF);color:#fff;text-decoration:none;margin-bottom:5px;transition:opacity .2s}
.pf-affil-btn:hover{opacity:.85}
.pf-bottom{display:flex;align-items:center;justify-content:space-between;padding-top:18px;border-top:1px solid #0D3A7A;flex-wrap:wrap;gap:10px}
.pf-logo{font-family:'Poppins',sans-serif;font-size:.82rem;font-weight:800;letter-spacing:2px;background:linear-gradient(135deg,#1479FF,#004DFF);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
#pfooter-copy{font-size:.6rem;color:#2d3055}
.pf-lang-mini{display:flex;gap:3px;flex-wrap:wrap}
@media(max-width:700px){.pf-top{grid-template-columns:1fr 1fr}}
@media(max-width:420px){.pf-top{grid-template-columns:1fr}}
</style>

<nav id="predikta-nav">
  <div class="pnav-top">
    <a class="pnav-home" href="/">
      <svg class="pnav-logo-svg" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="zg1" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stop-color="#1479FF"/>
            <stop offset="100%" stop-color="#004DFF"/>
          </linearGradient>
          <linearGradient id="zg2" x1="40" y1="0" x2="0" y2="40" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stop-color="#4DA6FF" stop-opacity=".7"/>
            <stop offset="100%" stop-color="#0038CC" stop-opacity=".7"/>
          </linearGradient>
        </defs>
        <!-- Z ribbon symbol -->
        <path d="M6 7 L34 7 Q36 7 36 9 L36 13 Q36 15 34 15 L14 15 L34 25 Q36 26 36 28 L36 31 Q36 33 34 33 L6 33 Q4 33 4 31 L4 27 Q4 25 6 25 L26 25 L6 15 Q4 14 4 12 L4 9 Q4 7 6 7 Z" fill="url(#zg1)"/>
        <path d="M14 15 L26 25" stroke="url(#zg2)" stroke-width="1.5" stroke-linecap="round"/>
      </svg>
      <div>
        <span class="pnav-logo-name">ZYNORIQ</span>
        <span class="pnav-logo-tag" id="pnav-tagline">${nt('tagline')}</span>
      </div>
    </a>

    <div class="pnav-services">${svcLinks}</div>

    <div class="pnav-right">
      <!-- MON COMPTE DROPDOWN — outside pnav-services to avoid overflow clip -->
      <span id="pnav-acct-wrap">
        <a href="/login" class="pnav-svc" data-navsvc="account">🔑 ${(NAV_T[l]||NAV_T.en).login||'Sign in'}</a>
      </span>
      <!-- LANGUE — TOUJOURS VISIBLE -->
      <div class="plang-switcher plang-desktop">${langBtns}</div>
      <div class="plang-mobile">${langSelect}</div>
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
    <div class="pmob-logo">ZYNORIQ</div>
    <button class="pmob-close" onclick="closeMobileMenu()">✕</button>
  </div>
  <div class="pmob-section">
    <div class="pmob-section-title">🌐 ${nt('lang')}</div>
    <div class="pmob-lang"><select class="plang-select" style="width:100%;padding:10px 12px;font-size:.82rem" onchange="saveLang(this.value);closeMobileMenu()">
      ${SUPPORTED.map(ll=>`<option value="${ll}"${ll===l?' selected':''}>${LANG_FLAGS[ll]} ${ll.toUpperCase()}</option>`).join('')}
    </select></div>
  </div>
  <div id="pmob-user-section" style="display:none;padding:12px 16px;border-bottom:1px solid #1a1a45"></div>
  <div class="pmob-section">
    <div class="pmob-section-title">🚀 Navigation</div>
    ${mobileSvcs}
  </div>
  <div class="pmob-section" style="display:flex;gap:8px">
    <button style="flex:1;padding:10px;border-radius:9px;border:1px solid #1a1a45;background:transparent;color:#1479FF;font-size:.74rem;font-weight:600;cursor:pointer" onclick="toggleTheme();closeMobileMenu()">${_dark?'☀️ Mode Clair':'🌙 Mode Sombre'}</button>
    <button style="flex:1;padding:10px;border-radius:9px;border:1px solid rgba(79,110,255,.3);background:rgba(79,110,255,.1);color:#88aaff;font-size:.74rem;font-weight:600;cursor:pointer" onclick="closeAssistant();window.setTimeout(()=>toggleAssistant(),100);closeMobileMenu()">💬 Assistant</button>
  </div>
  <div class="pmob-footer">
    <a href="/about">${T.about||'About'}</a><a href="/faq">FAQ</a>
    <a href="/contact">${T.contact||'Contact'}</a><a href="/privacy">${T.privacy||'Privacy'}</a><a href="/terms">${T.terms||'Terms'}</a>
  </div>
</div>
`;
}

function buildFooter(){
  const l = window.PREDIKTA_LANG;
  const T = NAV_T[l] || NAV_T.en;
  return `
<footer class="zynoriq-footer">
  <div class="pf-inner">
    <div class="pf-top">
      <div>
        <div class="pf-col-title">${{fr:'Services',en:'Services',es:'Servicios',pt:'Serviços',ht:'Sèvis'}[l]||'Services'}</div>
        ${SERVICES.filter(s=>!['worldmap','community','trackrecord','trackrecord4','accuracy','pick4','cash5','pick5'].includes(s.key)).map(s=>`<a class="pf-link" href="${s.href}">${s.icon} ${(NAV_T[l]||NAV_T.en)[s.key]}</a>`).join('')}
      </div>
      <div>
        <div class="pf-col-title">${{fr:'Informations',en:'Information',es:'Información',pt:'Informações',ht:'Enfòmasyon'}[l]||'Information'}</div>
        <a class="pf-link" href="/about">${T.about}</a>
        <a class="pf-link" href="/faq">${T.faq}</a>
        <a class="pf-link" href="/blog">${T.blog}</a>
        <a class="pf-link" href="/track-record">📈 ${T.trackrecord}</a>
        <a class="pf-link" href="/track-record-4">4️⃣ ${T.trackrecord4||'Pick 4 Track Record'}</a>
        <a class="pf-link" href="/accuracy">🏅 ${T.accuracy}</a>
        <a class="pf-link" href="/pick4-predictions">4️⃣ ${T.pick4||'Pick 4 / Cash 4'}</a>
        <a class="pf-link" href="/cash5">💰 ${T.cash5||'Cash 5 / Fantasy 5'}</a>
        <a class="pf-link" href="/pick5">5️⃣ ${T.pick5||'Pick 5 / Loto 5 Chiffres'}</a>
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
        <div class="pf-col-title" style="margin-top:10px">👑 ${{fr:'Plans',en:'Plans',es:'Planes',pt:'Planos',ht:'Plan'}[l]||'Plans'}</div>
        <a class="pf-link" href="/register?plan=pro" style="color:#6688ff;font-weight:700">PRO — $19/${{fr:'mois',en:'mo',es:'mes',pt:'mês',ht:'mwa'}[l]||'mo'}</a>
        <a class="pf-link" href="/register?plan=vip" style="color:#ffd700;font-weight:700">VIP — $49/${{fr:'mois',en:'mo',es:'mes',pt:'mês',ht:'mwa'}[l]||'mo'}</a>
        <a class="pf-link" href="/register?plan=elite" style="color:#ff9900;font-weight:700">PREMIUM — $99/${{fr:'mois',en:'mo',es:'mes',pt:'mês',ht:'mwa'}[l]||'mo'}</a>
        <span class="pf-link" style="color:#22e87a;cursor:default">● Online</span>
        <div style="display:flex;gap:12px;margin-top:14px;align-items:center">
          <a href="https://www.facebook.com/Zynoriq" target="_blank" title="Facebook" style="opacity:.6;transition:opacity .2s" onmouseover="this.style.opacity='1'" onmouseout="this.style.opacity='.6'"><img src="https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/facebook.svg" alt="Facebook" style="width:18px;height:18px;filter:invert(1)"></a>
          <a href="https://x.com/Zynoriq" target="_blank" title="X / Twitter" style="opacity:.6;transition:opacity .2s" onmouseover="this.style.opacity='1'" onmouseout="this.style.opacity='.6'"><img src="https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/x.svg" alt="X" style="width:18px;height:18px;filter:invert(1)"></a>
          <a href="https://www.instagram.com/zynoriqofficial/" target="_blank" title="Instagram" style="opacity:.6;transition:opacity .2s" onmouseover="this.style.opacity='1'" onmouseout="this.style.opacity='.6'"><img src="https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/instagram.svg" alt="Instagram" style="width:18px;height:18px;filter:invert(1)"></a>
          <a href="https://www.tiktok.com/@zynoriq" target="_blank" title="TikTok" style="opacity:.6;transition:opacity .2s" onmouseover="this.style.opacity='1'" onmouseout="this.style.opacity='.6'"><img src="https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/tiktok.svg" alt="TikTok" style="width:18px;height:18px;filter:invert(1)"></a>
          <a href="https://www.linkedin.com/company/zynoriq/" target="_blank" title="LinkedIn" style="opacity:.6;transition:opacity .2s" onmouseover="this.style.opacity='1'" onmouseout="this.style.opacity='.6'"><img src="https://cdn.jsdelivr.net/npm/simple-icons@v9/icons/linkedin.svg" alt="LinkedIn" style="width:18px;height:18px;filter:invert(1)"></a>
        </div>
      </div>
    </div>
    <div class="pf-bottom">
      <div class="pf-logo">ZYNORIQ</div>
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
    if(el.closest('#predikta-nav,#pnav-mobile,.zynoriq-footer,#passt-panel,#passt-bubble')) return false;
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
let _cachedUser = null;
async function initUserMenu(){
  let user = _cachedUser;
  if(!user) try{
    const r = await fetch('/api/auth/me');
    const d = await r.json();
    user = d.user || null;
    _cachedUser = user;
  }catch(e){ return; }
  if(!user){
    const l = window.PREDIKTA_LANG;
    const T = NAV_T[l] || NAV_T.en;
    const wrap = document.getElementById('pnav-acct-wrap');
    if(wrap) wrap.innerHTML = `<a href="/login" class="pnav-svc" data-navsvc="account">🔑 ${T.login}</a>`;
    const mobSec = document.getElementById('pmob-user-section');
    if(mobSec){ mobSec.style.display=''; mobSec.innerHTML = `<a href="/login" onclick="closeMobileMenu()" style="display:flex;align-items:center;gap:10px;padding:9px 10px;border-radius:8px;text-decoration:none;color:#44ff99;font-size:.8rem;font-weight:600;border:1px solid rgba(34,232,122,.3)">🔑 ${T.login}</a>`; }
    return;
  }

  const l  = window.PREDIKTA_LANG;
  const T  = NAV_T[l] || NAV_T.en;
  const initial = (user.username || user.email || '?')[0].toUpperCase();
  const plan = user.subscription?.plan_label ? ` · ${user.subscription.plan_label}` : '';

  // ── Desktop dropdown ──────────────────────────────────────────────
  const wrap = document.getElementById('pnav-acct-wrap');
  if(wrap){
    wrap.innerHTML = `
<div class="pnav-user" id="pnav-user-dd">
  <button class="pnav-user-btn" id="pnav-acct-btn" aria-haspopup="true" aria-expanded="false">
    <span class="pnav-user-avatar">${initial}</span>
    <span class="nav-svc-label">${T.myAccount} ▾</span>
  </button>
  <div class="pnav-user-menu" role="menu">
    <div class="pnav-user-info">
      <strong>${user.username || user.email}</strong>
      ${user.email}${plan}
    </div>
    <a href="/account" role="menuitem">👤 ${T.myAccount}</a>
    <a href="/dashboard" role="menuitem">📊 ${T.dashboard}</a>
    <a href="/analyze" role="menuitem">⚡ ${T.analyze || 'Analyze'}</a>
    <a href="/memory" role="menuitem">🧠 Memory Center</a>
    <a href="/studio" role="menuitem">🎨 Studio</a>
    <a href="/pro" role="menuitem">👑 PRO</a>
    <div class="pnav-user-menu-sep"></div>
    <button class="pnav-logout" id="pnav-logout-btn" role="menuitem">🚪 ${T.logout}</button>
  </div>
</div>`;
    // Events handled by document-level delegation (step 6 in inject())
  }

  // ── Mobile user section ───────────────────────────────────────────
  const mobSec = document.getElementById('pmob-user-section');
  if(mobSec){
    mobSec.style.display = '';
    mobSec.innerHTML = `
<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
  <div style="width:34px;height:34px;border-radius:50%;background:linear-gradient(135deg,#1479FF,#004DFF);color:#fff;font-size:.85rem;font-weight:800;display:flex;align-items:center;justify-content:center;flex-shrink:0">${initial}</div>
  <div><div style="font-size:.82rem;font-weight:700;color:#e8eeff">${user.username || user.email}</div>
  <div style="font-size:.65rem;color:#4d5a8a">${user.email}${plan}</div></div>
</div>
<a href="/account" onclick="closeMobileMenu()" style="display:flex;align-items:center;gap:10px;padding:9px 10px;border-radius:8px;text-decoration:none;color:#c0ccee;font-size:.8rem;font-weight:600;transition:background .15s;border:1px solid transparent" onmouseover="this.style.background='rgba(79,110,255,.12)'" onmouseout="this.style.background=''">👤 ${T.myAccount}</a>
<a href="/dashboard" onclick="closeMobileMenu()" style="display:flex;align-items:center;gap:10px;padding:9px 10px;border-radius:8px;text-decoration:none;color:#c0ccee;font-size:.8rem;font-weight:600;transition:background .15s;border:1px solid transparent" onmouseover="this.style.background='rgba(79,110,255,.12)'" onmouseout="this.style.background=''">📊 ${T.dashboard}</a>
<button onclick="doNavLogout();closeMobileMenu()" style="display:flex;align-items:center;gap:10px;width:100%;padding:9px 10px;border-radius:8px;background:transparent;border:1px solid rgba(255,61,46,.25);color:#ff6b6b;font-size:.8rem;font-weight:600;cursor:pointer;font-family:'Inter',sans-serif;margin-top:6px">🚪 ${T.logout}</button>`;
  }
}

window.toggleUserMenu = function(e){
  if(e) e.stopPropagation();
  const dd = document.getElementById('pnav-user-dd');
  if(!dd) return;
  const isOpen = dd.classList.toggle('open');
  const btn = dd.querySelector('.pnav-user-btn');
  if(btn) btn.setAttribute('aria-expanded', isOpen);
};

window.doNavLogout = function(){
  fetch('/api/auth/logout', {method:'POST'})
    .finally(()=>{ location.href = '/'; });
};

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
  ['#predikta-nav','#pnav-overlay','#pnav-mobile','#zynoriq-btt',
   '#pfloat-back','#pfloat-home','#pfloat-fwd','#pfloat-notif','#passt-bubble','#passt-panel'].forEach(sel=>{
    document.querySelectorAll(sel).forEach(el=>el.remove());
  });

  // 0. Inject ZYNORIQ global CSS (Poppins + brand colors)
  if(!document.getElementById('zynoriq-css')){
    const zLink = document.createElement('link');
    zLink.id = 'zynoriq-css';
    zLink.rel = 'stylesheet';
    zLink.href = '/static/zynoriq.css';
    document.head.appendChild(zLink);
  }

  // 0a. Google Search Console verification
  if(!document.querySelector('meta[name="google-site-verification"]')){
    const gsv=document.createElement('meta');gsv.name='google-site-verification';gsv.content='ziW-RCFWn1BEGNfpPnCciTo4sSgx4ghP8ZnRkutkVEE';document.head.appendChild(gsv);
  }

  // 0b. Inject favicon
  if(!document.querySelector('link[rel="icon"]')){
    const fav = document.createElement('link');
    fav.rel = 'icon';
    fav.type = 'image/svg+xml';
    fav.href = '/favicon.svg';
    document.head.appendChild(fav);
  }

  // 0b. Inject Schema.org (Organization + SoftwareApplication)
  if(!document.getElementById('zynoriq-schema')){
    const sch = document.createElement('script');
    sch.id = 'zynoriq-schema';
    sch.type = 'application/ld+json';
    sch.textContent = JSON.stringify({
      "@context":"https://schema.org","@graph":[
        {"@type":"Organization","name":"ZYNORIQ Intelligence","url":"https://www.zynoriq.com","logo":"https://www.zynoriq.com/favicon.svg","sameAs":["https://www.facebook.com/Zynoriq","https://x.com/Zynoriq","https://www.instagram.com/zynoriqofficial/","https://www.tiktok.com/@zynoriq","https://www.linkedin.com/company/zynoriq/"],"contactPoint":{"@type":"ContactPoint","email":"support@zynoriq.com","contactType":"customer support"}},
        {"@type":"SoftwareApplication","name":"ZYNORIQ","url":"https://www.zynoriq.com","applicationCategory":"UtilitiesApplication","operatingSystem":"Web","offers":{"@type":"AggregateOffer","lowPrice":"19","highPrice":"199","priceCurrency":"USD"},"description":"Lottery prediction platform using 7 ML algorithms — Pick3, Pick4, Lotto, Powerball across 44 US states in 5 languages."}
      ]
    });
    document.head.appendChild(sch);
  }

  // 0c. Inject tracking IDs
  if(!window.ZYNORIQ_GA_ID)   window.ZYNORIQ_GA_ID   = 'G-92CNHZQC61';
  if(!window.ZYNORIQ_META_ID) window.ZYNORIQ_META_ID = '1335183885409898';
  if(!window.ZYNORIQ_CLARITY) window.ZYNORIQ_CLARITY = 'xc5q6t8tp8';

  // 0d. Inject unified tracking (GA4 + Meta Pixel + Clarity)
  if(!document.getElementById('zynoriq-tracking')){
    const trk = document.createElement('script');
    trk.id = 'zynoriq-tracking';
    trk.src = '/tracking.js';
    trk.defer = true;
    document.head.appendChild(trk);
  }

  // 0c. Inject ZYNORIQ COPILOT™
  if(!document.getElementById('copilot-script')){
    const cpScript = document.createElement('script');
    cpScript.id = 'copilot-script';
    cpScript.src = '/copilot.js';
    cpScript.defer = true;
    document.head.appendChild(cpScript);
  }

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

  // 3. ASSISTANT — replaced by ZYNORIQ COPILOT™ (copilot.js)

  // 4. Inject FOOTER (replace existing or append)
  const existingFooter = document.querySelector('footer.zynoriq-footer, footer[data-pfooter]');
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

  // 6. USER MENU — event delegation (bullet-proof, works regardless of timing)
  document.addEventListener('click', function(e){
    // Toggle dropdown (matches both static and async-replaced button)
    const btn = e.target.closest('#pnav-acct-btn, .pnav-user-btn');
    if(btn && btn.closest('.pnav-user')){
      e.preventDefault();
      e.stopPropagation();
      const dd = btn.closest('.pnav-user');
      dd.classList.toggle('open');
      return;
    }
    // Logout button
    const logoutBtn = e.target.closest('.pnav-logout, #pnav-logout-btn');
    if(logoutBtn){
      e.preventDefault();
      fetch('/api/auth/logout', {method:'POST'}).finally(()=>{ location.href = '/'; });
      return;
    }
    // Close on outside click
    const openDD = document.querySelector('.pnav-user.open');
    if(openDD && !openDD.contains(e.target)){
      openDD.classList.remove('open');
    }
  });

  // 7. Auto-inject missing OG/Twitter meta tags
  (function(){
    const h = document.head;
    function ensureMeta(prop,content,attr){
      attr = attr||'property';
      if(!h.querySelector(`meta[${attr}="${prop}"]`)){
        const m=document.createElement('meta');m.setAttribute(attr,prop);m.content=content;h.appendChild(m);
      }
    }
    const title = document.title || 'ZYNORIQ Intelligence';
    const desc = (h.querySelector('meta[name="description"]')||{}).content || 'Lottery prediction platform — 7 ML algorithms, 44 US states, 5 languages.';
    const url = location.href;
    ensureMeta('og:title', title);
    ensureMeta('og:description', desc);
    ensureMeta('og:url', url);
    ensureMeta('og:type', 'website');
    ensureMeta('og:site_name', 'ZYNORIQ Intelligence');
    ensureMeta('og:image', 'https://www.zynoriq.com/favicon.svg');
    ensureMeta('twitter:card', 'summary', 'name');
    ensureMeta('twitter:title', title, 'name');
    ensureMeta('twitter:description', desc, 'name');
    if(!h.querySelector('link[rel="canonical"]')){
      const c=document.createElement('link');c.rel='canonical';c.href=url.split('?')[0];h.appendChild(c);
    }
    // hreflang for international SEO
    if(!h.querySelector('link[hreflang]')){
      const base = url.split('?')[0];
      const langs = {fr:'fr',en:'en',es:'es',pt:'pt',ht:'ht'};
      Object.entries(langs).forEach(function(e){
        const lnk=document.createElement('link');lnk.rel='alternate';lnk.hreflang=e[0];
        lnk.href=base+(base.includes('?')?'&':'?')+'lang='+e[1];h.appendChild(lnk);
      });
      const xd=document.createElement('link');xd.rel='alternate';xd.hreflang='x-default';xd.href=base;h.appendChild(xd);
    }
  })();

  // 8. USER MENU — async upgrade with user info if logged in
  initUserMenu();

  // 9. Smart CTA links: /register → /account for logged-in users
  function rewriteRegisterLinks(){
    if(!_cachedUser) return;
    document.querySelectorAll('a[href*="/register"]').forEach(a=>{
      const href = a.getAttribute('href');
      if(href === '/register' || href.startsWith('/register?')){
        a.href = href.replace('/register', '/account');
      }
    });
  }
  // Wait for user check to complete, then rewrite + observe future DOM changes
  (async()=>{
    if(!_cachedUser){
      try{
        const r = await fetch('/api/auth/me');
        const d = await r.json();
        if(d.user) _cachedUser = d.user;
      }catch(e){}
    }
    rewriteRegisterLinks();
    if(_cachedUser){
      const _regObs = new MutationObserver(()=>{ rewriteRegisterLinks(); });
      _regObs.observe(document.body, {childList:true, subtree:true});
    }
  })();
}

if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded', inject);
} else {
  inject();
}

})();
