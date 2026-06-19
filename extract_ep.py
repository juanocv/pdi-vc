#!/usr/bin/env python3
"""
Extrai o fragmento real de um EP a partir da página Quarto completa.

Regra:
  - Conteúdo útil = tudo dentro de <div class="ep-container"> ... </div>
    (a div raiz do EP), incluindo seu(s) <script> de simulador.
  - Removemos as "cells" de código Python/Jupyter (%%writefile, TestSuite...run())
    que não fazem sentido fora do notebook.
  - Tudo que vem depois desse </div> de fechamento (scripts de nav do Quarto,
    MathJax, scripts órfãos de outros simuladores que não existem nesta página)
    é descartado.
"""
import re
import sys
from pathlib import Path

CELL_RE = re.compile(
    r'<div class="cell"[^>]*id="[0-9a-f]{6,}"[\s\S]*?</div>\s*(?=<div class="cell"|</section>)',
    re.IGNORECASE
)

def find_container_span(html: str):
    start_match = re.search(r'<div class="ep-container">', html)
    if not start_match:
        return None
    start = start_match.start()
    # Faz parsing manual de profundidade de <div ...> / </div> a partir do start
    depth = 0
    i = start
    tag_re = re.compile(r'<div\b[^>]*>|</div>', re.IGNORECASE)
    pos = start
    while True:
        m = tag_re.search(html, pos)
        if not m:
            return None
        token = m.group(0)
        if token.lower().startswith('</div'):
            depth -= 1
        else:
            depth += 1
        pos = m.end()
        if depth == 0:
            return start, pos
    return None

def clean_fragment(fragment: str) -> str:
    # Remove blocos de "cell" do Jupyter/Quarto (%%writefile, TestSuite(...).run(), saídas)
    fragment = CELL_RE.sub('', fragment)
    return fragment

def process_file(path: Path, outdir: Path):
    html = path.read_text(encoding='utf-8', errors='replace')
    span = find_container_span(html)
    if not span:
        print(f"[AVISO] '{path.name}': <div class=\"ep-container\"> não encontrado — pulando.")
        return False
    start, end = span
    fragment = html[start:end]
    fragment = clean_fragment(fragment)
    outpath = outdir / path.name
    outpath.write_text(fragment, encoding='utf-8')
    print(f"[OK] {path.name}: {len(html)} bytes -> {len(fragment)} bytes")
    return True

def main():
    if len(sys.argv) < 3:
        print("Uso: extract_ep.py <pasta_entrada> <pasta_saida>")
        sys.exit(1)
    indir = Path(sys.argv[1])
    outdir = Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    ok, fail = 0, 0
    for f in sorted(indir.glob("EP*.html")):
        if process_file(f, outdir):
            ok += 1
        else:
            fail += 1
    print(f"\nConcluído: {ok} extraídos, {fail} com problema.")

if __name__ == "__main__":
    main()
