import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


PO_LINE_RE = re.compile(r'^(msgid|msgstr)\s+"(.*)"\s*$')
PO_CONT_RE = re.compile(r'^"(.*)"\s*$')

APP_TAG_RE = re.compile(r"\[[a-z_]+\]")
TRAIT_RE = re.compile(r"\[\[[^\]]+\]\]")
HTML_TAG_RE = re.compile(r"</?[a-zA-Z][^>]*>")
HASH_PLACEHOLDER_RE = re.compile(r"#[A-Za-z0-9_]+#")


@dataclass
class Entry:
    msgid: str
    msgstr: str
    msgid_multiline: bool
    msgstr_multiline: bool
    msgid_line: int
    msgstr_line: int


def decode_po(path: Path):
    payload = path.read_bytes()
    has_bom = payload.startswith(b"\xef\xbb\xbf")
    payload.decode("utf-8")
    return has_bom


def parse_po(path: Path):
    entries = []
    current = None
    state = None
    lines = path.read_text(encoding="utf-8").splitlines()

    for line_no, line in enumerate(lines, start=1):
        if line.startswith("#"):
            continue

        match = PO_LINE_RE.match(line)
        if match:
            key, content = match.group(1), match.group(2)
            if key == "msgid":
                if current and "msgstr" in current:
                    entries.append(
                        Entry(
                            msgid=current["msgid"],
                            msgstr=current["msgstr"],
                            msgid_multiline=current["msgid_multiline"],
                            msgstr_multiline=current["msgstr_multiline"],
                            msgid_line=current["msgid_line"],
                            msgstr_line=current["msgstr_line"],
                        )
                    )
                current = {
                    "msgid": content,
                    "msgstr": "",
                    "msgid_multiline": content == "",
                    "msgstr_multiline": False,
                    "msgid_line": line_no,
                    "msgstr_line": -1,
                }
                state = "msgid"
            else:
                if current is None:
                    continue
                current["msgstr"] = content
                current["msgstr_multiline"] = content == ""
                current["msgstr_line"] = line_no
                state = "msgstr"
            continue

        cont = PO_CONT_RE.match(line)
        if cont and current is not None:
            if state == "msgid":
                current["msgid"] += cont.group(1)
                current["msgid_multiline"] = True
            elif state == "msgstr":
                current["msgstr"] += cont.group(1)
                current["msgstr_multiline"] = True
            continue

        if not line.strip():
            state = None

    if current and "msgstr" in current:
        entries.append(
            Entry(
                msgid=current["msgid"],
                msgstr=current["msgstr"],
                msgid_multiline=current["msgid_multiline"],
                msgstr_multiline=current["msgstr_multiline"],
                msgid_line=current["msgid_line"],
                msgstr_line=current["msgstr_line"],
            )
        )

    return entries


def collect_tokens(text: str):
    tokens = set()
    tokens.update(APP_TAG_RE.findall(text))
    tokens.update(TRAIT_RE.findall(text))
    tokens.update(HTML_TAG_RE.findall(text))
    tokens.update(HASH_PLACEHOLDER_RE.findall(text))
    return tokens


def validate_entry(entry: Entry, check_multiline: bool):
    errors = []
    warnings = []

    if entry.msgid == "":
        return errors, warnings

    source_tokens = collect_tokens(entry.msgid)
    target_tokens = collect_tokens(entry.msgstr)
    missing = sorted(source_tokens - target_tokens)
    if missing:
        errors.append(
            f"line {entry.msgstr_line}: missing preserved tokens in msgstr: {', '.join(missing)}"
        )

    if check_multiline and (not entry.msgid_multiline and entry.msgstr_multiline):
        errors.append(
            f"line {entry.msgstr_line}: msgstr is multiline but msgid is single-line"
        )

    if check_multiline and (entry.msgid_multiline and not entry.msgstr_multiline):
        warnings.append(
            f"line {entry.msgstr_line}: msgid is multiline but msgstr is single-line"
        )

    if entry.msgstr == "":
        warnings.append(f"line {entry.msgstr_line}: empty msgstr")

    return errors, warnings


def gather_po_files(paths, recursive):
    result = []
    for raw in paths:
        target = Path(raw)
        if target.is_file() and target.suffix == ".po":
            result.append(target)
        elif target.is_dir():
            pattern = "**/*.po" if recursive else "*.po"
            result.extend(sorted(target.glob(pattern)))
    return sorted(set(result))


def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate .po files for encoding, placeholders/tags, and msgid/msgstr shape."
    )
    parser.add_argument(
        "targets",
        nargs="+",
        help="One or more .po files or directories.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="When target is a directory, include subdirectories.",
    )
    parser.add_argument(
        "--no-multiline-check",
        action="store_true",
        help="Disable msgid/msgstr multiline shape checks.",
    )
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="Return non-zero on warnings too.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    po_files = gather_po_files(args.targets, recursive=args.recursive)
    if not po_files:
        print("No .po files found.")
        return 1

    total_errors = 0
    total_warnings = 0
    checked = 0

    for po_file in po_files:
        file_errors = []
        file_warnings = []
        checked += 1

        try:
            has_bom = decode_po(po_file)
            if has_bom:
                file_errors.append("file has UTF-8 BOM")
            entries = parse_po(po_file)
            for entry in entries:
                errors, warnings = validate_entry(
                    entry, check_multiline=not args.no_multiline_check
                )
                file_errors.extend(errors)
                file_warnings.extend(warnings)
        except UnicodeDecodeError:
            file_errors.append("file is not valid UTF-8")
        except Exception as error:
            file_errors.append(f"unexpected parser error: {error}")

        if file_errors or file_warnings:
            print(f"[FILE] {po_file}")
            for err in file_errors:
                print(f"  [ERROR] {err}")
            for warn in file_warnings:
                print(f"  [WARN] {warn}")

        total_errors += len(file_errors)
        total_warnings += len(file_warnings)

    print(
        f"Checked {checked} file(s). Errors: {total_errors}. Warnings: {total_warnings}."
    )

    if total_errors > 0:
        return 1
    if args.fail_on_warning and total_warnings > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
