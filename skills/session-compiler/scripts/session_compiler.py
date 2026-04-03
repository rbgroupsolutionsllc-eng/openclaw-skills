#!/usr/bin/env python3
"""
session_compiler.py — Compilador de sesiones OpenClaw
Convierte archivos JSONL de sesión en texto legible, buscable y recuperable.

Uso:
  session_compiler <archivo.jsonl ...> [opciones]
  session_compiler --list                    # Lista sesiones disponibles
  session_compiler --current                 # Compila la sesión activa actual
  session_compiler <archivo.jsonl> --grep "patrón"  # Busca en la sesión

Opciones:
  -o <dir>          Directorio de salida (default: junto al JSONL)
  -t <N>            Límite de palabras por bloque en .min.txt (default: 200)
  -tu <N>           Límite para mensajes de usuario (default: 256)
  --grep <patrón>   Búsqueda regex (Python re.search, case-insensitive)
  --thinking        Incluir bloques de pensamiento en .txt
  --list            Lista sesiones disponibles ordenadas por fecha
  --current         Usa la sesión activa actual (main agent)
  --agent <nombre>  Agente a usar con --current/--list (default: main)
"""

import json
import sys
import os
import re
import argparse
from datetime import datetime, timezone
from pathlib import Path

# --- Configuration ---
DEFAULT_TRUNC_WORDS = 200
DEFAULT_TRUNC_USER_WORDS = 256
OPENCLAW_DIR = Path.home() / ".openclaw"
AGENTS_DIR = OPENCLAW_DIR / "agents"


def get_sessions_dir(agent="main"):
    return AGENTS_DIR / agent / "sessions"


def get_current_session_id(agent="main"):
    """Lee sessions.json para obtener el ID de la sesión activa."""
    sessions_json = get_sessions_dir(agent) / "sessions.json"
    if not sessions_json.exists():
        return None
    try:
        with open(sessions_json) as f:
            data = json.load(f)
        key = f"agent:{agent}:main"
        return data.get(key, {}).get("sessionId")
    except Exception:
        return None


# --- Helpers ---

def trunc_words(text, n):
    if not text:
        return ""
    words = text.split()
    if len(words) <= n:
        return text
    return " ".join(words[:n]) + " …"


def strip_telegram_wrapper(text):
    """Remueve el header de metadata de Telegram, devolviendo solo el mensaje real."""
    if text.startswith("Conversation info (untrusted metadata):"):
        idx = text.rfind("\n\n")
        if idx != -1:
            return text[idx + 2:].strip()
    return text


def format_tool_args(arguments):
    """Formatea los argumentos de un tool call en una línea corta."""
    if not arguments:
        return "()"
    priority_keys = ("path", "cmd", "command", "query", "url", "text", "content",
                     "message", "input", "prompt", "file", "name")
    for key in priority_keys:
        if key in arguments:
            val = str(arguments[key])
            val = val.replace("\n", " ").strip()
            if len(val) > 80:
                val = val[:80] + "…"
            return f"({val})"
    k, v = next(iter(arguments.items()))
    val = str(v).replace("\n", " ").strip()[:80]
    return f"({k}={val})"


def format_timestamp(ts_str):
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return ts_str


def ts_ms_to_hhmm(ts_ms):
    if not ts_ms:
        return ""
    try:
        dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
        return f" [{dt.strftime('%H:%M')}]"
    except Exception:
        return ""


def parse_jsonl(path):
    events = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return events


# --- Transcript Building ---

