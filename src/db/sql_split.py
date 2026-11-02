"""
Splits a .sql file into statements the way the mariadb command-line client
does: understands DELIMITER lines, skips -- and /* */ comments, and never
splits inside a quoted string. Used by the View Queries screen to read
db/queries/required_queries.sql.
"""


def split_statements(sql_text: str):
    """Split a .sql file into statements the way the mariadb client does.

    Handles `DELIMITER $$` lines (needed for procedures and triggers, whose
    bodies contain semicolons), skips -- and /* */ comments, and never
    splits inside a quoted string.
    """
    statements = []
    delimiter = ";"
    buf = []
    i, n = 0, len(sql_text)
    at_line_start = True

    while i < n:
        # A DELIMITER command occupies a whole line.
        if at_line_start:
            line_end = sql_text.find("\n", i)
            line_end = n if line_end == -1 else line_end
            line = sql_text[i:line_end].strip()
            if line.upper().startswith("DELIMITER "):
                if "".join(buf).strip():
                    statements.append("".join(buf).strip())
                buf = []
                delimiter = line.split(None, 1)[1].strip()
                i = line_end + 1
                continue

        ch = sql_text[i]
        at_line_start = ch == "\n"

        if ch in ("'", '"', "`"):  # copy a quoted string/identifier untouched
            quote = ch
            j = i + 1
            while j < n:
                if sql_text[j] == "\\" and quote != "`":
                    j += 2
                    continue
                if sql_text[j] == quote:
                    if j + 1 < n and sql_text[j + 1] == quote:  # doubled quote = escaped
                        j += 2
                        continue
                    break
                j += 1
            buf.append(sql_text[i:j + 1])
            i = j + 1
            continue

        if sql_text.startswith("--", i):  # comment to end of line
            line_end = sql_text.find("\n", i)
            i = n if line_end == -1 else line_end
            continue
        if sql_text.startswith("/*", i):
            end = sql_text.find("*/", i + 2)
            i = n if end == -1 else end + 2
            continue

        if sql_text.startswith(delimiter, i):
            stmt = "".join(buf).strip()
            if stmt:
                statements.append(stmt)
            buf = []
            i += len(delimiter)
            continue

        buf.append(ch)
        i += 1

    if "".join(buf).strip():
        statements.append("".join(buf).strip())
    return statements
