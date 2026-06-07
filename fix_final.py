"""Fix remaining blocked links + add GA4 to bizai.html + complete results.html translations."""
import re

# ── FIX 1: index.html remaining blocked links ─────────────────────────────
path = 'C:/Users/PC/Downloads/lottery-analyzer/static/index.html'
c = open(path, encoding='utf-8').read()

# Fix newsletter button in sidebar → wire to real API
c = c.replace(
    '<button class="nl-btn" onclick="return false">S\'abonner Gratuitement</button>',
    '<button class="nl-btn" onclick="subscribeNewsletter()">S\'abonner Gratuitement</button>'
)

# Fix sb-btn in sidebar → wire to real subscribe
c = c.replace(
    '<button class="sb-btn" onclick="return false">S\'abonner — Gratuit 7 jours</button>',
    '<button class="sb-btn" onclick="window.location=\'/pro\'">S\'abonner — Gratuit 7 jours</button>'
)

# Fix all remaining onclick="return false" on affiliate sponsor buttons
c = c.replace(
    'onclick="return false">Jouer Maintenant →</button>',
    'onclick="window.open(window.PREDIKTA_AFFILIATE.thelotter,\'_blank\')">Jouer Maintenant →</button>'
)
c = c.replace(
    'onclick="return false">Jouer →</button>',
    'onclick="window.open(window.PREDIKTA_AFFILIATE.thelotter,\'_blank\')">Jouer →</button>'
)

# Count remaining
remaining = c.count('onclick="return false"')
open(path, 'w', encoding='utf-8').write(c)
print(f'index.html: liens bloques restants = {remaining}')

# ── FIX 2: bizai.html → add GA4 ──────────────────────────────────────────
path2 = 'C:/Users/PC/Downloads/lottery-analyzer/static/bizai.html'
c2 = open(path2, encoding='utf-8').read()
if 'googletagmanager' not in c2:
    ga_snippet = '''<!-- Google Analytics 4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer=window.dataLayer||[];
  function gtag(){dataLayer.push(arguments);}
  gtag('js',new Date()); gtag('config','G-XXXXXXXXXX',{anonymize_ip:true});
  function trackEvent(a,c,l){gtag('event',a,{event_category:c,event_label:l});}
</script>
<!-- PWA -->
<script>if('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(()=>{});</script>
'''
    c2 = c2.replace('<script src="/nav.js"></script>', ga_snippet + '<script src="/nav.js"></script>')
    open(path2, 'w', encoding='utf-8').write(c2)
    print('bizai.html: GA4 ajoute')
else:
    print('bizai.html: GA4 deja present')

# ── FIX 3: results.html → add ES/PT/HT translations ─────────────────────
path3 = 'C:/Users/PC/Downloads/lottery-analyzer/static/results.html'
c3 = open(path3, encoding='utf-8').read()

# Find the LANGS dict and add missing languages
old_langs = """  en:{title:"USA Lottery Results",sub:"Cash3 · Pick3 · Daily3 · 30 States · Updated Daily",search:"Search a State... e.g. New York, Texas, Florida",gridTitle:"All States",today:"Today",yesterday:"Yesterday",noData:"No data",update:"Update",noDataMsg:"No data available for this state.",scrapeBtn:"🔄 Load Data",loading:"Loading...",draws:"draws",allStates:"All States",hasData:"Data available",todayRes:"Today's results"},"""

new_langs = old_langs + """
  es:{title:"Resultados de Lotería USA",sub:"Cash3 · Pick3 · Daily3 · 30 Estados · Actualizado diariamente",search:"Buscar un Estado... ej: New York, Texas, Florida",gridTitle:"Todos los Estados",today:"Hoy",yesterday:"Ayer",noData:"Sin datos",update:"Actualizar",noDataMsg:"No hay datos disponibles para este estado.",scrapeBtn:"🔄 Cargar Datos",loading:"Cargando...",draws:"sorteos",allStates:"Todos los Estados",hasData:"Datos disponibles",todayRes:"Resultados de hoy"},
  pt:{title:"Resultados da Loteria USA",sub:"Cash3 · Pick3 · Daily3 · 30 Estados · Atualizado diariamente",search:"Buscar um Estado... ex: New York, Texas, Florida",gridTitle:"Todos os Estados",today:"Hoje",yesterday:"Ontem",noData:"Sem dados",update:"Atualizar",noDataMsg:"Nenhum dado disponível para este estado.",scrapeBtn:"🔄 Carregar Dados",loading:"Carregando...",draws:"sorteios",allStates:"Todos os Estados",hasData:"Dados disponíveis",todayRes:"Resultados de hoje"},
  ht:{title:"Rezilta Lotri USA",sub:"Cash3 · Pick3 · 30 Eta · Mete ajou chak jou",search:"Chèche yon Eta... egz: New York, Texas, Florida",gridTitle:"Tout Eta yo",today:"Jodi a",yesterday:"Ayè",noData:"Pa gen done",update:"Mete ajou",noDataMsg:"Pa gen done pou eta sa a.",scrapeBtn:"🔄 Chaje Done",loading:"Ap chaje...",draws:"tiraj",allStates:"Tout Eta yo",hasData:"Done disponib",todayRes:"Rezilta jodi a"},"""

if 'es:{title:' not in c3:
    c3 = c3.replace(old_langs, new_langs)
    open(path3, 'w', encoding='utf-8').write(c3)
    print('results.html: ES/PT/HT ajoutes')
else:
    print('results.html: traductions deja presentes')

print('\nFixes done.')
