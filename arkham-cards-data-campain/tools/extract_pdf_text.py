import argparse
import json
import os
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF

"""
Extrai texto de PDFs de guias de campanha do Arkham Horror LCG.

Saidas geradas para cada PDF:
- .raw.txt: texto bruto, com glifos preservados e marcador de pagina.
- .llm.txt: texto limpo para leitura por agentes/LLMs.
- .search.txt: texto normalizado para matching aproximado com msgid/msgstr.
- .map.json: mapa dos glifos/icones encontrados e como foram normalizados.
- .txt: alias de compatibilidade apontando para o conteudo de .llm.txt.

Uso:
  python extract_pdf_text.py caminho\\arquivo.pdf
  python extract_pdf_text.py caminho\\arquivo1.pdf caminho\\arquivo2.pdf
  python extract_pdf_text.py --input-dir guides\\tcu
  python extract_pdf_text.py --input-dir guides --recursive
"""

# Padroes estruturais indesejados. Mantidos conservadores para nao apagar
# texto valido em outras campanhas.
GARBAGE_PATTERNS = [
    r"(?i)^\s*guia de campanha\s*$",
    r"(?i)^\s*campaign guide\s*$",
    r"^\s*\d+\s*$",
]

TOC_HEADERS = {
    "conteúdo",
    "contents",
}

TOC_LINE_RE = re.compile(r"^.+\.{3,}\s*\d+\s*$")
PAGE_MARKER_RE = re.compile(r"^=== PAGE \d+ ===$")

# Glifos que aparecem com frequencia como bullets/ornamentos em PDFs.
BULLET_ICON_CHARS = {
    "•",
    "●",
    "■",
    "□",
    "▪",
    "▫",
    "◦",
    "◻",
    "◼",
}

# Todos os glifos "suspeitos" que merecem tratamento especial.
ICON_CHAR_RE = re.compile(r"[\uf000-\uf8ff\u25A0-\u25FF\u2022Æ•●■□▪▫◦]")

# Mapa conservador: so use aqui substituicoes de alta confianca.
# Exemplo futuro: "Æ": "[action]"
KNOWN_ICON_MAP = {}

# Tags do app que devem ser neutralizadas ao criar a chave de busca.
APP_ICON_TAG_RE = re.compile(r"\[[a-z_]+\]|\[ICONE\]")
UNKNOWN_ICON_RE = re.compile(r"<<ICON_UNKNOWN:[^>]+>>")
TOP_READING_ZONE_RATIO = 0.18
COLUMN_MID_TOLERANCE = 20
WIDE_BLOCK_RATIO = 0.72


def is_garbage_line(line):
    stripped = line.strip()
    if not stripped:
        return False
    return any(re.match(pattern, stripped) for pattern in GARBAGE_PATTERNS)


def replace_known_nbsp(text):
    return text.replace("\xa0", " ").replace("\u202f", " ")


def normalize_block_text(text):
    return replace_known_nbsp(text).strip()


def extract_text_blocks(page):
    blocks = []
    for block in page.get_text("blocks"):
        x0, y0, x1, y1, text, *_ = block
        normalized = normalize_block_text(text)
        if not normalized:
            continue
        blocks.append(
            {
                "x0": x0,
                "y0": y0,
                "x1": x1,
                "y1": y1,
                "width": x1 - x0,
                "height": y1 - y0,
                "text": normalized,
            }
        )
    return blocks


def sort_blocks_top_to_bottom(blocks):
    return sorted(blocks, key=lambda block: (round(block["y0"], 1), round(block["x0"], 1)))


def is_centered_header_block(block, page_width, page_height):
    page_center = page_width / 2
    return (
        block["y0"] <= page_height * TOP_READING_ZONE_RATIO
        and block["x0"] < page_center
        and block["x1"] > page_center
    )


def is_two_column_page(blocks, page_width, page_height):
    mid_x = page_width / 2
    top_boundary = page_height * TOP_READING_ZONE_RATIO
    left_candidates = 0
    right_candidates = 0

    for block in blocks:
        if block["y0"] <= top_boundary:
            continue
        if block["width"] >= page_width * WIDE_BLOCK_RATIO:
            continue
        if block["x1"] <= mid_x - COLUMN_MID_TOLERANCE:
            left_candidates += 1
        elif block["x0"] >= mid_x + COLUMN_MID_TOLERANCE:
            right_candidates += 1

    return left_candidates >= 2 and right_candidates >= 2


