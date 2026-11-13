# The six required queries for the View Queries screen.

# They are read from db/queries/required_queries.sql every time
# the server starts, so you can edit that file to change them

import os
import re

from src.db.helpers import fetch_all
from src.db.sql_split import split_statements

QUERIES_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "db", "queries", "required_queries.sql"
)

_HEADER = re.compile(r"^--\s*(\d+)\.\s*(.*)$")
_SET = re.compile(r"^SET\s+@(\w+)\s*=\s*(.+)$", re.IGNORECASE | re.DOTALL)


def _split(sql_text):
    return split_statements(sql_text)


def _parse_value(text):
    text = text.strip()
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    if re.fullmatch(r"-?\d+\.\d+", text):
        return float(text)
    if text[:1] in ("'", '"') and text[-1:] == text[:1]:
        return text[1:-1]
    return text


def load_queries(path=QUERIES_FILE):
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    blocks, current = [], None
    for line in lines:
        m = _HEADER.match(line)
        if m:
            current = {
                "number": int(m.group(1)),
                "title_lines": [m.group(2).strip()],
                "body": [],
                "in_header": True,
            }
            blocks.append(current)
            continue
        if current is None:
            continue
        if current["in_header"] and line.startswith("--"):
            current["title_lines"].append(line.lstrip("-").strip())
            continue
        current["in_header"] = False
        current["body"].append(line)

    queries = []
    for b in blocks:
        title_parts, param_help = [], ""
        for t in b["title_lines"]:
            if t.lower().startswith("parameter:"):
                param_help = t.split(":", 1)[1].strip()
            elif t:
                title_parts.append(t)
        params, sql = {}, None
        for stmt in _split("\n".join(b["body"])):
            m = _SET.match(stmt)
            if m:
                params[m.group(1)] = _parse_value(m.group(2))
            else:
                sql = stmt
        if sql is None:
            continue
        for name in re.findall(r"@(\w+)", sql):
            params.setdefault(name, None)
        queries.append(
            {
                "number": b["number"],
                "title": " ".join(title_parts),
                "param_help": param_help,
                "params": params,
                "sql": re.sub(r"@(\w+)", r"%(\1)s", sql),
            }
        )
    return queries


def run_query(query, values=None):
    if query["params"]:
        merged = dict(query["params"])
        merged.update(values or {})
        return fetch_all(query["sql"], merged)
    return fetch_all(query["sql"])
