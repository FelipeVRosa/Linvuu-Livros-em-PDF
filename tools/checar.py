#!/usr/bin/env python3
"""Verificações mecânicas de um capítulo .md. uso: checar.py arquivo.md [...]"""
import re, sys
def checar(p):
    s = open(p, encoding='utf8').read(); av = []
    if len(re.findall(r'(?m)^# ', s)) != 1: av.append('deve haver exatamente um H1')
    if s.count('{{') != s.count('}}'): av.append('{{ }} desbalanceado')
    # containers
    abre = len(re.findall(r'(?m)^:{3,}[ \t]*\w+', s)); fecha = len(re.findall(r'(?m)^:{3,}[ \t]*$', s))
    if abre != fecha: av.append(f'containers: {abre} abertos x {fecha} fechados')
    h2 = re.findall(r'(?m)^## (.*)$', s)
    if re.search(r'Cena|Treino|Retorno', s):  # livros em português no formato do professor
        for n, nome in [(1,'Cena'),(2,'armadilha'),(3,'Descubra'),(4,'30 segundos'),(5,'Por dentro'),(6,'Frases de ouro'),(7,'Treino'),(8,'erro típico'),(9,'Retorno'),(10,'Resumo')]:
            if not any(h.startswith(f'{n}.') and nome.lower() in h.lower() for h in h2): av.append(f'falta seção {n}. {nome}')
        if not any(h.startswith('Glossário') for h in h2): av.append('falta Glossário')
        if not any(h.startswith('Chave') for h in h2): av.append('falta Chave comentada')
    # tabelas: colunas consistentes
    for bloco in re.findall(r'(?:^\|.*\n)+', s, flags=re.M):
        ls = bloco.strip('\n').split('\n'); n = ls[0].count('|')
        if any(l.count('|') != n and not l.count('\\|') for l in ls): av.append('tabela com número de colunas irregular: ' + ls[0][:50])
        if any(re.match(r'\|\s*\|', l) and not set(l) <= set('| -') for l in ls[2:]): pass
    # exercícios x chave: conta itens numerados
    m = re.search(r'(?ms)^## 7\..*?(?=^## 8\.)', s); k = re.search(r'(?ms)^## Chave.*', s)
    if m and k:
        itens = len(re.findall(r'(?m)^\d+\.\s', m.group(0)))
        chave = len(re.findall(r'(?m)^\d+\.\s', k.group(0))) + len(re.findall(r'(?m)^\*\*Degrau', k.group(0)))
        if chave == 0: av.append('chave sem itens numerados')
    pal = len(re.sub(r'[`*#|:_{}~\-]', ' ', s).split())
    if pal < 2000: av.append(f'curto: {pal} palavras')
    for l in s.split('\n'):
        if '<' in l and re.search(r'</?(br|p|div|span|table)\b', l): av.append('HTML no texto: ' + l[:50]); break
    return pal, av
rc = 0
for p in sys.argv[1:]:
    pal, av = checar(p)
    print(f'{p}: {pal} palavras', 'OK' if not av else '')
    for a in av: print('  -', a); rc = 1
sys.exit(rc)
