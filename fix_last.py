import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

c = open('C:/Users/PC/Downloads/lottery-analyzer/static/index.html', encoding='utf-8').read()

for m in re.finditer(r'onclick="return false"', c):
    ctx = c[max(0,m.start()-200):m.end()+200]
    print("FOUND AT", m.start(), ":", ctx[:300])
    print()

# Fix: the inline banner CTA button is likely still blocked
# Replace it with the affiliate link
c = c.replace(
    'onclick="return false">Jouer →</button>',
    'onclick="window.open(window.PREDIKTA_AFFILIATE.thelotter,\'_blank\')">Jouer →</button>'
)

remaining = c.count('onclick="return false"')
print(f"Remaining blocked links: {remaining}")
open('C:/Users/PC/Downloads/lottery-analyzer/static/index.html', 'w', encoding='utf-8').write(c)
print("Saved.")
