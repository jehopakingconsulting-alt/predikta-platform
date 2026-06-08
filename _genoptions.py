import re

names = {
 "AL":"Alabama","AR":"Arkansas","AZ":"Arizona","CA":"California","CO":"Colorado",
 "CT":"Connecticut","DC":"Washington D.C.","DE":"Delaware","FL":"Florida","GA":"Georgia",
 "IA":"Iowa","ID":"Idaho","IL":"Illinois","IN":"Indiana","KS":"Kansas","KY":"Kentucky",
 "LA":"Louisiana","MA":"Massachusetts","MD":"Maryland","ME":"Maine","MI":"Michigan",
 "MN":"Minnesota","MO":"Missouri","MS":"Mississippi","NC":"North Carolina","NE":"Nebraska",
 "NH":"New Hampshire","NJ":"New Jersey","NM":"New Mexico","NY":"New York","OH":"Ohio",
 "OK":"Oklahoma","OR":"Oregon","PA":"Pennsylvania","PR":"Puerto Rico","RI":"Rhode Island",
 "SC":"South Carolina","TN":"Tennessee","TX":"Texas","VA":"Virginia","VT":"Vermont",
 "WA":"Washington","WI":"Wisconsin","WV":"West Virginia",
}

src = open('app.py', encoding='utf-8').read()
m = re.search(r'STATE_FLAGS = \{(.*?)\n\}', src, re.S)
flags = dict(re.findall(r'"(\w\w)":"([^"]+)"', m.group(1)))

codes = sorted(names.keys())
lines = []
for c in codes:
    lines.append(f'      <option value="{c}">{flags.get(c,"")} {names[c]}</option>')
block = "    <optgroup label=\"── Tous les États (A-Z) ──\">\n" + "\n".join(lines) + "\n    </optgroup>"
print(block)
