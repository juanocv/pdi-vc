#!/usr/bin/env python3
"""
ep_tools.py — Ferramentas unificadas para extração de EPs de HTML Quarto.

Subcomandos:
  extrair   Extrai cada EP de cap*.html e salva em arquivo individual.
  limpar    Extrai o fragmento utilizável (compatível com Moodle/VPL) de cada EPxx_xx.html.

────────────────────────────────────────────────────────────────────────────
EXTRAIR — gera um HTML por EP a partir das páginas de capítulo do Quarto
────────────────────────────────────────────────────────────────────────────
  python ep_tools.py extrair                                  # processa gen/book/*/cap*/*.html
  python ep_tools.py extrair --input gen/book/py.pt           # versão específica
  python ep_tools.py extrair --input gen/book/py.pt/cap01/cap01.py.pt.html  # arquivo único
  python ep_tools.py extrair --out-dir output/eps             # pasta de saída customizada
  python ep_tools.py extrair --dry-run                        # só lista EPs encontrados

  Saída padrão: gen/book/eps/<versao>/EP01_02.html

────────────────────────────────────────────────────────────────────────────
LIMPAR — extrai o fragmento Moodle/VPL de cada EPxx_xx.html já extraído
────────────────────────────────────────────────────────────────────────────
  python ep_tools.py limpar <pasta_entrada> <pasta_saida>
  python ep_tools.py limpar gen/book/eps/py.pt gen/book/eps/py.pt_moodle

  Remove células Jupyter (%%writefile, TestSuite…run()) e descarta tudo fora
  do <div class="ep-container">. Pronto para colar no Moodle.
"""

import argparse
import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup, Tag


# ══════════════════════════════════════════════════════════════════════════════
# PARTE 1 — EXTRAIR: extrai EPs de cap*.html  (extrair_eps.py)
# ══════════════════════════════════════════════════════════════════════════════

# Identifica o título de um EP: h2, h3 ou h4 cujo texto contém "EPXX_YY"
RE_EP_HEADING = re.compile(r'\bEP(\d{2})_(\d{2})\b')

# Identifica a célula %%writefile EPXX_YY.py que fecha o bloco do EP
RE_WRITEFILE = re.compile(r'%%writefile\s+(EP\d{2}_\d{2}\.py)')


HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{ep_id} — {title}</title>
  {styles}
