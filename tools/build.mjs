// Monta o PDF de um livro da Linvuu: capa + sumário + aulas + contracapa.
//   node tools/build.mjs <pasta-do-livro> [--rapido]      ex.: node tools/build.mjs br-en
// Cada livro fica em livros/<pasta>/ com livro.json e uma aula por arquivo .md (00-intro.md, 01-....md).
// Saída: saida/<pasta>.pdf (e saida/<pasta>.html para conferir no navegador).
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';
import MarkdownIt from 'markdown-it';
import container from 'markdown-it-container';
import { chromium } from 'playwright';

const raiz = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const pasta = process.argv[2];
if (!pasta) { console.error('uso: node tools/build.mjs <pasta-do-livro>'); process.exit(1); }
const dirLivro = path.join(raiz, 'livros', pasta);
const meta = JSON.parse(fs.readFileSync(path.join(dirLivro, 'livro.json'), 'utf8'));
const saida = path.join(raiz, 'saida');
fs.mkdirSync(saida, { recursive: true });
const CHROMIUM = process.env.PLAYWRIGHT_CHROMIUM || '/opt/pw-browsers/chromium';

const R = meta.rotulos; // rótulos na língua do livro
const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const slug = (s) => s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 60);

// ---------- Markdown ----------
const md = new MarkdownIt({ html: true, typographer: true, breaks: false });
md.core.ruler.disable(["replacements"]);
// guias de pronúncia longos precisam quebrar linha
md.renderer.rules.code_inline = (tokens, idx) => { const c = tokens[idx].content; return `<code${c.length > 34 ? ' class="lv-longo"' : ''}>${esc(c)}</code>`; };
// {{texto}} = texto no idioma estudado (Literata)
md.inline.ruler.before('emphasis', 'alvo', (state, silent) => {
  const s = state.src, i = state.pos;
  if (s.charCodeAt(i) !== 0x7b || s.charCodeAt(i + 1) !== 0x7b) return false;
  const fim = s.indexOf('}}', i + 2);
  if (fim < 0) return false;
  if (!silent) {
    const t = state.push('alvo_open', 'span', 1); t.attrs = [['class', 'lv-alvo']];
    const filhos = [];
    state.md.inline.parse(s.slice(i + 2, fim), state.md, state.env, filhos); // tokeniza e resolve negrito/itálico
    for (const f of filhos) state.tokens.push(f);
    state.push('alvo_close', 'span', -1);
  }
  state.pos = fim + 2;
  return true;
});
// tabelas: envoltório e classe da matriz de marca
md.renderer.rules.table_open = () => '<div class="lv-matriz-wrap"><table class="lv-matriz">\n';
md.renderer.rules.table_close = () => '</table></div>\n';
let ids = new Set();
const unico = (base) => { let id = base || 'x', n = 2; while (ids.has(id)) id = `${base}-${n++}`; ids.add(id); return id; };
md.renderer.rules.heading_open = (tokens, idx, o, env, self) => {
  const t = tokens[idx];
  if (t.tag === 'h1' || t.tag === 'h2') {
    const texto = tokens[idx + 1].children.map((c) => c.content).join('');
    t.attrSet('id', unico(slug(texto)));
    env.titulos.push({ nivel: t.tag === 'h1' ? 1 : 2, texto, id: t.attrGet('id') });
  }
  return self.renderToken(tokens, idx, o);
};
const caixa = (nome, classe, rotulo, extra = '') => md.use(container, nome, {
  render(tokens, idx) {
    const t = tokens[idx];
    if (t.nesting === 1) {
      const titulo = t.info.trim().slice(nome.length).trim();
      return `<div class="${classe}"><p class="lv-eyebrow">${esc(rotulo)}${titulo ? ' · ' + esc(titulo) : ''}</p>\n`;
    }
    return '</div>\n';
  },
});
caixa('dica', 'lv-dica', R.dica);
caixa('atencao', 'lv-atencao', R.atencao);
caixa('exercicio', 'lv-exercicio', R.exercicio);
caixa('gabarito', 'lv-gabarito', R.gabarito);
caixa('resumo', 'lv-resumo', R.resumo);
caixa('erros', 'lv-erros-wrap', R.erros);
caixa('comparacao', 'lv-comparacao-wrap', R.comparacao);
caixa('dialogo', 'lv-dialogo', R.dialogo);
md.use(container, 'passo', {
  render(tokens, idx) {
    const t = tokens[idx];
    if (t.nesting === 1) {
      const m = t.info.trim().match(/^passo\s+(\S+)\s*(.*)$/);
      return `<div class="lv-passo"><div class="lv-passo-num">${esc(m?.[1] ?? '')}</div><div class="lv-passo-corpo"><h4>${md.renderInline(m?.[2] ?? '')}</h4>\n`;
    }
    return '</div></div>\n';
  },
});