def build_transcript(events, include_thinking=False):
    """Construye el transcript completo (.txt). Sin truncamiento."""
    lines = []
    current_model = None

    for ev in events:
        t = ev.get("type")

        if t == "session":
            ts = format_timestamp(ev.get("timestamp", ""))
            cwd = ev.get("cwd", "")
            sid = ev.get("id", "")
            lines.append(f"{'═' * 60}")
            lines.append(f"SESIÓN: {sid}")
            lines.append(f"Inicio: {ts}")
            if cwd:
                lines.append(f"CWD:    {cwd}")
            lines.append(f"{'═' * 60}")
            lines.append("")

        elif t == "model_change":
            provider = ev.get("provider", "")
            model_id = ev.get("modelId", "?")
            current_model = f"{provider}/{model_id}" if provider else model_id

        elif t == "compaction":
            summary = ev.get("summary", "").strip()
            ts = format_timestamp(ev.get("timestamp", ""))
            lines.append(f"── COMPACTACIÓN [{ts}] ──")
            lines.append(summary)
            lines.append("")

        elif t == "message":
            msg = ev.get("message", {})
            role = msg.get("role")
            content = msg.get("content", [])
            model = msg.get("model")
            ts_tag = ts_ms_to_hhmm(msg.get("timestamp"))

            if role == "user":
                texts = []
                for c in content:
                    if isinstance(c, dict) and c.get("type") == "text":
                        texts.append(strip_telegram_wrapper(c["text"]))
                if texts:
                    lines.append(f"[usuario]{ts_tag}")
                    lines.append("\n".join(texts))
                    lines.append("")

            elif role == "assistant":
                model_tag = ""
                if model and model != current_model:
                    model_tag = f" ({model})"
                parts = []
                for c in content:
                    if not isinstance(c, dict):
                        continue
                    ctype = c.get("type")
                    if ctype == "text" and c.get("text", "").strip():
                        parts.append(c["text"].strip())
                    elif ctype == "thinking" and include_thinking:
                        th = c.get("thinking", "").strip()
                        if th:
                            parts.append(f"<pensamiento>\n{th}\n</pensamiento>")
                    elif ctype == "toolCall":
                        name = c.get("name", "?")
                        args = c.get("arguments", {})
                        parts.append(f"* {name}{format_tool_args(args)}")
                if parts:
                    lines.append(f"[asistente]{model_tag}{ts_tag}")
                    lines.append("\n".join(parts))
                    lines.append("")

            elif role == "toolResult":
                tool_name = msg.get("toolName", "?")
                is_error = msg.get("isError", False)
                tag = "error" if is_error else "resultado"
                result_texts = []
                for c in content:
                    if isinstance(c, dict) and c.get("type") == "text":
                        result_texts.append(c["text"])
                if result_texts:
                    lines.append(f"[{tag}: {tool_name}]")
                    lines.append("\n".join(result_texts))
                    lines.append("")

    return lines


def build_min_transcript(events, trunc=DEFAULT_TRUNC_WORDS, trunc_user=DEFAULT_TRUNC_USER_WORDS):
    """Construye el transcript mínimo (.min.txt). Truncado, sin tool results ni thinking."""
    lines = []

    for ev in events:
        t = ev.get("type")

        if t == "session":
            ts = format_timestamp(ev.get("timestamp", ""))
            sid = ev.get("id", "")[:8]
            cwd = ev.get("cwd", "")
            lines.append(f"═ SESIÓN {sid} — {ts} ═")
            if cwd:
                lines.append(f"CWD: {cwd}")
            lines.append("")

        elif t == "compaction":
            summary = ev.get("summary", "").strip()
            lines.append("[compacción]")
            lines.append(trunc_words(summary, trunc))
            lines.append("")

        elif t == "message":
            msg = ev.get("message", {})
            role = msg.get("role")
            content = msg.get("content", [])

            if role == "user":
                texts = []
                for c in content:
                    if isinstance(c, dict) and c.get("type") == "text":
                        raw = strip_telegram_wrapper(c["text"])
                        texts.append(trunc_words(raw, trunc_user))
                if texts:
                    lines.append("[usuario]")
                    lines.append("\n".join(texts))
                    lines.append("")

            elif role == "assistant":
                parts = []
                for c in content:
                    if not isinstance(c, dict):
                        continue
                    ctype = c.get("type")
                    if ctype == "text" and c.get("text", "").strip():
                        parts.append(trunc_words(c["text"].strip(), trunc))
                    elif ctype == "toolCall":
                        name = c.get("name", "?")
                        args = c.get("arguments", {})
                        parts.append(f"* {name}{format_tool_args(args)}")
                if parts:
                    lines.append("[asistente]")
                    lines.append("\n".join(parts))
                    lines.append("")

            # toolResult: se omite en .min.txt

    return lines


# --- Grep ---

def grep_lines(filename, lines, pattern):
    """Busca patrón en líneas y muestra bloques con rangos de línea."""
    try:
        rx = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        print(f"Error en regex '{pattern}': {e}", file=sys.stderr)
        return 0

    # Identificar bloques separados por líneas vacías
    blocks = []
    start = 0
    for i, line in enumerate(lines):
        if line == "":
            if start < i:
                blocks.append((start, i - 1))
            start = i + 1
    if start < len(lines):
        blocks.append((start, len(lines) - 1))

    hit_count = 0
    for bstart, bend in blocks:
        block_text = "\n".join(lines[bstart:bend + 1])
        if rx.search(block_text):
            hit_count += 1
            print(f"({filename}:L{bstart + 1}-L{bend + 1})")
            for i in range(bstart, min(bend + 1, bstart + 6)):
                line = lines[i]
                m = rx.search(line)
                marker = "►" if m else " "
                print(f"  {marker} {i + 1}: {line[:120]}")
            print()

    return hit_count


