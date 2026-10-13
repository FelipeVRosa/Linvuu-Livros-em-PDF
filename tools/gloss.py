#!/usr/bin/env python3
"""Monta livros/de/30-vocabulario-oficial.html a partir de dados/glossario (entradas + pt_N.json + grupos_pt.json)."""
import json, re, html, glob, os
D = 'dados/glossario'
esc = html.escape
ent = json.load(open(f'{D}/entradas_todas.json'))
pt = {}
for f in sorted(glob.glob(f'{D}/pt_[0-9].json')):
    for x in json.load(open(f)): pt[x['k']] = x['pt']
if os.path.exists(f'{D}/pt_revisao.json'):
    for x in json.load(open(f'{D}/pt_revisao.json')): pt[x['k']] = x['pt']
lim = f'{D}/limpeza.json'
if os.path.exists(lim):
    L = json.load(open(lim))
    for c in L.get('corrigir', []):
        for e in ent:
            if e['k'] == c['k']:
                if c.get('de'): e['de'] = c['de']
                if c.get('pt'): pt[e['k']] = c['pt']
    rem = set(L.get('remover', []))
    for d in L.get('dividir', []):
        rem.add(d['k'])
        for n in d['novos']:
            ent.append({'k': n['k'], 'de': n['de'], 'lvl': n.get('lvl') or ['A2']}); pt[n['k']] = n['pt']
    ent = [e for e in ent if e['k'] not in rem]
    seen = set(); ent2 = []
    for e in ent:
        if e['k'] in seen: continue
        seen.add(e['k']); ent2.append(e)
    ent = ent2
faltam = [e['de'] for e in ent if e['k'] not in pt]
if faltam: raise SystemExit(f'{len(faltam)} entradas sem tradução: {faltam[:8]}')
grupos = json.load(open(f'{D}/grupos_pt.json'))

def sk(s):
    s = s.lower()
    s = re.sub(r'^(der/die|der/das|die/der|der|die|das|sich|\(sich\))\s+', '', s)
    s = re.sub(r'[()\-¨/\s,.]', '', s)
    return s.replace('ä', 'a').replace('ö', 'o').replace('ü', 'u').replace('ß', 'ss')
def lema(de):
    m = re.match(r'^(.*?)(,\s.*)?$', de)
    return m.group(1), (m.group(2) or '')
def chip(l):
    l = sorted(set(l))
    return 'A1·A2' if l == ['A1', 'A2'] else l[0]
ent.sort(key=lambda e: sk(e['de']))
out = []
letra = None
for e in ent:
    L = (sk(e['de'])[:1] or '#').upper()
    if L != letra:
        letra = L; out.append(f'<div class="lt">{esc(L)}</div>')
    a, b = lema(e['de'])
    out.append(f'<p class="g"><b>{esc(a)}</b><span class="f">{esc(b)}</span> {esc(pt[e["k"]])} <i class="lv">{chip(e["lvl"])}</i></p>')
alfa = '\n'.join(out)
gr = []
for g in grupos:
    gr.append(f'<div class="gt">{esc(g["titulo_de"])} <i>— {esc(g["titulo_pt"])}</i></div>')
    for it in g['itens']:
        gr.append(f'<p class="g"><b>{esc(it["de"])}</b> — {esc(it["pt"])}</p>')
grupos_html = '\n'.join(gr)
intro = open(f'{D}/intro.html').read()
n_a1 = sum('A1' in e['lvl'] for e in ent); n_a2 = sum('A2' in e['lvl'] for e in ent)
intro = intro.replace('{{N_TOTAL}}', str(len(ent))).replace('{{N_A1}}', str(n_a1)).replace('{{N_A2}}', str(n_a2))
doc = f'''{intro}
<h2>Parte 1. Grupos de palavras</h2>
<p class="lv-nota">Números, horas, datas, cores, profissões e outros grupos que as provas tratam à parte. Cada palavra do vocabulário oficial aparece ou aqui ou na Parte 2.</p>
<div class="lv-gloss">
{grupos_html}
</div>
<h2>Parte 2. Glossário alemão–português</h2>
<p class="lv-nota">Ordem alfabética. A etiqueta à direita diz em qual lista a palavra aparece: <b>A1</b>, <b>A2</b> ou <b>A1·A2</b>.</p>
<div class="lv-gloss">
{alfa}
</div>
<h2>Fonte e créditos</h2>
{open(f"{D}/fonte.html").read()}
'''
open('livros/de/30-vocabulario-oficial.html', 'w').write(doc)
print(len(ent), 'entradas;', len(grupos), 'grupos')