const tracoSvg = '<svg class="lv-traco" viewBox="0 0 400 20" preserveAspectRatio="none" aria-hidden="true"><path d="M2,11 C40,8.6 90,8.2 140,8.9 C190,9.6 240,7.6 290,7.9 C330,8.1 370,8.8 397,9.6 C399,10 399,11.4 396.5,11.6 C360,12.4 320,11.6 280,11.8 C230,12.1 180,13.4 130,12.6 C80,11.9 40,12.6 4,13.4 C1,13.5 0.5,11.3 2,11 Z" fill="#B7791F"/></svg>';

// ---------- Aulas ----------
const arquivos = fs.readdirSync(dirLivro).filter((f) => /^\d+.*\.(md|html)$/.test(f)).sort();
const titulos = [];
const usados = new Set();
const secoes = arquivos.map((f) => {
  let src = fs.readFileSync(path.join(dirLivro, f), 'utf8');
  let eyebrow = '';
  const fm = src.match(/^---\n([\s\S]*?)\n---\n/);
  if (fm) { eyebrow = (fm[1].match(/eyebrow:\s*(.*)/) ?? [])[1] ?? ''; src = src.slice(fm[0].length); }
  const env = { titulos: [] };
  let html;
  if (f.endsWith('.html')) {
    // aula já em HTML (livro do professor): só indexa os títulos
    html = src.replace(/<h([12])([^>]*)>([\s\S]*?)<\/h\1>/g, (_m, n, attrs, t) => {
      const texto = t.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
      let id = (attrs.match(/id="([^"]+)"/) ?? [])[1];
      if (!id) id = slug(texto) || 'sec';
      { let base = id, k = 2; while (usados.has(id)) id = `${base}-${k++}`; usados.add(id); }
      env.titulos.push({ nivel: Number(n), texto, id });
      return `<h${n}${attrs.replace(/\sid="[^"]*"/, '')} id="${id}">${t}</h${n}>`;
    });
  } else html = md.render(src, env);
  // o primeiro h1 vira abertura de aula
  html = html.replace(/<h1[^>]*?id="([^"]+)"[^>]*>([\s\S]*?)<\/h1>/, (_m, id, t) => `<header class="lv-abertura">${eyebrow ? `<p class="lv-eyebrow">${esc(eyebrow)}</p>` : ''}<h1 id="${id}">${t}</h1>${tracoSvg}</header>`);
  env.titulos.forEach((t) => titulos.push({ ...t, eyebrow: t.nivel === 1 ? eyebrow : '', arquivo: f }));
  return `<section class="lv-aula" data-arquivo="${f}">${html}</section>`;
});

// ---------- Fontes e CSS ----------
const fonte = (fam, arq, extra = '') => `@font-face{font-family:'${fam}';src:url('file://${raiz}/template/fontes/${arq}') format('woff2');font-weight:200 900;${extra}}`;
const latin = 'unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+20AC,U+2122,U+2212;';
const latinExt = 'unicode-range:U+0100-02BA,U+1E00-1EFF,U+2020,U+20A0-20AB;';
const fontesCss = [
  fonte('Newsreader', 'newsreader-latin-opsz-normal.woff2', latin), fonte('Newsreader', 'newsreader-latin-ext-opsz-normal.woff2', latinExt),
  fonte('Source Sans 3', 'source-sans-3-latin-wght-normal.woff2', latin), fonte('Source Sans 3', 'source-sans-3-latin-ext-wght-normal.woff2', latinExt),
  fonte('Literata', 'literata-latin-wght-normal.woff2', latin), fonte('Literata', 'literata-latin-ext-wght-normal.woff2', latinExt),
  fonte('Literata', 'literata-cyrillic-wght-normal.woff2', 'unicode-range:U+0400-045F,U+0490-0491,U+2116;'),
].join('\n');
const marca = fs.readFileSync(path.join(raiz, 'template', 'linvuu.css'), 'utf8').replace(/@import url\([^)]*\);/, '');
const livroCss = fs.readFileSync(path.join(raiz, 'template', 'livro.css'), 'utf8');