</head>
<body class="ep-standalone">
<div class="ep-container">
{content}
</div>
{scripts}
</body>
</html>
"""


def extract_head_assets(soup: BeautifulSoup) -> tuple[str, str]:
    """
    Extrai <link rel="stylesheet"> e <script> do <head> do documento original
    para que o HTML gerado tenha o mesmo visual do livro.
    Retorna (styles_html, scripts_html).
    """
    styles_parts: list[str] = []
    scripts_parts: list[str] = []

    head = soup.find("head")
    if not head:
        return "", ""

    for tag in head.find_all(["link", "style"]):
        if tag.name == "link" and tag.get("rel") == ["stylesheet"]:
            styles_parts.append(str(tag))
        elif tag.name == "style":
            styles_parts.append(str(tag))

    # Scripts do head (ex: MathJax)
    for tag in head.find_all("script"):
        src = tag.get("src", "")
        if src and any(k in src for k in ("mathjax", "highlight", "quarto")):
            scripts_parts.append(str(tag))
        elif not src and tag.string and "MathJax" in tag.string:
            scripts_parts.append(str(tag))

    # Scripts do body (copy-to-clipboard, etc.)
    body = soup.find("body")
    if body:
        for tag in body.find_all("script"):
            src = tag.get("src", "")
            if src or (tag.string and len(tag.string.strip()) > 0):
                scripts_parts.append(str(tag))

    return "\n  ".join(styles_parts), "\n".join(scripts_parts)


def detect_lang(soup: BeautifulSoup) -> str:
    html_tag = soup.find("html")
    return html_tag.get("lang", "pt") if html_tag else "pt"


def find_ep_blocks(soup: BeautifulSoup) -> list[dict]:
    """
    Percorre o DOM e localiza cada bloco EP.

    Estratégia:
    1. Encontra todos os headings (h2/h3/h4) cujo texto casa com RE_EP_HEADING.
    2. Para cada heading, coleta todos os elementos irmãos seguintes até:
       a) encontrar a célula %%writefile EPXX_YY.py  → inclui e para
       b) encontrar outro heading EP                 → para (não inclui)
       c) encontrar heading de nível igual/superior  → para
    """
    heading_tags = {"h2", "h3", "h4"}
    eps: list[dict] = []

    main = (
        soup.find("main")
        or soup.find("article")
        or soup.find("div", class_=re.compile(r"content|chapter|book"))
        or soup.find("body")
    )
    if not main:
        return []

    ep_headings: list[tuple] = []
    for tag in main.find_all(heading_tags):
        text = tag.get_text(" ", strip=True)
        m = RE_EP_HEADING.search(text)
        if m:
            ep_headings.append((tag, m.group(0)))  # (tag, "EP01_02")

    for heading_tag, ep_id in ep_headings:
        title_text = heading_tag.get_text(" ", strip=True)
        title_text = re.sub(r'^\s*[\d.]+\s+', '', title_text)

        heading_level = int(heading_tag.name[1])  # h3 → 3

        block_elements: list[Tag] = [heading_tag]
        found_writefile = False

        sibling = heading_tag.find_next_sibling()
        while sibling:
            if isinstance(sibling, Tag):
                tag_name = sibling.name

                if tag_name in heading_tags:
                    sib_level = int(tag_name[1])
                    if sib_level <= heading_level:
                        break
                    sib_text = sibling.get_text(" ", strip=True)
                    if RE_EP_HEADING.search(sib_text):
                        break

                sib_text_full = sibling.get_text()
                wf_match = RE_WRITEFILE.search(sib_text_full)
                if wf_match and wf_match.group(1).startswith(ep_id):
                    block_elements.append(sibling)
                    found_writefile = True
                    break

                block_elements.append(sibling)

            sibling = sibling.find_next_sibling()

        eps.append({
            "ep_id": ep_id,
            "title": title_text,
            "elements": block_elements,
            "has_writefile": found_writefile,
        })

    return eps


def elements_to_html(elements: list[Tag]) -> str:
    return "\n".join(str(el) for el in elements)


def build_ep_html(ep: dict, styles: str, scripts: str, lang: str) -> str:
    content = elements_to_html(ep["elements"])
    return HTML_TEMPLATE.format(
        lang=lang,
        ep_id=ep["ep_id"],
        title=ep["title"],
        styles=styles,
        scripts=scripts,
        content=content,
    )


def process_html_file(
    html_path: Path,
    out_dir: Path,
    dry_run: bool = False,
    verbose: bool = True,
) -> list[str]:
    raw = html_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(raw, "html.parser")

    lang = detect_lang(soup)
    styles, scripts = extract_head_assets(soup)
    eps = find_ep_blocks(soup)

    if not eps:
        if verbose:
            print(f"  ⚠️  Nenhum EP encontrado em {html_path.name}")
        return []

    extracted: list[str] = []
    for ep in eps:
        ep_id = ep["ep_id"]
        out_file = out_dir / f"{ep_id}.html"

        if dry_run:
            wf = "✓ writefile" if ep["has_writefile"] else "✗ sem writefile"
            print(f"  [{wf}] {ep_id}  →  {out_file}")
        else:
            out_file.parent.mkdir(parents=True, exist_ok=True)
            html_content = build_ep_html(ep, styles, scripts, lang)
            out_file.write_text(html_content, encoding="utf-8")
            size_kb = out_file.stat().st_size / 1024
            if verbose:
                wf = "✓" if ep["has_writefile"] else "⚠"
                print(f"  {wf} {ep_id}  →  {out_file}  ({size_kb:.0f} KB)")

        extracted.append(ep_id)

    return extracted


def collect_html_files(input_path: Path) -> list[tuple[Path, Path]]:
    pairs: list[tuple[Path, Path]] = []

    if input_path.is_file() and input_path.suffix == ".html":
        parts = input_path.parts
        try:
            book_idx = list(parts).index("book")
            versao_dir = Path(*parts[: book_idx + 2])
        except ValueError:
            versao_dir = input_path.parent
        pairs.append((input_path, versao_dir))

    elif input_path.is_dir():
        for html_file in sorted(input_path.rglob("cap*/*.html")):
            parts = html_file.parts
            try:
                book_idx = list(parts).index("book")
                versao_dir = Path(*parts[: book_idx + 2])
            except ValueError:
                versao_dir = input_path
            pairs.append((html_file, versao_dir))

    return pairs


def cmd_extrair(args: argparse.Namespace) -> None:
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Caminho não encontrado: {input_path}", file=sys.stderr)
        sys.exit(1)

    pairs = collect_html_files(input_path)
    if not pairs:
        print(f"❌ Nenhum arquivo HTML de capítulo encontrado em: {input_path}", file=sys.stderr)
        sys.exit(1)

    verbose = not args.quiet
    total_eps: list[str] = []

    for html_file, versao_dir in pairs:
        if args.out_dir:
            out_dir = Path(args.out_dir)
        else:
            versao_name = versao_dir.name
            book_root = versao_dir.parent
            out_dir = book_root / "eps" / versao_name

        if verbose or args.dry_run:
            print(f"\n📄 {html_file}")

        extracted = process_html_file(
            html_path=html_file,
            out_dir=out_dir,
            dry_run=args.dry_run,
            verbose=verbose,
        )
        total_eps.extend(extracted)

    action = "encontrados" if args.dry_run else "gerados"
    print(f"\n{'─'*50}")
    print(f"✅ {len(total_eps)} EPs {action}: {', '.join(sorted(set(total_eps)))}")

    if not args.dry_run and total_eps and not args.out_dir:
        sample_versao = pairs[0][1].name
        book_root = pairs[0][1].parent
        print(f"📁 Saída: {book_root / 'eps' / sample_versao}/")


# ══════════════════════════════════════════════════════════════════════════════
# PARTE 2 — LIMPAR: extrai e sanitiza fragmento Moodle de EPxx_xx.html
# ══════════════════════════════════════════════════════════════════════════════
#
# Pipeline aplicada a cada arquivo:
#   1. Extrai <div class="ep-container"> ... </div>
#   2. Remove células Quarto/Jupyter (%%writefile, TestSuite, outputs)
#   3. Converte LaTeX inline/display para HTML semântico (sem MathJax)
#   4. Reescreve estrutura Quarto (h.anchored, section.level*, span.header-section-number,
#      quarto-float, figcaption, quarto-xref, data-* attrs) para HTML inline puro
#   5. Reescreve scripts de simulador: padrão init(root)+querySelector+dataset
#      → padrão getElementById direto (gabarito EP03_01, compatível com Moodle/TinyMCE)
#   6. Remove accent-color de inputs (causa erro #rrggbb no TinyMCE)
#
# ─────────────────────────────────────────────────────────────────────────────

# Remove células Quarto com id hexadecimal (%%writefile, TestSuite, outputs)
CELL_RE = re.compile(
    r'<div[^>]+class="cell"[^>]*id="[0-9a-f]{6,}"[\s\S]*?'
    r'(?=<div[^>]+class="cell"|</section>|</div>\s*</section>)',
    re.IGNORECASE,
)

# Remove quarto-float wrapper + figcaption, preservando o conteúdo interno
QUARTO_FLOAT_OUTER_RE = re.compile(
    r'<div[^>]+class="[^"]*cell-output[^"]*"[^>]*>\s*'
    r'<figure[^>]*>([\s\S]*?)</figure>\s*</div>',
    re.IGNORECASE,
)

# Converte <figcaption ...>...</figcaption> → remove
FIGCAPTION_RE = re.compile(r'<figcaption[^>]*>[\s\S]*?</figcaption>', re.IGNORECASE)

# Remove o div aria-describedby que envolve o simulador dentro do figure
ARIA_DIV_RE = re.compile(
    r'<div\s+aria-describedby="[^"]*">([\s\S]*?)</div>',
    re.IGNORECASE,
)


# ── Conversão LaTeX → HTML ────────────────────────────────────────────────────

def _cases_to_inline(m: re.Match) -> str:
    r"""\\begin{cases}...\\end{cases} → versão inline com ponto-e-vírgula."""
    body = m.group(1)
    cases = [c.strip().replace('&', '').strip() for c in re.split(r'\\\\', body)]
    return '; '.join(c for c in cases if c)


def latex_body_to_html(body: str) -> str:
    """Converte o corpo de uma expressão LaTeX (sem delimitadores) em HTML."""
    s = body.strip()

    # \begin{cases}...\end{cases} → inline
    s = re.sub(r'\\begin\{cases\}([\s\S]*?)\\end\{cases\}', _cases_to_inline, s)

    # Comandos LaTeX → entidades HTML / texto
    cmd_map = [
        (r'\\times',  '&times;'),
        (r'\\geq',    '&ge;'),
        (r'\\leq',    '&le;'),
        (r'\\neq',    '&ne;'),
        (r'\\cdot',   '&middot;'),
        (r'\\ldots',  '&hellip;'),
        (r'\\in',     '&isin;'),
        (r'\\alpha',  '&alpha;'),
        (r'\\beta',   '&beta;'),
        (r'\\gamma',  '&gamma;'),
        (r'\\sigma',  '&sigma;'),
        (r'\\mu',     '&mu;'),
        (r'\\pm',     '&plusmn;'),
        (r'\\infty',  '&infin;'),
        (r'\\sum',    '&sum;'),
        (r'\\sqrt\{([^}]*)\}', r'&radic;(\1)'),
        (r'\\frac\{([^}]*)\}\{([^}]*)\}', r'(\1)/(\2)'),
        (r'\\text\{([^}]*)\}', r'\1'),
        (r'\\mathbf\{([^}]*)\}', r'<strong>\1</strong>'),
        (r'\\mathrm\{([^}]*)\}', r'\1'),
        (r'\\_', '_'),
        (r'\\{', '{'),
        (r'\\}', '}'),
    ]
    for pat, repl in cmd_map:
        s = re.sub(pat, repl, s)

    # Variáveis de uma letra (p, T, L, C, k, n, f, g, …) → <em>
    s = re.sub(r'(?<![a-zA-Z&;{])([a-zA-Z])(?![a-zA-Z;={])', r'<em>\1</em>', s)

    # Remover chaves remanescentes e espaços redundantes
    s = s.replace('{', '').replace('}', '')
    s = re.sub(r'  +', ' ', s).strip()
    return s


def convert_math_spans(html: str) -> str:
    """Substitui <span class="math inline/display">\\(...\\)</span> por HTML limpo."""
    def repl_inline(m: re.Match) -> str:
        inner = re.sub(r'^\\\(|\\\)$', '', m.group(1)).strip()
        return latex_body_to_html(inner)

    def repl_display(m: re.Match) -> str:
        inner = re.sub(r'^\\\[|\\\]$', '', m.group(1)).strip()
        converted = latex_body_to_html(inner)
        return (
            '<p style="text-align:center;font-family:monospace;font-size:1.1em;'
            'padding:8px;background:#f8f8f8;border-radius:4px;border:1px solid #ddd;">'
            f'{converted}</p>'
        )

    html = re.sub(r'<span class="math inline">([\s\S]*?)</span>', repl_inline, html)
    html = re.sub(r'<span class="math display">([\s\S]*?)</span>', repl_display, html)
    return html


# ── Sanitização de estrutura Quarto → HTML inline ────────────────────────────

def strip_quarto_structure(html: str) -> str:
    """
    Remove/simplifica estruturas Quarto que dependem de CSS externo:
    - <span class="header-section-number">4.9.1</span> → removido
    - <h3 class="anchored" data-anchor-id="..." data-number="..."> → <h3>
    - <section class="level4" data-number="..." id="..."> → <div>  (fechamento </section> → </div>)
    - class="quarto-xref" → removido (mantém o texto do link)
    - data-anchor-id, data-number, data-execution_count → removidos
    - quarto-float, figcaption wrappers → desenrolados para o conteúdo interno
    - accent-color em style= → removido
    """
    # 1. Remove <span class="header-section-number">...</span>
    html = re.sub(r'<span class="header-section-number">[^<]*</span>\s*', '', html)

    # 2. Limpa atributos Quarto de headings: class="anchored", data-anchor-id, data-number
    def clean_heading(m: re.Match) -> str:
        tag = m.group(1)  # h2, h3, h4
        # Remover class="anchored" e atributos data-*
        inner = m.group(2)
        inner = re.sub(r'\s*class="anchored"', '', inner)
        inner = re.sub(r'\s*data-anchor-id="[^"]*"', '', inner)
        inner = re.sub(r'\s*data-number="[^"]*"', '', inner)
        inner = inner.strip()
        return f'<{tag}{" " + inner if inner else ""}>'

    html = re.sub(
        r'<(h[2-6])(\s[^>]*)?>',
        lambda m: clean_heading(m) if m.group(2) and ('anchored' in m.group(2) or 'data-' in m.group(2)) else m.group(0),
        html,
    )

    # 3. <section class="level*" ...> → <div>  |  </section> → </div>
    html = re.sub(r'<section[^>]+class="level\d+"[^>]*>', '<div>', html, flags=re.IGNORECASE)
    html = re.sub(r'</section>', '</div>', html, flags=re.IGNORECASE)

    # 4. Links quarto-xref: remover class e href interno (ref para figura inexistente)
    html = re.sub(
        r'<a[^>]*class="quarto-xref"[^>]*>([\s\S]*?)</a>',
        r'\1',
        html,
        flags=re.IGNORECASE,
    )

    # 5. data-execution_count e outros data-* soltos nos divs
    html = re.sub(r'\s*data-execution_count="[^"]*"', '', html)
    html = re.sub(r'\s*data-anchor-id="[^"]*"', '', html)
    html = re.sub(r'\s*data-number="[^"]*"', '', html)

    # 6. Desenrolar quarto-float figure wrapper:
    #    <div class="cell-output ... quarto-float ..."><figure ...>CONTEÚDO</figure></div>
    #    → CONTEÚDO (sem figcaption)
    def unwrap_float(m: re.Match) -> str:
        inner = m.group(1)
        # Remover figcaption
        inner = FIGCAPTION_RE.sub('', inner)
        # Remover div aria-describedby wrapper (mantém seu conteúdo)
        inner = re.sub(r'<div\s+aria-describedby="[^"]*">([\s\S]*?)</div>', r'\1', inner)
        return inner.strip()

    html = QUARTO_FLOAT_OUTER_RE.sub(unwrap_float, html)

    # 7. Remove class="cell" wrappers remanescentes (célula do simulador sem id hex)
    html = re.sub(
        r'<div[^>]+class="[^"]*\bcell\b[^"]*"[^>]*>\s*(<div[^>]+id="sim-)',
        r'\1',
        html,
        flags=re.IGNORECASE,
    )

    # 8. accent-color: #... → remove só essa propriedade do style
    html = re.sub(r'\s*accent-color\s*:\s*[^;"\s]+\s*;?', '', html)

    # 9. Limpar classes Quarto desnecessárias de tabelas
    html = re.sub(r'\s*class="caption-top table"', '', html)
    html = re.sub(r'\s*class="(header|odd|even)"', '', html)

    return html


# ── Reescrita de scripts de simulador ────────────────────────────────────────

def rewrite_sim_script(script: str) -> str:
    """
    Reescreve o padrão Quarto:
        (function(){ function init(root){...} function tryInit(){querySelectorAll([id=...])...} setInterval... })()
    para o padrão EP03_01 (compatível com Moodle/TinyMCE):
        (function initXxx(){ var container = getElementById(...); if(!container){setTimeout...} ... })()

    Transforma:
      - root.querySelector('#id') → document.getElementById('id')
      - root.dataset.xyzReady     → removido (guarda de dupla execução)
      - tryInit() + setInterval   → removido (substituído por setTimeout fallback)
    """
    # Detectar id do container do simulador
    sim_id_m = re.search(r'\[id=["\']([^"\']+)["\']\]', script)
    if not sim_id_m:
        return script  # padrão não reconhecido — retorna intacto
    sim_id = sim_id_m.group(1)

    # Detectar nome da variável "root"
    root_m = re.search(r'function init\((\w+)\)', script)
    if not root_m:
        return script
    root_var = root_m.group(1)

    # Extrair o corpo de init(root) — tudo entre o primeiro { e seu } balanceado
    init_start = script.find(f'function init({root_var}){{')
    if init_start == -1:
        init_start = script.find(f'function init({root_var}) {{')
    if init_start == -1:
        return script

    # Avançar até o { de abertura
    brace_open = script.find('{', init_start)
    depth, pos = 0, brace_open
    while pos < len(script):
        if script[pos] == '{':
            depth += 1
        elif script[pos] == '}':
            depth -= 1
            if depth == 0:
                init_body = script[brace_open + 1: pos]
                break
        pos += 1
    else:
        return script

    # Limpar linhas de guarda (dataset e !root)
    init_body = re.sub(rf'\s*if\s*\(!{root_var}\)\s*return;\s*\n?', '\n', init_body)
    init_body = re.sub(
        rf'\s*if\s*\({root_var}\.dataset\.\w+\s*===\s*[\'"][^\'"]*[\'"]\)\s*return;\s*\n?',
        '\n', init_body,
    )
    init_body = re.sub(rf'\s*{root_var}\.dataset\.\w+\s*=\s*[\'"][^\'"]*[\'"];\s*\n?', '\n', init_body)
    # Remover guarda if(!slT || ...) return
    init_body = re.sub(r'\s*if\s*\(![^)]{5,}\)\s*return;\s*\n?', '\n', init_body)

    # Substituir root.querySelector('#id') → document.getElementById('id')
    init_body = re.sub(
        rf"{root_var}\.querySelector\(['\"]#([^'\"]+)['\"]\)",
        r"document.getElementById('\1')",
        init_body,
    )

    # Nome da IIFE a partir do sim_id (ex: sim-ep0401b → initSimEp0401b)
    iife_name = 'init' + re.sub(r'[^a-zA-Z0-9]', '_', sim_id).title().replace('_', '')

    new_script = (
        f'(function {iife_name}() {{\n'
        f'  var container = document.getElementById(\'{sim_id}\');\n'
        f'  if (!container) {{ setTimeout({iife_name}, 100); return; }}\n'
        f'{init_body}\n'
        f'}})();'
    )
    return new_script


def sanitize_scripts(html: str) -> str:
    """Aplica rewrite_sim_script a cada bloco <script>...</script> do fragmento."""
    def repl(m: re.Match) -> str:
        content = m.group(1)
        # Só reescrever scripts que têm o padrão Quarto (tryInit + querySelectorAll)
        if 'querySelectorAll' in content and 'tryInit' in content:
            content = rewrite_sim_script(content)
        return f'<script>\n{content}\n</script>'

    return re.sub(r'<script>([\s\S]*?)</script>', repl, html, flags=re.IGNORECASE)


# ── Localização do ep-container ───────────────────────────────────────────────

def find_container_span(html: str) -> tuple[int, int] | None:
    """Localiza o span [start, end) do <div class="ep-container"> mais externo."""
    start_match = re.search(r'<div class="ep-container">', html)
    if not start_match:
        return None

    depth = 0
    pos = start_match.start()
    tag_re = re.compile(r'<div\b[^>]*>|</div>', re.IGNORECASE)

    while True:
        m = tag_re.search(html, pos)
        if not m:
            return None
        token = m.group(0)
        depth += -1 if token.lower().startswith('</div') else 1
        pos = m.end()
        if depth == 0:
            return start_match.start(), pos

    return None


# ── Pipeline completa ─────────────────────────────────────────────────────────

def moodle_sanitize(fragment: str) -> str:
    """Aplica a pipeline completa de sanitização para Moodle ao fragmento HTML."""
    # 1. Remove células Quarto (%%writefile, TestSuite, outputs com id hex)
    fragment = CELL_RE.sub('', fragment)
    # 2. LaTeX → HTML semântico
    fragment = convert_math_spans(fragment)
    # 3. Estrutura Quarto → HTML inline puro
    fragment = strip_quarto_structure(fragment)
    # 4. Scripts: padrão Quarto → padrão EP03_01
    fragment = sanitize_scripts(fragment)
    return fragment


def process_ep_file(path: Path, outdir: Path) -> bool:
    html = path.read_text(encoding='utf-8', errors='replace')
    span = find_container_span(html)
    if not span:
        print(f"[AVISO] '{path.name}': <div class=\"ep-container\"> não encontrado — pulando.")
        return False

    start, end = span
    fragment = moodle_sanitize(html[start:end])

    # Relatório rápido de problemas remanescentes
    warnings = []
    if 'accent-color' in fragment:
        warnings.append('accent-color')
    if 'querySelector' in fragment:
        warnings.append('querySelector')
    if 'dataset.' in fragment:
        warnings.append('dataset.')
    if r'\(' in fragment:
        warnings.append('LaTeX residual')
    if 'class="anchored"' in fragment:
        warnings.append('class=anchored')
    if 'class="math' in fragment:
        warnings.append('class=math')

    outpath = outdir / path.name
    outpath.write_text(fragment, encoding='utf-8')

    warn_str = '  ⚠ ' + ', '.join(warnings) if warnings else ''
    print(f"[OK] {path.name}: {len(html)} → {len(fragment)} bytes{warn_str}")
    return True


def cmd_limpar(args: argparse.Namespace) -> None:
    indir = Path(args.entrada)
    outdir = Path(args.saida)

    if not indir.is_dir():
        print(f"❌ Pasta de entrada não encontrada: {indir}", file=sys.stderr)
        sys.exit(1)

    outdir.mkdir(parents=True, exist_ok=True)
    print(f"Entrada : {indir}")
    print(f"Saída   : {outdir}\n")

    ok, fail = 0, 0
    for f in sorted(indir.glob("EP*.html")):
        if process_ep_file(f, outdir):
            ok += 1
        else:
            fail += 1

    print(f"\n{'─'*50}")
    print(f"✅ Concluído: {ok} sanitizados, {fail} com problema.")
    if ok:
        print(f"📁 Fragmentos prontos para Moodle em: {outdir}/")


# ══════════════════════════════════════════════════════════════════════════════
# CLI principal
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ep_tools.py",
        description="Ferramentas unificadas para extração de EPs de HTML Quarto.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="cmd", metavar="SUBCOMANDO")
    sub.required = True

    # ── subcomando: extrair ──────────────────────────────────────────────────
    p_ext = sub.add_parser(
        "extrair",
        help="Extrai cada EP de cap*.html e salva em arquivo individual.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_ext.add_argument(
        "--input", "-i",
        default="gen/book",
        metavar="CAMINHO",
        help="Arquivo HTML ou diretório raiz (padrão: gen/book)",
    )
    p_ext.add_argument(
        "--out-dir", "-o",
        default=None,
        metavar="PASTA",
        help="Pasta de saída (padrão: gen/book/eps/<versao>/)",
    )
    p_ext.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Apenas lista EPs encontrados, não grava arquivos",
    )
    p_ext.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suprime saída detalhada",
    )
    p_ext.set_defaults(func=cmd_extrair)

    # ── subcomando: limpar ───────────────────────────────────────────────────
    p_lim = sub.add_parser(
        "limpar",
        help="Extrai fragmento Moodle/VPL de cada EPxx_xx.html já extraído.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_lim.add_argument(
        "entrada",
        metavar="PASTA_ENTRADA",
        help="Pasta com os EPxx_xx.html extraídos (ex: gen/book/eps/py.pt)",
    )
    p_lim.add_argument(
        "saida",
        metavar="PASTA_SAIDA",
        nargs="?",
        default=None,
        help="Pasta de saída (padrão: <PASTA_ENTRADA>_moodle)",
    )
    p_lim.set_defaults(func=cmd_limpar)

    args = parser.parse_args()

    # Valor padrão de saída para 'limpar'
    if args.cmd == "limpar" and args.saida is None:
        args.saida = str(Path(args.entrada).with_name(Path(args.entrada).name + "_moodle"))

    args.func(args)


if __name__ == "__main__":
    main()