def extract_page_text(page):
    page_width = page.rect.width
    page_height = page.rect.height
    blocks = extract_text_blocks(page)
    if not blocks:
        return ""

    if not is_two_column_page(blocks, page_width, page_height):
        return "\n\n".join(block["text"] for block in sort_blocks_top_to_bottom(blocks))

    mid_x = page_width / 2
    header_blocks = []
    left_blocks = []
    right_blocks = []
    spanning_blocks = []

    for block in blocks:
        if is_centered_header_block(block, page_width, page_height):
            header_blocks.append(block)
            continue

        if block["width"] >= page_width * WIDE_BLOCK_RATIO or (
            block["x0"] < mid_x - COLUMN_MID_TOLERANCE
            and block["x1"] > mid_x + COLUMN_MID_TOLERANCE
        ):
            spanning_blocks.append(block)
            continue

        if block["x1"] <= mid_x - COLUMN_MID_TOLERANCE:
            left_blocks.append(block)
        elif block["x0"] >= mid_x + COLUMN_MID_TOLERANCE:
            right_blocks.append(block)
        elif block["x0"] < mid_x:
            left_blocks.append(block)
        else:
            right_blocks.append(block)

    ordered_blocks = (
        sort_blocks_top_to_bottom(header_blocks)
        + sort_blocks_top_to_bottom(spanning_blocks)
        + sort_blocks_top_to_bottom(left_blocks)
        + sort_blocks_top_to_bottom(right_blocks)
    )
    return "\n\n".join(block["text"] for block in ordered_blocks)


def build_raw_output(page_texts):
    chunks = []
    for index, text in enumerate(page_texts, start=1):
        chunks.append(f"=== PAGE {index} ===\n{text.strip()}")
    return "\n\n".join(chunks).strip() + "\n"


def strip_garbage_lines(text):
    lines = []
    for line in text.splitlines():
        if is_garbage_line(line):
            continue
        lines.append(line.rstrip())
    return "\n".join(lines)


def strip_table_of_contents(text):
    output = []

    for line in text.splitlines():
        stripped = line.strip()
        lowered = stripped.lower()

        if lowered in TOC_HEADERS:
            continue

        if TOC_LINE_RE.match(stripped):
            continue

        output.append(line)

    return "\n".join(output)


def merge_soft_wrapped_lines(text):
    blocks = []
    current = []

    def flush_current():
        if not current:
            return

        normalized_lines = [line.strip() for line in current if line.strip()]
        current.clear()
        if not normalized_lines:
            return

        if any(PAGE_MARKER_RE.match(line) for line in normalized_lines):
            blocks.extend(normalized_lines)
            return

        # Mantem listas de sumario como linhas individuais caso escapem do filtro.
        if all(TOC_LINE_RE.match(line) for line in normalized_lines):
            blocks.append("\n".join(normalized_lines))
            return

        blocks.append(" ".join(normalized_lines))

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            flush_current()
            continue
        if PAGE_MARKER_RE.match(stripped):
            flush_current()
            blocks.append(stripped)
            continue
        current.append(line)

    flush_current()
    return "\n\n".join(blocks)


def icon_placeholder(char):
    codepoint = f"U+{ord(char):04X}"
    return f"<<ICON_UNKNOWN:{codepoint}:{char}>>"


def normalize_icons(text):
    icon_stats = {}

    def register_icon(char, replacement, status):
        codepoint = f"U+{ord(char):04X}"
        bucket = icon_stats.setdefault(
            char,
            {
                "glyph": char,
                "unicode": codepoint,
                "replacement": replacement,
                "status": status,
                "count": 0,
            },
        )
        bucket["count"] += 1

    normalized_lines = []
    for line in text.splitlines():
        line_out = []
        for index, char in enumerate(line):
            if not ICON_CHAR_RE.match(char):
                line_out.append(char)
                continue

            if char in KNOWN_ICON_MAP:
                replacement = KNOWN_ICON_MAP[char]
                register_icon(char, replacement, "known")
                line_out.append(replacement)
                continue

            if char in BULLET_ICON_CHARS and not "".join(line_out).strip():
                replacement = "[ICONE]"
                register_icon(char, replacement, "bullet")
                line_out.append(replacement)
                continue

            replacement = icon_placeholder(char)
            register_icon(char, replacement, "unknown")
            line_out.append(replacement)

        normalized_lines.append("".join(line_out))

    return "\n".join(normalized_lines), list(icon_stats.values())


