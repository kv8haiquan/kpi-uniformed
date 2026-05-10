#!/usr/bin/env python3
"""
One-shot script: thay thế pattern X.toFixed(6).replace(/\\.?0+$/, '') bằng formatScore(X)
trên toàn bộ frontend/src/. Tự động thêm import { formatScore } from '@/lib/format'.
"""
import os
import re
import subprocess
import sys

ROOT = "frontend/src"
SUFFIX = ".toFixed(6).replace(/\\.?0+$/, '')"
NEW_IMPORT = "import { formatScore } from '@/lib/format';"


def find_expr_start(text: str, end_pos: int) -> int:
    """Walk backward from end_pos to find start of the expression preceding `.toFixed(6)`."""
    pos = end_pos - 1
    paren_depth = 0
    bracket_depth = 0
    while pos >= 0:
        ch = text[pos]
        if paren_depth > 0:
            if ch == ')':
                paren_depth += 1
            elif ch == '(':
                paren_depth -= 1
            pos -= 1
            continue
        if bracket_depth > 0:
            if ch == ']':
                bracket_depth += 1
            elif ch == '[':
                bracket_depth -= 1
            pos -= 1
            continue
        if ch == ')':
            paren_depth = 1
            pos -= 1
            continue
        if ch == ']':
            bracket_depth = 1
            pos -= 1
            continue
        if ch.isalnum() or ch in "_$.?":
            pos -= 1
            continue
        break
    return pos + 1


def add_import(text: str) -> str:
    if "from '@/lib/format'" in text or 'from "@/lib/format"' in text:
        return text
    pattern = re.compile(r"^import\s+[^;]+?;\s*$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    if matches:
        insert_pos = matches[-1].end()
        return text[:insert_pos] + "\n" + NEW_IMPORT + text[insert_pos:]
    if text.startswith("'use client';"):
        nl = text.index("\n")
        return text[: nl + 1] + "\n" + NEW_IMPORT + text[nl + 1 :]
    return NEW_IMPORT + "\n" + text


def process_file(path: str) -> int:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    if SUFFIX not in text:
        return 0

    count = 0
    while SUFFIX in text:
        idx = text.index(SUFFIX)
        expr_start = find_expr_start(text, idx)
        expr = text[expr_start:idx]
        if expr.endswith("?"):
            expr = expr[:-1]
        replacement = f"formatScore({expr})"
        text = text[:expr_start] + replacement + text[idx + len(SUFFIX):]
        count += 1

    text = add_import(text)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return count


def main() -> int:
    result = subprocess.run(
        ["grep", "-rl", "--include=*.tsx", "--include=*.ts", "toFixed(6)", ROOT],
        capture_output=True,
        text=True,
        check=True,
    )
    files = [f for f in result.stdout.strip().split("\n") if f]
    total = 0
    for f in files:
        n = process_file(f)
        if n > 0:
            print(f"{f}: {n}")
            total += n
    print(f"--- Total replacements: {total} across {len(files)} files ---")
    return 0


if __name__ == "__main__":
    sys.exit(main())