const montar = (paginas) => {
  const toc = titulos.filter((t) => t.nivel <= (meta.tocNivel ?? 2));
  const linhaToc = (t) => `<li class="lv-toc-${t.nivel}"><a href="#${t.id}"><span class="lv-toc-t">${t.eyebrow ? `<b>${esc(t.eyebrow)}</b> ` : ''}${esc(t.texto)}</span><span class="lv-toc-leader"></span><span class="lv-toc-p">${paginas?.[t.id] ?? '00'}</span></a></li>`;
  return `<!doctype html><html lang="${meta.lang}"><head><meta charset="utf-8"><title>${esc(meta.titulo)} · Linvuu</title>
<style>${fontesCss}\n${marca}\n${livroCss}</style></head><body class="lv-livro">
<section class="lv-sumario" id="sumario"><p class="lv-eyebrow">${esc(R.livro)}</p><h1 id="toc-titulo" class="lv-toc-h1">${esc(R.sumario)}</h1>${tracoSvg}<ul class="lv-toc">${toc.map(linhaToc).join('\n')}</ul></section>
${secoes.join('\n')}
</body></html>`;
};

// ---------- PDF ----------
const b64 = (arq) => fs.readFileSync(path.join(raiz, 'template', 'fontes', arq)).toString('base64');
const rodape = `<style>@font-face{font-family:'SS3';src:url(data:font/woff2;base64,${b64('source-sans-3-latin-wght-normal.woff2')}) format('woff2');font-weight:200 900}
.f{font-family:'SS3',sans-serif;font-size:8.5px;color:#5C5E57;width:100%;padding:0 18mm;display:flex;justify-content:space-between;letter-spacing:.04em}</style>
<div class="f"><span>Linvuu · ${esc(meta.cabecalho)}</span><span class="pageNumber"></span></div>`;

const navegador = await chromium.launch({ executablePath: CHROMIUM });
async function renderizar(html, arquivo) {
  fs.writeFileSync(arquivo.replace(/\.pdf$/, '.html'), html);
  const p = await navegador.newPage();
  await p.goto(pathToFileURL(arquivo.replace(/\.pdf$/, '.html')).href, { waitUntil: 'load' });
  await p.evaluate(() => document.fonts.ready);
  await p.pdf({ path: arquivo, format: 'A4', printBackground: true, outline: true, tagged: true, preferCSSPageSize: true });
  await p.close();
}
const corpo = path.join(saida, `${pasta}-corpo.pdf`);
await renderizar(montar(null), corpo);

// 2ª passada: números de página do sumário, lidos dos marcadores (outline) do próprio PDF
const py = `
import sys, json
from pypdf import PdfReader
r = PdfReader(sys.argv[1]); out = {}
def walk(items):
    for it in items:
        if isinstance(it, list): walk(it)
        else: out[it.title] = r.get_destination_page_number(it) + 1
walk(r.outline)
print(json.dumps(out))`;
const marcadores = JSON.parse(execFileSync('python3', ['-c', py, corpo], { encoding: 'utf8' }));
const paginas = {};
const norm = (s) => s.replace(/\s+/g, "");
const porNorm = Object.fromEntries(Object.entries(marcadores).map(([k, v]) => [norm(k), v]));
for (const t of titulos) { const n = marcadores[t.texto] || porNorm[norm(t.texto)]; if (n) paginas[t.id] = n; }
const final = path.join(saida, `${pasta}-corpo2.pdf`);
await renderizar(montar(paginas), final);

