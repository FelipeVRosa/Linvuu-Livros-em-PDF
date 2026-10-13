#!/usr/bin/env python3
"""Monta livros/en/99-vocabulario-basico.html a partir de dados/ingles (en_N.json + grupos_en.json)"""
import json, re, html, glob
D = 'dados/ingles'
esc = html.escape
rows = []
for f in sorted(glob.glob(f'{D}/en_[0-9].json')):
    for x in json.load(open(f, encoding='utf8')):
        if x.get('skip') or not x.get('en'): 
            pass
        else: rows.append((x['en'], x['pt']))
        for e in x.get('extra') or []:
            if e.get('en'): rows.append((e['en'], e['pt']))
lim = f'{D}/limpeza_en.json'
import os
if os.path.exists(lim):
    L = json.load(open(lim, encoding='utf8'))
    rem = set(L.get('remover', []))
    cor = {c['en']: c for c in L.get('corrigir', [])}
    nrows = []
    for en, pt in rows:
        if en in rem: continue
        if en in cor:
            en2 = cor[en].get('en_novo', en); pt = cor[en].get('pt', pt); en = en2
        nrows.append((en, pt))
    rows = nrows + [(a['en'], a['pt']) for a in L.get('adicionar', [])]
def head(en): return re.split(r'\s*\(', en, 1)[0].strip().lower()
def lemma_parts(en):
    m = re.match(r'^(.*?)(\s*\(.*)?$', en)
    return m.group(1), (m.group(2) or '')
# dedupe por (cabeçalho, classe): junta traduções
vistos = {}
for en, pt in rows:
    k = en.lower()
    if k in vistos:
        if pt not in vistos[k][1]: vistos[k] = (en, vistos[k][1] + '; ' + pt)
    else: vistos[k] = (en, pt)
rows = sorted(vistos.values(), key=lambda r: (re.sub(r'[^a-z]', '', head(r[0])), r[0].lower()))
out = []; letra = None
for en, pt in rows:
    L0 = (re.sub(r'[^a-z]', '', head(en))[:1] or '#').upper()
    if L0 != letra:
        letra = L0; out.append(f'<div class="lt">{esc(L0)}</div>')
    a, b = lemma_parts(en)
    out.append(f'<p class="g"><b>{esc(a)}</b><span class="f">{esc(b)}</span> – {esc(pt)}</p>')
ALFA = '\n'.join(out)
g = []
for gr in json.load(open(f'{D}/grupos_en.json', encoding='utf8')):
    g.append(f'<div class="gt">{esc(gr["titulo_en"])} <i>— {esc(gr["titulo_pt"])}</i></div>')
    for it in gr['itens']:
        g.append(f'<p class="g"><b>{esc(it["en"])}</b> – {esc(it["pt"])}</p>')
GR = '\n'.join(g)
doc = f'''{open(f"{D}/intro.html", encoding="utf8").read()}
<h2>Parte 1. Grupos de palavras</h2>
<p class="lv-nota">Números, horas, datas, cores, profissões, família e outros grupos que valem aprender por tema.</p>
<div class="lv-gloss">
{GR}
</div>
<h2>Parte 2. Glossário inglês–português</h2>
<p class="lv-nota">Ordem alfabética. Verbos irregulares trazem passado e particípio; substantivos irregulares trazem o plural.</p>
<div class="lv-gloss">
{ALFA}
</div>
<h2>Fonte e créditos</h2>
{open(f"{D}/fonte.html", encoding="utf8").read()}
'''
open('livros/en/99-vocabulario-basico.html', 'w', encoding='utf8').write(doc)
print(len(rows), 'verbetes;', GR.count('class="g"'), 'itens de grupos')
