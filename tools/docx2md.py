#!/usr/bin/env python3
"""Converte o .docx do Linvuu (pandoc → gfm) em arquivos .md por capítulo, no formato do build.mjs.
uso: docx2md.py entrada.docx pasta_saida prefixo_h1 [rotulo_cap]"""
import re, subprocess, sys, pathlib, tempfile, os
docx, outdir, h1pat = sys.argv[1], pathlib.Path(sys.argv[2]), sys.argv[3]
LUA = r'''
local function unq(blocks)
  local out = pandoc.List()
  for _,b in ipairs(blocks) do
    if b.t == 'BlockQuote' then out:extend(unq(b.content)) else out:insert(b) end
  end
  return out
end
function Table(t)
  for _,r in ipairs(t.head.rows) do for _,c in ipairs(r.cells) do c.contents = unq(c.contents) end end
  for _,b in ipairs(t.bodies) do for _,r in ipairs(b.body) do for _,c in ipairs(r.cells) do c.contents = unq(c.contents) end end end
  return t
end'''
tmp = pathlib.Path(tempfile.mkdtemp()); (tmp/'f.lua').write_text(LUA)
md = subprocess.run(['pandoc', docx, '-t', 'gfm', '--wrap=none', f'--lua-filter={tmp}/f.lua'], capture_output=True, text=True, check=True).stdout

# --- tabelas html residuais → pipe
def html_table(m):
    t = m.group(0)
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', t, flags=re.S)
    out = []
    for r in rows:
        cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', r, flags=re.S)
        cells = [re.sub(r'\s+', ' ', re.sub(r'</?(p|blockquote)>', ' ', c)).strip() for c in cells]
        cells = [re.sub(r'<strong>(.*?)</strong>', r'**\1**', c) for c in cells]
        cells = [re.sub(r'<em>(.*?)</em>', r'*\1*', c) for c in cells]
        cells = [re.sub(r'<[^>]+>', '', c).replace('|', '\\|') for c in cells]
        out.append(cells)
    if not out: return ''
    n = max(len(r) for r in out)
    out = [r + [''] * (n - len(r)) for r in out]
    lines = ['| ' + ' | '.join(out[0]) + ' |', '|' + '|'.join(['---'] * n) + '|'] + ['| ' + ' | '.join(r) + ' |' for r in out[1:]]
    return '\n'.join(lines)
md = re.sub(r'<table>.*?</table>', html_table, md, flags=re.S)

# --- remove cabeçalhos de tabela repetidos (quebra de página do Word)
def dedupe(block):
    ls = block.split('\n')
    head = ls[0]
    return '\n'.join([ls[0], ls[1]] + [l for l in ls[2:] if l != head])
md = re.sub(r'(?:^\|.*\n)+', lambda m: dedupe(m.group(0).rstrip('\n')) + '\n', md, flags=re.M)

md = md.replace(' ', ' ')
# --- títulos de seção engolidos em listas: "3.  Descubra você mesmoCompare…"
md = re.sub(r'^(\d+)\.\s+(Descubra você mesmo)(?=\S)', lambda m: f'## {m.group(1)}. {m.group(2)}\n\n', md, flags=re.M)
md = re.sub(r'^(\d+)\.\s+(Descubra você mesmo)\s*$', r'## \1. \2', md, flags=re.M)


# --- títulos de seção engolidos por listas do Word (Cena / Treino / Descubra)
md = re.sub(r'(?m)^(?:> )?(\d+)\\?\.\s+(Treino em quatro degraus)\s*', lambda m: f'## {m.group(1)}. {m.group(2)}\n\n', md)
md = re.sub(r'(?m)^(?:> )?3\\?\.\s+(Descubra você mesmo)\s+', r'## 3. \1\n\n', md)
CENAS = {'Cena: como chegar à estação': 'Cena: como chegar à estação', 'Cena: o que você fez ontem?': 'Cena: o que você fez ontem?', 'Cena: onde jantar?': 'Cena: onde jantar?'}
for k in CENAS:
    md = re.sub(r'(?m)^(?:> )?1\\?\.\s+' + re.escape(k) + r'\s*', f'## 1. {k}\n\n', md)

# --- separa capítulos
parts = re.split(r'(?m)^(?=# )', md)
caps = [p for p in parts if re.match(h1pat, p)]
outdir.mkdir(parents=True, exist_ok=True)
SEC = re.compile(r'^## (\d+)\. ', re.M)
def fmt_dialog(m):
    txt = m.group(1)
    txt = re.sub(r'\s*\*\*([^*]+?):\*\*', r'\n\n**\1:**', txt).strip()
    return '::: dialogo\n' + re.sub(r'^> ?', '', txt, flags=re.M) + '\n:::\n'
rel = []
for i, c in enumerate(caps, 1):
    # diálogos: blockquote que começa com "**Nome:**" e tem ≥ 2 falas
    c = re.sub(r'(?m)^> (\*\*[^*\n]+:\*\*[^\n]*)\n(?!>)', lambda m: fmt_dialog(m) if m.group(1).count(':**') >= 2 else m.group(0), c)
    # blocos de aviso do Pretzel
    c = re.sub(r'(?m)^> \*\*Pretzel avisa:\*\*\s*(.*)$', r'::: atencao\n\1\n:::\n', c)
    c = re.sub(r'(?m)^> \*\*Pretzel avisa:\*\*', '::: atencao', c)
    # blockquotes restantes viram parágrafos recuados normais
    c = re.sub(r'(?m)^> ?', '', c)
    # envolve as seções-chave em caixas
    def wrap(name, titulo, box):
        global c
        m = re.search(rf'(?m)^## ({name})\s*$', c)
        if not m: return
        start = m.end()
        n = re.search(r'(?m)^## ', c[start:])
        end = start + n.start() if n else len(c)
        corpo = c[start:end].strip('\n')
        c = c[:m.start()] + f'## {m.group(1)}\n\n::::: {box}\n{corpo}\n:::::\n\n' + c[end:]
    wrap(r'4\. Em 30 segundos', '', 'dica')
    wrap(r'7\. Treino em quatro degraus', '', 'exercicio')
    wrap(r'10\. Resumo e “já consigo”', '', 'resumo')
    m = re.search(r'(?m)^## (Chave comentada.*)$', c)
    if m:
        c = c[:m.end()] + '\n\n::::: gabarito\n' + c[m.end():].strip('\n') + '\n:::::\n'
    secs = [int(x) for x in SEC.findall(c)]
    falta = [n for n in range(1, 11) if n not in secs]
    if falta: rel.append((i, c.split('\n')[0][:60], falta))
    (outdir / f'{i:02d}-cap.md').write_text(c.strip() + '\n')
print(len(caps), 'capítulos')
for r in rel: print('seções sem título:', r)
