#!/usr/bin/env python3
"""Monta livros/ru/99-vocabulario-oficial.html a partir de dados/russo/*.txt"""
import html, re, glob
D = 'dados/russo'
esc = html.escape
def key(s):
    s = s.lower().replace('ё', 'е\u0001')
    return re.sub(r'[^\w\u0001]', '', s)
def pares(f):
    out = []
    for l in open(f, encoding='utf8'):
        l = l.rstrip('\n')
        if l.strip(): out.append(tuple(x.strip() for x in l.split('|', 1)))
    return out
alfa = []
for f in sorted(glob.glob(f'{D}/alfa*.txt')): alfa += pares(f)
vistos = set(); a2 = []
for ru, pt in alfa:
    if (ru, pt) in vistos: continue
    vistos.add((ru, pt)); a2.append((ru, pt))
a2.sort(key=lambda p: key(p[0]))
out = []; letra = None
for ru, pt in a2:
    L = key(ru)[:1].upper().replace('\u0001', '') or '#'
    if L != letra:
        letra = L; out.append(f'<div class="lt">{esc(L)}</div>')
    out.append(f'<p class="g"><b>{esc(ru)}</b> – {esc(pt)}</p>')
ALFA = '\n'.join(out)
g = []
for l in open(f'{D}/grupos.txt', encoding='utf8'):
    l = l.strip()
    if not l: continue
    if l.startswith('## '):
        ru, pt = [x.strip() for x in l[3:].split('|', 1)]
        g.append(f'<div class="gt">{esc(ru)} <i>— {esc(pt)}</i></div>')
    elif l.startswith('# '):
        ru, pt = [x.strip() for x in l[2:].split('|', 1)]
        g.append(f'<div class="gt" style="font-size:11.5px;margin-top:12px">{esc(ru)} <i>— {esc(pt)}</i></div>')
    else:
        for it in l.split('; '):
            ru, pt = it.split('=', 1)
            g.append(f'<p class="g"><b>{esc(ru.strip())}</b> – {esc(pt.strip())}</p>')
GRUPOS = '\n'.join(g)
def bloco(f): return '\n'.join(f'<p class="g"><b>{esc(a)}</b> – {esc(b)}</p>' for a, b in pares(f))
doc = f'''{open(f"{D}/intro.html", encoding="utf8").read()}
<h2>Parte 1. Grupos temáticos</h2>
<p class="lv-nota">O léxico mínimo organizado por assunto: pessoas, corpo, saúde, comida, casa, estudo, cidade, viagens, natureza, tempo e números. Muitas palavras aparecem em mais de um grupo, como no original.</p>
<div class="lv-gloss">
{GRUPOS}
</div>
<h2>Parte 2. Dicionário russo–português</h2>
<p class="lv-nota">Ordem alfabética do alfabeto russo. Quando a palavra tem par de aspecto verbal, os dois aparecem juntos.</p>
<div class="lv-gloss">
{ALFA}
</div>
<h2>Parte 3. Apêndices</h2>
<h3>Nomes russos mais usados</h3>
<p class="lv-nota">Nome completo e forma carinhosa (diminutivo), com o nome em português quando existe equivalente.</p>
<div class="lv-gloss">
{bloco(f"{D}/ap_nomes.txt")}
</div>
<h3>Sinônimos</h3>
<div class="lv-gloss">
{bloco(f"{D}/ap_sin.txt")}
</div>
<h3>Antônimos</h3>
<div class="lv-gloss">
{bloco(f"{D}/ap_ant.txt")}
</div>
<h3>Palavras correlatas</h3>
<div class="lv-gloss">
{bloco(f"{D}/ap_corr.txt")}
</div>
<h3>Termos linguísticos</h3>
<p class="lv-nota">Os termos que aparecem nas instruções e nos livros de gramática.</p>
<div class="lv-gloss">
{bloco(f"{D}/ap_term.txt")}
</div>
<h2>Fonte e créditos</h2>
{open(f"{D}/fonte.html", encoding="utf8").read()}
'''
open('livros/ru/99-vocabulario-oficial.html', 'w', encoding='utf8').write(doc)
print(len(a2), 'verbetes;', GRUPOS.count('class="g"'), 'itens temáticos')