// ---------- Rodapé com número de página (carimbado depois: o Chromium não pinta o fundo na margem quando há rodapé) ----------
const nPag = Number(execFileSync('pdfinfo', [final], { encoding: 'utf8' }).match(/Pages:\s+(\d+)/)[1]);
const overlayHtml = `<!doctype html><html><head><meta charset="utf-8"><style>${fontesCss}
@page{size:A4;margin:0}html,body{margin:0;background:#F5F1E8}
.pg{position:relative;width:210mm;height:297mm;overflow:hidden;break-after:page}
.f{position:absolute;left:18mm;right:18mm;bottom:9mm;display:flex;justify-content:space-between;align-items:baseline;font:600 8.6px/1 'Source Sans 3',sans-serif;letter-spacing:.14em;text-transform:uppercase;color:#5C5E57;border-top:1px solid rgba(29,31,28,.14);padding-top:7px}
.f b{font-weight:700;color:#1E3B2F;letter-spacing:.04em;font-size:10px}</style></head><body>${Array.from({ length: nPag }, (_, i) => `<div class="pg"><div class="f"><span>Linvuu · ${esc(meta.cabecalho)}</span><b>${i + 1}</b></div></div>`).join('')}</body></html>`;
fs.writeFileSync(path.join(saida, `${pasta}-rodape.html`), overlayHtml);
{
  const po = await navegador.newPage();
  await po.goto(pathToFileURL(path.join(saida, `${pasta}-rodape.html`)).href, { waitUntil: 'load' });
  await po.evaluate(() => document.fonts.ready);
  await po.pdf({ path: path.join(saida, `${pasta}-rodape.pdf`), format: 'A4', printBackground: true, preferCSSPageSize: true });
  await po.close();
  const carimbo = `
import sys
from pypdf import PdfReader, PdfWriter
base = PdfReader(sys.argv[1]); over = PdfReader(sys.argv[2]); w = PdfWriter()
for i, pg in enumerate(over.pages):
    pg.merge_page(base.pages[i]); w.add_page(pg)  # fundo de papel e rodapé por baixo, conteúdo por cima
w.write(sys.argv[3])`;
  execFileSync('python3', ['-c', carimbo, final, path.join(saida, `${pasta}-rodape.pdf`), path.join(saida, `${pasta}-corpo3.pdf`)]);
}

// ---------- Capa e contracapa ----------
const c = meta.capa;
const q = new URLSearchParams({ idioma: c.idioma, saudacao: c.saudacao, lang: c.lang, nivel: c.nivel, vol: String(c.vol ?? 1), foto: c.foto, pos: c.pos ?? '50% 50%', edicao: meta.lang, prog: String(c.prog ?? 40), ...(c.titulo2 ? { titulo2: c.titulo2 } : {}), ...(c.credito ? { credito: c.credito } : {}) });
const pc = await navegador.newPage({ viewport: { width: 817, height: 1145 } });
await pc.goto(pathToFileURL(path.join(raiz, 'template', 'capa', 'capa.html')).href + '?' + q);
await pc.waitForSelector('body[data-pronto="1"]');
await pc.waitForTimeout(400);
const capaPdf = path.join(saida, `${pasta}-capas.pdf`);
await pc.pdf({ path: capaPdf, width: '216mm', height: '303mm', printBackground: true });
await navegador.close();
execFileSync('pdfseparate', [capaPdf, path.join(saida, `${pasta}-capa-%d.pdf`)]);
execFileSync('pdfunite', [path.join(saida, `${pasta}-capa-1.pdf`), path.join(saida, `${pasta}-corpo3.pdf`), path.join(saida, `${pasta}-capa-2.pdf`), path.join(saida, `${pasta}.pdf`)]);
for (const f of fs.readdirSync(saida)) if (new RegExp(`^${pasta}-(capa|corpo|rodape)`).test(f) && f.endsWith('.pdf')) fs.rmSync(path.join(saida, f));
const info = execFileSync('pdfinfo', [path.join(saida, `${pasta}.pdf`)], { encoding: 'utf8' }).match(/Pages:\s+(\d+)/)?.[1];
console.log(`${pasta}.pdf: ${info} páginas · ${Object.keys(paginas).length}/${titulos.length} títulos com página`);
