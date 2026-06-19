#!/usr/bin/env bash
# Extrai o fragmento utilizável (compatível com Moodle/VPL) de cada EPxx_xx.html
# a partir das páginas completas geradas pelo Quarto.
#
# Uso:
#   ./run_extract.sh /caminho/para/gen/book/eps/py.pt /caminho/para/saida
#
# Se nenhum argumento for passado, assume:
#   entrada = gen/book/eps/py.pt
#   saida   = gen/book/eps/py.pt_moodle

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IN_DIR="${1:-gen/book/eps/py.pt}"
OUT_DIR="${2:-${IN_DIR}_moodle}"

if [ ! -d "$IN_DIR" ]; then
  echo "Pasta de entrada não encontrada: $IN_DIR"
  exit 1
fi

echo "Entrada : $IN_DIR"
echo "Saída   : $OUT_DIR"
echo

python3 "$SCRIPT_DIR/extract_ep.py" "$IN_DIR" "$OUT_DIR"

echo
echo "Pronto. Os arquivos extraídos (prontos para colar no Moodle) estão em: $OUT_DIR"