def clean_text_for_llm(raw_text):
    text = replace_known_nbsp(raw_text)
    text = strip_garbage_lines(text)
    text = strip_table_of_contents(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = merge_soft_wrapped_lines(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    normalized_text, icon_stats = normalize_icons(text)
    return normalized_text.strip() + "\n", icon_stats


def make_search_key(text):
    normalized = UNKNOWN_ICON_RE.sub("{ICON}", text)
    normalized = APP_ICON_TAG_RE.sub("{ICON}", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def resolve_output_dir(source):
    configured = os.environ.get("ARKHAM_PDF_OUTPUT_DIR")
    if configured:
        return Path(configured)
    return source.parent


def build_output_paths(pdf_path):
    source = Path(pdf_path)
    output_dir = resolve_output_dir(source)
    stem = source.with_suffix("")
    base_name = stem.name
    return {
        "raw": output_dir / f"{base_name}.raw.txt",
        "llm": output_dir / f"{base_name}.llm.txt",
        "search": output_dir / f"{base_name}.search.txt",
        "map": output_dir / f"{base_name}.map.json",
        "legacy": output_dir / f"{base_name}.txt",
    }


def write_outputs(pdf_path, raw_text, llm_text, icon_stats):
    source = Path(pdf_path)
    output_paths = build_output_paths(source)
    search_key = make_search_key(llm_text)

    try:
        output_paths["raw"].write_text(raw_text, encoding="utf-8")
        output_paths["llm"].write_text(llm_text, encoding="utf-8")
        output_paths["search"].write_text(search_key + "\n", encoding="utf-8")
        output_paths["legacy"].write_text(llm_text, encoding="utf-8")
    except PermissionError:
        fallback_dir = Path.cwd()
        if fallback_dir.resolve() == output_paths["raw"].parent.resolve():
            raise
        print(
            f"Aviso: sem permissão para gravar em '{output_paths['raw'].parent}'. "
            f"Usando '{fallback_dir}' como diretório de saída."
        )
        output_paths = {
            name: fallback_dir / path.name
            for name, path in output_paths.items()
        }
        output_paths["raw"].write_text(raw_text, encoding="utf-8")
        output_paths["llm"].write_text(llm_text, encoding="utf-8")
        output_paths["search"].write_text(search_key + "\n", encoding="utf-8")
        output_paths["legacy"].write_text(llm_text, encoding="utf-8")

    metadata = {
        "source_pdf": str(source.resolve()),
        "outputs": {name: str(path.resolve()) for name, path in output_paths.items()},
        "icon_map_mode": "conservative",
        "known_icon_map": KNOWN_ICON_MAP,
        "icons": icon_stats,
        "search_key_preview": search_key[:500],
    }
    output_paths["map"].write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    return output_paths


def extract_text_from_pdf(pdf_path):
    source = Path(pdf_path)
    if not source.exists():
        print(f"Erro: Arquivo '{pdf_path}' não encontrado.")
        return False

    print(f"Lendo PDF: {source}...")

    try:
        with fitz.open(source) as doc:
            page_texts = [extract_page_text(page) for page in doc]
        raw_text = build_raw_output(page_texts)
        llm_text, icon_stats = clean_text_for_llm("\n\n".join(page_texts))
        outputs = write_outputs(source, raw_text, llm_text, icon_stats)

        print(f"Sucesso! Arquivos gerados:")
        for name in ("raw", "llm", "search", "map", "legacy"):
            print(f"  - {name}: {outputs[name]}")
        return True
    except Exception as error:
        print(f"Erro ao processar o PDF: {error}")
        return False


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extrai arquivos auxiliares (.raw/.llm/.search/.map/.txt) de PDFs de guias."
    )
    parser.add_argument(
        "pdf_files",
        nargs="*",
        help="Lista de PDFs a processar. Se omitido, usa --input-dir.",
    )
    parser.add_argument(
        "--input-dir",
        default=None,
        help="Pasta para buscar PDFs quando nenhum arquivo for informado.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Busca recursiva por PDFs dentro de --input-dir.",
    )
    return parser.parse_args()


def collect_pdfs(args):
    auto_recursive = False
    if args.pdf_files:
        return [Path(path) for path in args.pdf_files]

    if args.input_dir:
        base_dir = Path(args.input_dir)
    else:
        default_candidates = [
            Path("guides"),
            Path("arkham-cards-data-campain/guides"),
        ]
        base_dir = next(
            (candidate for candidate in default_candidates if candidate.exists()),
            Path("."),
        )
        auto_recursive = base_dir.name == "guides"

    pattern = "**/*.pdf" if (args.recursive or auto_recursive) else "*.pdf"
    return sorted(base_dir.glob(pattern))


if __name__ == "__main__":
    args = parse_args()
    pdfs = collect_pdfs(args)
    if not pdfs:
        print("Nenhum PDF encontrado. Informe arquivos ou use --input-dir.")
        sys.exit(1)

    failures = 0
    for pdf in pdfs:
        if not extract_text_from_pdf(pdf):
            failures += 1

    if failures:
        print(f"Concluído com {failures} falha(s).")
        sys.exit(1)

    print(f"Concluído com sucesso. PDFs processados: {len(pdfs)}")
