#!/usr/bin/env python3
"""
extrair_eps.py — Extrai cada EP de cap*.html e salva em arquivo individual.

Uso:
    python extrair_eps.py                              # processa gen/book/*/cap*/*.html
    python extrair_eps.py --input gen/book/py.pt      # versão específica
    python extrair_eps.py --input gen/book/py.pt/cap01/cap01.py.pt.html  # arquivo único
    python extrair_eps.py --out-dir output/eps        # pasta de saída customizada
    python extrair_eps.py --dry-run                   # só lista EPs encontrados

Saída padrão: gen/book/eps/<versao>/EP01_02.html
"""

import argparse
import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup, Tag


# ── Padrões ──────────────────────────────────────────────────────────────────

# Identifica o título de um EP: h2, h3 ou h4 cujo texto contém "EPXX_YY"
RE_EP_HEADING = re.compile(r'\bEP(\d{2})_(\d{2})\b')

# Identifica a célula %%writefile EPXX_YY.py que fecha o bloco do EP
RE_WRITEFILE = re.compile(r'%%writefile\s+(EP\d{2}_\d{2}\.py)')


# ── HTML mínimo para envolver o fragmento extraído ───────────────────────────

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
    styles_parts = []
    scripts_parts = []

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
        # Inclui apenas scripts externos relevantes (MathJax, highlight.js…)
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
    eps = []

    # Trabalhar sobre o conteúdo principal (main, article ou body)
    main = (
        soup.find("main")
        or soup.find("article")
        or soup.find("div", class_=re.compile(r"content|chapter|book"))
        or soup.find("body")
    )
    if not main:
        return []

    all_elements = list(main.descendants)
    # Filtra só filhos diretos de contêineres de bloco (evita iterar dentro de tags)
    # Usaremos uma abordagem baseada em elementos irmãos do primeiro nível significativo
    # navegando pelos parents dos headings.

    ep_headings = []
    for tag in main.find_all(heading_tags):
        text = tag.get_text(" ", strip=True)
        m = RE_EP_HEADING.search(text)
        if m:
            ep_headings.append((tag, m.group(0)))  # (tag, "EP01_02")

    for heading_tag, ep_id in ep_headings:
        title_text = heading_tag.get_text(" ", strip=True)
        # Remove o número de seção do início ("1.16.2 EP01_02 …" → "EP01_02 …")
        title_text = re.sub(r'^\s*[\d.]+\s+', '', title_text)

        heading_level = int(heading_tag.name[1])  # h3 → 3

        # Coleta elementos a partir do heading até o fim do bloco EP
        block_elements = [heading_tag]
        found_writefile = False

        # Navega pelos irmãos seguintes no mesmo nível pai
        sibling = heading_tag.find_next_sibling()
        while sibling:
            if isinstance(sibling, Tag):
                tag_name = sibling.name

                # Parar se encontrar outro heading de nível ≤ ao do EP
                if tag_name in heading_tags:
                    sib_level = int(tag_name[1])
                    if sib_level <= heading_level:
                        break
                    # Heading filho: verificar se é outro EP
                    sib_text = sibling.get_text(" ", strip=True)
                    if RE_EP_HEADING.search(sib_text):
                        break

                # Verificar se contém %%writefile EPXX_YY.py
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
    """Serializa lista de elementos BeautifulSoup para string HTML."""
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
    """
    Processa um arquivo HTML e extrai todos os EPs encontrados.
    Retorna lista de ep_ids extraídos.
    """
    raw = html_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(raw, "html.parser")

    lang = detect_lang(soup)
    styles, scripts = extract_head_assets(soup)
    eps = find_ep_blocks(soup)

    if not eps:
        if verbose:
            print(f"  ⚠️  Nenhum EP encontrado em {html_path.name}")
        return []

    extracted = []
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
    """
    Dado um caminho (arquivo ou diretório), retorna lista de
    (html_file, versao_dir) onde versao_dir é o subdiretório da versão
    (ex: gen/book/py.pt).
    """
    pairs = []

    if input_path.is_file() and input_path.suffix == ".html":
        # Tenta inferir versao_dir subindo na árvore até "book"
        parts = input_path.parts
        try:
            book_idx = list(parts).index("book")
            versao_dir = Path(*parts[: book_idx + 2])  # book/<versao>
        except ValueError:
            versao_dir = input_path.parent
        pairs.append((input_path, versao_dir))

    elif input_path.is_dir():
        # Procura cap*/*.html recursivamente
        for html_file in sorted(input_path.rglob("cap*/*.html")):
            # Inferir versao_dir: parte após "book/"
            parts = html_file.parts
            try:
                book_idx = list(parts).index("book")
                versao_dir = Path(*parts[: book_idx + 2])
            except ValueError:
                versao_dir = input_path
            pairs.append((html_file, versao_dir))

    return pairs


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Extrai EPs de HTML gerados pelo Quarto (PDI+VC)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--input", "-i",
        default="gen/book",
        help="Arquivo HTML ou diretório raiz (padrão: gen/book)",
    )
    parser.add_argument(
        "--out-dir", "-o",
        default=None,
        help="Pasta de saída (padrão: gen/book/eps/<versao>/)",
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Apenas lista EPs encontrados, não grava arquivos",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suprime saída detalhada",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Caminho não encontrado: {input_path}", file=sys.stderr)
        sys.exit(1)

    pairs = collect_html_files(input_path)
    if not pairs:
        print(f"❌ Nenhum arquivo HTML de capítulo encontrado em: {input_path}", file=sys.stderr)
        sys.exit(1)

    verbose = not args.quiet
    total_eps = []

    for html_file, versao_dir in pairs:
        # Determina pasta de saída
        if args.out_dir:
            out_dir = Path(args.out_dir)
        else:
            # gen/book/eps/<versao>/  (ex: gen/book/eps/py.pt/)
            versao_name = versao_dir.name  # "py.pt"
            book_root = versao_dir.parent  # gen/book/
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

    # Resumo
    action = "encontrados" if args.dry_run else "gerados"
    print(f"\n{'─'*50}")
    print(f"✅ {len(total_eps)} EPs {action}: {', '.join(sorted(set(total_eps)))}")

    if not args.dry_run and total_eps and not args.out_dir:
        # Mostra pasta de saída principal
        sample_versao = pairs[0][1].name
        book_root = pairs[0][1].parent
        print(f"📁 Saída: {book_root / 'eps' / sample_versao}/")


if __name__ == "__main__":
    main()