# --- Output ---

def write_output(lines, path_base, suffix, output_dir=None):
    base = Path(path_base).stem
    if output_dir:
        out_path = Path(output_dir) / f"{base}{suffix}"
    else:
        out_path = Path(path_base).parent / f"{base}{suffix}"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(lines) + "\n"
    out_path.write_text(content, encoding="utf-8")
    word_count = len(content.split())
    print(f"{out_path}  ({len(lines)} líneas, {word_count} palabras)")
    return out_path


# --- Session Listing ---

def list_sessions(agent="main", extra_dirs=None):
    dirs = [get_sessions_dir(agent)]
    if extra_dirs:
        dirs.extend([Path(d) for d in extra_dirs])

    sessions = []
    for d in dirs:
        if not d.exists():
            continue
        for f in d.glob("*.jsonl"):
            try:
                with open(f, encoding="utf-8", errors="replace") as fp:
                    first_line = fp.readline().strip()
                first = json.loads(first_line) if first_line else {}
                ts = first.get("timestamp", "")[:16].replace("T", " ")
                sid = first.get("id", f.stem)
                size_kb = f.stat().st_size // 1024
                mtime = f.stat().st_mtime
                sessions.append((mtime, ts, sid, size_kb, f))
            except Exception:
                sessions.append((0, "", f.stem, 0, f))

    sessions.sort(reverse=True)
    print(f"{'FECHA':<17}  {'ID':<36}  {'TAMAÑO':>8}  ARCHIVO")
    print("-" * 80)
    for mtime, ts, sid, size_kb, f in sessions:
        print(f"{ts:<17}  {sid:<36}  {size_kb:>6}KB  {f.name}")


# --- Main ---

def main():
    parser = argparse.ArgumentParser(
        description="Compilador de sesiones OpenClaw — convierte JSONL a texto legible y buscable",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("files", nargs="*", help="Archivos JSONL de sesión")
    parser.add_argument("-o", "--output-dir", help="Directorio de salida")
    parser.add_argument("-t", "--trunc", type=int, default=DEFAULT_TRUNC_WORDS,
                        help=f"Palabras máx por bloque en .min.txt (default: {DEFAULT_TRUNC_WORDS})")
    parser.add_argument("-tu", "--trunc-user", type=int, default=DEFAULT_TRUNC_USER_WORDS,
                        help=f"Palabras máx para mensajes usuario (default: {DEFAULT_TRUNC_USER_WORDS})")
    parser.add_argument("--grep", help="Patrón regex para buscar en las sesiones")
    parser.add_argument("--thinking", action="store_true",
                        help="Incluir bloques de pensamiento en .txt")
    parser.add_argument("--list", action="store_true",
                        help="Listar sesiones disponibles")
    parser.add_argument("--current", action="store_true",
                        help="Usar la sesión activa actual")
    parser.add_argument("--agent", default="main",
                        help="Nombre del agente (default: main)")
    args = parser.parse_args()

    # --list
    if args.list:
        list_sessions(agent=args.agent)
        return

    # --current
    if args.current:
        sid = get_current_session_id(args.agent)
        if not sid:
            print(f"No se encontró sesión activa para agente '{args.agent}'", file=sys.stderr)
            sys.exit(1)
        session_file = get_sessions_dir(args.agent) / f"{sid}.jsonl"
        if not session_file.exists():
            print(f"Archivo no encontrado: {session_file}", file=sys.stderr)
            sys.exit(1)
        args.files = [str(session_file)]

    if not args.files:
        parser.print_help()
        return

    # Procesar cada archivo
    for file_path in args.files:
        path = Path(file_path)
        if not path.exists():
            print(f"Archivo no encontrado: {path}", file=sys.stderr)
            continue

        events = parse_jsonl(path)
        if not events:
            print(f"Sin eventos en: {path}", file=sys.stderr)
            continue

        if args.grep:
            full_lines = build_transcript(events, include_thinking=False)
            print(f"\n=== {path.name} ===")
            hits = grep_lines(path.stem, full_lines, args.grep)
            if hits == 0:
                print(f"  (sin resultados para '{args.grep}')")
        else:
            full_lines = build_transcript(events, include_thinking=args.thinking)
            min_lines = build_min_transcript(events, trunc=args.trunc, trunc_user=args.trunc_user)
            write_output(full_lines, path, ".txt", args.output_dir)
            write_output(min_lines, path, ".min.txt", args.output_dir)


if __name__ == "__main__":
    main()
