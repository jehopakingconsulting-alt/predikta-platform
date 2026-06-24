/**
 * ZYNORIQ — Unified Tracking (GA4 + Meta Pixel + Microsoft Clarity)
 * Injected via nav.js on every page. IDs configured via data attributes
 * or window globals. No-op if IDs are not set.
 */
(function(){
  const GA_ID    = window.ZYNORIQ_GA_ID    || '';
  const META_ID  = window.ZYNORIQ_META_ID  || '';
  const CLARITY  = window.ZYNORIQ_CLARITY  || '';

  // ── Google Analytics 4 ──────────────────────────────────────────────
  if(GA_ID && GA_ID !== 'G-PLACEHOLDER'){
    const s = document.createElement('script');
    s.async = true;
    s.src = `https://www.googletagmanager.com/gtag/js?id=${GA_ID}`;
    document.head.appendChild(s);
    window.dataLayer = window.dataLayer || [];
    window.gtag = function(){ dataLayer.push(arguments); };
    gtag('js', new Date());
    gtag('config', GA_ID, { send_page_view: true });
  }

  // ── Meta Pixel (Facebook) ──────────────────────────────────────────
  if(META_ID){
    !function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){
    n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};
    if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
    n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;
    s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}
    (window,document,'script','https://connect.facebook.net/en_US/fbevents.js');
    fbq('init', META_ID);
    fbq('track', 'PageView');
  }

  // ── Microsoft Clarity ──────────────────────────────────────────────
  if(CLARITY){
    (function(c,l,a,r,i,t,y){
      c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
      t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
      y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
    })(window,document,"clarity","script",CLARITY);
  }

  // ── Custom Events API ──────────────────────────────────────────────
  window.zTrack = function(eventName, params){
    params = params || {};
    if(window.gtag)    gtag('event', eventName, params);
    if(window.fbq)     fbq('trackCustom', eventName, params);
    if(window.clarity)  clarity('event', eventName);
  };

  // ── Auto-track key events ─────────────────────────────────────────
  document.addEventListener('click', function(e){
    const btn = e.target.closest('button, a');
    if(!btn) return;
    const txt = (btn.textContent||'').trim().substring(0,40);
    const href = btn.getAttribute('href') || '';

    // Registration
    if(btn.id === 'btnRegister' || href === '/register'){
      zTrack('sign_up_click', {method: 'form'});
    }
    // Plan selection
    if(btn.classList.contains('submit') && location.pathname === '/register'){
      const plan = document.querySelector('.plan.selected');
      if(plan) zTrack('begin_checkout', {plan: plan.dataset.plan});
    }
    // Analyze button
    if(btn.id === 'btn-analyze' || txt.includes('Analyser') || txt.includes('Analyze')){
      zTrack('analyze_click', {page: location.pathname});
    }
    // Scrape button
    if(btn.id === 'btn-scrape'){
      zTrack('scrape_click');
    }
    // PDF download
    if(txt.includes('PDF') || txt.includes('Rapport')){
      zTrack('pdf_download');
    }
    // Copilot open
    if(btn.id === 'copilot-fab' || txt.includes('Copilot')){
      zTrack('copilot_open');
    }
    // Pricing CTA
    if(href === '/pro' || href.includes('plan=')){
      zTrack('pricing_view', {source: location.pathname});
    }
  });

  // ── Track page timing ─────────────────────────────────────────────
  window.addEventListener('load', function(){
    setTimeout(function(){
      if(window.gtag && performance.timing){
        var t = performance.timing;
        gtag('event', 'page_load_time', {
          value: t.loadEventEnd - t.navigationStart,
          page: location.pathname
        });
      }
    }, 100);
  });

})();
