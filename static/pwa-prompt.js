// PREDIKTA — PWA Install Prompt
// Affiche un mini-modal après 2 pages visitées, une seule fois, si non installé

(function(){
  const KEY_DISMISSED = '_pwa_dismissed';
  const KEY_VISITS    = '_pwa_visits';

  // Déjà installé (standalone) ou déjà refusé → rien
  if(window.matchMedia('(display-mode: standalone)').matches) return;
  if(localStorage.getItem(KEY_DISMISSED)) return;

  // Compte les visites
  const visits = parseInt(localStorage.getItem(KEY_VISITS) || '0') + 1;
  localStorage.setItem(KEY_VISITS, visits);
  if(visits < 2) return; // attendre 2 pages visitées

  let _deferredPrompt = null;

  window.addEventListener('beforeinstallprompt', e => {
    e.preventDefault();
    _deferredPrompt = e;
    // Délai 3s pour laisser la page charger
    setTimeout(_showPrompt, 3000);
  });

  function _showPrompt(){
    if(document.getElementById('_pwaModal')) return;

    const modal = document.createElement('div');
    modal.id = '_pwaModal';
    modal.style.cssText = [
      'position:fixed','bottom:24px','left:50%','transform:translateX(-50%)',
      'z-index:99999','width:min(380px,calc(100vw - 32px))',
      'background:#0f0f2a','border:1.5px solid rgba(124,58,237,.5)',
      'border-radius:18px','padding:20px 22px','box-shadow:0 16px 60px rgba(0,0,0,.6)',
      'animation:_pwaSlide .35s cubic-bezier(.4,0,.2,1)',
      'display:flex','gap:14px','align-items:center',
    ].join(';');

    // Keyframe
    if(!document.getElementById('_pwaStyle')){
      const s = document.createElement('style');
      s.id = '_pwaStyle';
      s.textContent = '@keyframes _pwaSlide{from{opacity:0;transform:translateX(-50%) translateY(20px)}to{opacity:1;transform:translateX(-50%) translateY(0)}}';
      document.head.appendChild(s);
    }

    modal.innerHTML = `
      <div style="flex-shrink:0;width:44px;height:44px;border-radius:12px;background:linear-gradient(135deg,#4f6eff,#7c3aed);display:flex;align-items:center;justify-content:center;font-size:1.4rem">🎯</div>
      <div style="flex:1;min-width:0">
        <div style="font-weight:800;font-size:.88rem;color:#e2e8f0;margin-bottom:3px">Installer PREDIKTA</div>
        <div style="font-size:.72rem;color:#64748b;line-height:1.4">Accès rapide · Notifs push · Fonctionne hors-ligne</div>
        <div style="display:flex;gap:8px;margin-top:10px">
          <button id="_pwaInstall" style="padding:6px 16px;border-radius:8px;border:none;background:linear-gradient(135deg,#4f6eff,#7c3aed);color:#fff;font-size:.75rem;font-weight:700;cursor:pointer">Installer →</button>
          <button id="_pwaDismiss" style="padding:6px 12px;border-radius:8px;border:1px solid rgba(255,255,255,.1);background:none;color:#64748b;font-size:.72rem;cursor:pointer">Plus tard</button>
        </div>
      </div>
      <button onclick="document.getElementById('_pwaModal').remove();localStorage.setItem('${KEY_DISMISSED}','1')" style="position:absolute;top:10px;right:12px;background:none;border:none;color:#475569;font-size:1rem;cursor:pointer;line-height:1">✕</button>`;

    document.body.appendChild(modal);

    document.getElementById('_pwaInstall').onclick = async () => {
      modal.remove();
      if(_deferredPrompt){
        _deferredPrompt.prompt();
        const { outcome } = await _deferredPrompt.userChoice;
        localStorage.setItem(KEY_DISMISSED, '1');
        _deferredPrompt = null;
      }
    };

    document.getElementById('_pwaDismiss').onclick = () => {
      modal.remove();
      // "Plus tard" → réessaie dans 3 jours
      const retry = Date.now() + 3*24*3600*1000;
      localStorage.setItem(KEY_DISMISSED, retry.toString());
    };

    // Auto-ferme après 12s
    setTimeout(() => modal?.remove(), 12000);
  }

  // Sur iOS/Safari : beforeinstallprompt n'existe pas → instruction manuelle
  const isIos = /iphone|ipad|ipod/i.test(navigator.userAgent);
  const isSafari = /safari/i.test(navigator.userAgent) && !/chrome/i.test(navigator.userAgent);
  if(isIos && isSafari && visits >= 3){
    setTimeout(()=>{
      if(document.getElementById('_pwaModal')) return;
      const modal = document.createElement('div');
      modal.id = '_pwaModal';
      modal.style.cssText = 'position:fixed;bottom:24px;left:50%;transform:translateX(-50%);z-index:99999;width:min(360px,calc(100vw - 32px));background:#0f0f2a;border:1.5px solid rgba(124,58,237,.4);border-radius:16px;padding:18px 20px;box-shadow:0 16px 60px rgba(0,0,0,.6);text-align:center';
      modal.innerHTML = `
        <div style="font-size:1.5rem;margin-bottom:8px">📲</div>
        <div style="font-weight:800;font-size:.88rem;color:#e2e8f0;margin-bottom:6px">Installer PREDIKTA sur iPhone</div>
        <div style="font-size:.72rem;color:#64748b;line-height:1.5">Appuyez sur <strong style="color:#88aaff">⬆️ Partager</strong> puis <strong style="color:#88aaff">Sur l'écran d'accueil</strong></div>
        <button onclick="this.closest('#_pwaModal').remove();localStorage.setItem('${KEY_DISMISSED}','1')" style="margin-top:12px;padding:6px 18px;border-radius:8px;border:none;background:rgba(124,58,237,.2);color:#a78bfa;font-size:.72rem;cursor:pointer">OK, compris</button>`;
      document.body.appendChild(modal);
      setTimeout(()=>modal?.remove(), 10000);
    }, 4000);
  }

})();
