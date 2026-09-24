#!/usr/bin/env python3
"""
Reverse-engineers Python source into a Markdown outline: every function,
its loops/conditions, plain-English pseudocode, a Mermaid flowchart, and a
list of detected input/output files and fields (CSV/Excel/JSON I/O,
open(), Streamlit widgets, DataFrame column access).

Usage:
    python reverse_engineer.py <file_or_directory> [-o output.md] [--no-mermaid]
"""
import argparse
import ast
import itertools
import os
import sys

# --- Known I/O call patterns -------------------------------------------------

PANDAS_READERS = {"read_csv", "read_excel", "read_json", "read_sql", "read_parquet",
                   "read_html", "read_pickle", "read_feather", "read_xml"}
PANDAS_WRITERS = {"to_csv", "to_excel", "to_json", "to_sql", "to_parquet",
                   "to_pickle", "to_feather", "to_xml"}

ST_INPUT_WIDGETS = {"number_input", "text_input", "text_area", "selectbox",
                     "multiselect", "slider", "checkbox", "radio", "date_input",
                     "time_input", "file_uploader", "data_editor", "color_picker",
                     "select_slider", "camera_input", "audio_input"}
ST_OUTPUT_WIDGETS = {"write", "metric", "dataframe", "table", "plotly_chart",
                      "line_chart", "bar_chart", "area_chart", "pyplot", "json",
                      "code", "markdown", "info", "warning", "error", "success",
                      "caption", "subheader", "title", "header", "image", "map"}


AUGASSIGN_OPS = {
    ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/", ast.FloorDiv: "//",
    ast.Mod: "%", ast.Pow: "**", ast.LShift: "<<", ast.RShift: ">>",
    ast.BitOr: "|", ast.BitXor: "^", ast.BitAnd: "&", ast.MatMult: "@",
}


def short(node, limit=60):
    """ast.unparse a node and truncate it for display."""
    try:
        text = ast.unparse(node)
    except Exception:
        text = "<expr>"
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


# --- Pseudocode rendering -----------------------------------------------------

def render_block(stmts, indent=0):
    lines = []
    pad = "    " * indent
    i = 0
    while i < len(stmts):
        stmt = stmts[i]
        lines.extend(render_stmt(stmt, indent))
        i += 1
    return lines


def render_stmt(stmt, indent):
    pad = "    " * indent
    lines = []
    if isinstance(stmt, ast.If):
        lines.append(f"{pad}IF {short(stmt.test)}:")
        lines.extend(render_block(stmt.body, indent + 1))
        orelse = stmt.orelse
        while orelse and len(orelse) == 1 and isinstance(orelse[0], ast.If):
            elif_stmt = orelse[0]
            lines.append(f"{pad}ELIF {short(elif_stmt.test)}:")
            lines.extend(render_block(elif_stmt.body, indent + 1))
            orelse = elif_stmt.orelse
        if orelse:
            lines.append(f"{pad}ELSE:")
            lines.extend(render_block(orelse, indent + 1))
    elif isinstance(stmt, ast.For):
        lines.append(f"{pad}FOR {short(stmt.target)} IN {short(stmt.iter)}:")
        lines.extend(render_block(stmt.body, indent + 1))
        if stmt.orelse:
            lines.append(f"{pad}ELSE (loop finished without break):")
            lines.extend(render_block(stmt.orelse, indent + 1))
    elif isinstance(stmt, ast.While):
        lines.append(f"{pad}WHILE {short(stmt.test)}:")
        lines.extend(render_block(stmt.body, indent + 1))
    elif isinstance(stmt, (ast.Try, getattr(ast, "TryStar", ast.Try))):
        lines.append(f"{pad}TRY:")
        lines.extend(render_block(stmt.body, indent + 1))
        for handler in stmt.handlers:
            etype = short(handler.type) if handler.type else "Exception"
            lines.append(f"{pad}EXCEPT {etype}:")
            lines.extend(render_block(handler.body, indent + 1))
        if stmt.orelse:
            lines.append(f"{pad}ELSE:")
            lines.extend(render_block(stmt.orelse, indent + 1))
        if stmt.finalbody:
            lines.append(f"{pad}FINALLY:")
            lines.extend(render_block(stmt.finalbody, indent + 1))
    elif isinstance(stmt, (ast.With, ast.AsyncWith)):
        items = ", ".join(short(i.context_expr) for i in stmt.items)
        lines.append(f"{pad}WITH {items}:")
        lines.extend(render_block(stmt.body, indent + 1))
    elif isinstance(stmt, ast.Return):
        val = f" {short(stmt.value)}" if stmt.value is not None else ""
        lines.append(f"{pad}RETURN{val}")
    elif isinstance(stmt, (ast.Break,)):
        lines.append(f"{pad}BREAK")
    elif isinstance(stmt, (ast.Continue,)):
        lines.append(f"{pad}CONTINUE")
    elif isinstance(stmt, ast.Pass):
        lines.append(f"{pad}PASS")
    elif isinstance(stmt, ast.Raise):
        exc = f" {short(stmt.exc)}" if stmt.exc else ""
        lines.append(f"{pad}RAISE{exc}")
    elif isinstance(stmt, ast.Assert):
        lines.append(f"{pad}ASSERT {short(stmt.test)}")
    elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
        lines.append(f"{pad}DEFINE {stmt.name}(...)  [see separate function entry]")
    elif isinstance(stmt, ast.ClassDef):
        lines.append(f"{pad}DEFINE CLASS {stmt.name}  [see separate section]")
    elif isinstance(stmt, (ast.Import, ast.ImportFrom)):
        pass  # omitted from pseudocode; not control-flow relevant
    elif isinstance(stmt, ast.Assign):
        targets = ", ".join(short(t) for t in stmt.targets)
        lines.append(f"{pad}{targets} = {short(stmt.value)}")
    elif isinstance(stmt, ast.AugAssign):
        op = AUGASSIGN_OPS.get(type(stmt.op), "?")
        lines.append(f"{pad}{short(stmt.target)} {op}= {short(stmt.value)}")
    elif isinstance(stmt, ast.AnnAssign):
        val = f" = {short(stmt.value)}" if stmt.value is not None else ""
        lines.append(f"{pad}{short(stmt.target)}{val}")
    elif isinstance(stmt, ast.Expr):
        lines.append(f"{pad}{short(stmt.value)}")
    else:
        lines.append(f"{pad}{short(stmt) if hasattr(stmt, 'lineno') else stmt.__class__.__name__}")
    return lines


# --- Loop / condition collection ---------------------------------------------

def collect_loops_and_conditions(node):
    loops, conditions = [], []
    for child in ast.walk(node):
        if child is node:
            continue
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue  # nested functions get their own entry
        if isinstance(child, ast.For):
            loops.append((child.lineno, f"for {short(child.target)} in {short(child.iter)}"))
        elif isinstance(child, ast.While):
            loops.append((child.lineno, f"while {short(child.test)}"))
        elif isinstance(child, ast.If):
            conditions.append((child.lineno, f"if {short(child.test)}"))
    return loops, conditions


# --- I/O + field detection ----------------------------------------------------

class IOItem:
    def __init__(self, direction, kind, detail, lineno):
        self.direction = direction  # "input" or "output"
        self.kind = kind
        self.detail = detail
        self.lineno = lineno


def call_root_name(func):
    """For a Call.func Attribute chain, return the leftmost Name id, if any."""
    node = func
    while isinstance(node, ast.Attribute):
        node = node.value
    if isinstance(node, ast.Name):
        return node.id
    return None


def detect_io(tree, module_alias_map):
    items = []
    fields = {}  # (varname, fieldname) -> lineno (first seen)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            attr = node.func.attr
            root = call_root_name(node.func)
            args_text = ", ".join(short(a, 40) for a in node.args[:2])

            if attr in PANDAS_READERS:
                items.append(IOItem("input", "pandas read", f"{attr}({args_text})", node.lineno))
            elif attr in PANDAS_WRITERS:
                items.append(IOItem("output", "pandas write", f"{attr}({args_text})", node.lineno))
            elif root == "st" and attr in ST_INPUT_WIDGETS:
                items.append(IOItem("input", "streamlit widget", f"{attr}({args_text})", node.lineno))
            elif root == "st" and attr in ST_OUTPUT_WIDGETS:
                items.append(IOItem("output", "streamlit widget", f"{attr}({args_text})", node.lineno))

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open":
            args_text = ", ".join(short(a, 40) for a in node.args)
            mode = ""
            for kw in node.keywords:
                if kw.arg == "mode":
                    mode = short(kw.value)
            for i, a in enumerate(node.args):
                if i == 1:
                    mode = short(a)
            direction = "output" if any(m in mode for m in ("w", "a", "x")) else "input"
            items.append(IOItem(direction, "file open", f"open({args_text})", node.lineno))

        # DataFrame / dict-like field access: subscript with a string literal key
        if isinstance(node, ast.Subscript):
            key = node.slice
            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                varname = short(node.value, 30)
                fields.setdefault((varname, key.value), node.lineno)

    return items, fields


# --- Function-level report -----------------------------------------------------

def build_function_entry(node, filename, class_name=None):
    qualname = f"{class_name}.{node.name}" if class_name else node.name
    args = [a.arg for a in node.args.args]
    signature = f"{qualname}({', '.join(args)})"
    doc = ast.get_docstring(node)
    loops, conditions = collect_loops_and_conditions(node)
    pseudocode = render_block(node.body)
    io_items, fields = detect_io(node, {})

    out = []
    out.append(f"### `{signature}`")
    out.append(f"- **Location:** `{filename}:{node.lineno}`")
    out.append(f"- **Docstring:** {doc.splitlines()[0] if doc else '_none_'}")
    out.append(f"- **Loops:** {len(loops)}")
    for ln, text in loops:
        out.append(f"  - line {ln}: `{text}`")
    out.append(f"- **Conditions:** {len(conditions)}")
    for ln, text in conditions:
        out.append(f"  - line {ln}: `{text}`")
    if fields:
        out.append(f"- **Fields accessed:**")
        for (var, key), ln in sorted(fields.items()):
            out.append(f"  - `{var}['{key}']` (line {ln})")
    out.append("")
    out.append("**Pseudocode:**")
    out.append("```")
    out.append(f"FUNCTION {signature}:")
    out.extend(pseudocode if pseudocode else ["    PASS"])
    out.append("```")
    out.append("")
    return out, io_items, fields


# --- Mermaid flowchart ---------------------------------------------------------

class FlowBuilder:
    def __init__(self, func_name):
        self.func_name = func_name
        self.counter = itertools.count()
        self.lines = ["flowchart TD"]
        self.edges = []

    def new_id(self):
        return f"n{next(self.counter)}"

    def node(self, shape_open, shape_close, label):
        nid = self.new_id()
        safe = label.replace('"', "'")
        self.lines.append(f'    {nid}{shape_open}"{safe}"{shape_close}')
        return nid

    def edge(self, a, b, label=None):
        if label:
            self.edges.append(f'    {a} -->|{label}| {b}')
        else:
            self.edges.append(f'    {a} --> {b}')

    def process_block(self, stmts, entry_ids):
        """Returns list of node ids that flow OUT of this block (empty if it always returns)."""
        current = entry_ids
        for stmt in stmts:
            current = self.process_stmt(stmt, current)
            if not current:
                break  # dead end (return/raise) — rest of block is unreachable
        return current

    def process_stmt(self, stmt, entry_ids):
        if isinstance(stmt, ast.If):
            cond_id = self.node("{", "}", f"if {short(stmt.test)}?")
            for e in entry_ids:
                self.edge(e, cond_id)
            true_out = self.process_block(stmt.body, [cond_id])
            if true_out:
                for e in entry_ids[:0]:
                    pass
            # relabel first edge into cond as plain; label branches instead
            # (simplify: label the edges leaving cond_id)
            self._label_last_edges_from(cond_id, "yes", len(stmt.body))
            if stmt.orelse:
                false_out = self.process_block(stmt.orelse, [cond_id])
                self._label_last_edges_from(cond_id, "no", len(stmt.orelse))
                return true_out + false_out
            else:
                return true_out + [cond_id]  # "no" branch skips straight past
        elif isinstance(stmt, (ast.For, ast.While)):
            label = (f"for {short(stmt.target)} in {short(stmt.iter)}"
                     if isinstance(stmt, ast.For) else f"while {short(stmt.test)}")
            loop_id = self.node("{{", "}}", label)
            for e in entry_ids:
                self.edge(e, loop_id)
            body_out = self.process_block(stmt.body, [loop_id])
            for e in body_out:
                self.edge(e, loop_id, "loop")
            return [loop_id]  # exit edge drawn when next statement connects
        elif isinstance(stmt, ast.Return):
            val = short(stmt.value) if stmt.value is not None else ""
            rid = self.node("([", "])", f"return {val}".strip())
            for e in entry_ids:
                self.edge(e, rid)
            return []
        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                                ast.Import, ast.ImportFrom)):
            return entry_ids
        else:
            label = short(stmt, 50)
            if not label:
                return entry_ids
            nid = self.node("[", "]", label)
            for e in entry_ids:
                self.edge(e, nid)
            return [nid]

    def _label_last_edges_from(self, node_id, label, count):
        # Find edges "node_id --> X" without a label and add one, for the
        # edges just appended by the immediately preceding process_block call.
        replaced = 0
        for i in range(len(self.edges) - 1, -1, -1):
            if replaced >= 1:
                break
            e = self.edges[i]
            prefix = f"    {node_id} --> "
            if e.startswith(prefix):
                target = e[len(prefix):]
                self.edges[i] = f"    {node_id} -->|{label}| {target}"
                replaced += 1

    def render(self, func_node):
        start_id = self.node("([", "])", f"{self.func_name} start")
        out_ids = self.process_block(func_node.body, [start_id])
        if out_ids:
            end_id = self.node("([", "])", "end")
            for e in out_ids:
                self.edge(e, end_id)
        return "\n".join(self.lines + self.edges)


def build_mermaid(func_node, qualname):
    try:
        fb = FlowBuilder(qualname)
        return fb.render(func_node)
    except Exception as e:  # pragma: no cover - best-effort diagram
        return f"flowchart TD\n    n0[\"(diagram unavailable: {e})\"]"


# --- Top-level driver -----------------------------------------------------------

def iter_functions(tree, class_name=None):
    for node in tree.body if hasattr(tree, "body") else []:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield node, class_name
            yield from iter_functions(node, class_name)  # nested functions
        elif isinstance(node, ast.ClassDef):
            yield from iter_functions(node, node.name)


def analyze_file(path, mermaid=True):
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    tree = ast.parse(source, filename=path)

    out = [f"## File: `{path}`", ""]

    # Module-level ("script body") control flow, if any statements exist
    # outside of function/class/import definitions.
    top_level = [n for n in tree.body
                 if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                                        ast.ClassDef, ast.Import, ast.ImportFrom))]
    module_io_items = []
    module_fields = {}

    if top_level:
        loops, conditions = collect_loops_and_conditions(tree)
        # Exclude loops/conditions that live inside functions (already reported there)
        func_line_ranges = []
        for node, _ in iter_functions(tree):
            end = max((getattr(n, "lineno", node.lineno) for n in ast.walk(node)), default=node.lineno)
            func_line_ranges.append((node.lineno, end))

        def in_a_function(lineno):
            return any(start <= lineno <= end for start, end in func_line_ranges)

        loops = [l for l in loops if not in_a_function(l[0])]
        conditions = [c for c in conditions if not in_a_function(c[0])]

        out.append("### `MODULE` (top-level script logic)")
        out.append(f"- **Loops:** {len(loops)}")
        for ln, text in loops:
            out.append(f"  - line {ln}: `{text}`")
        out.append(f"- **Conditions:** {len(conditions)}")
        for ln, text in conditions:
            out.append(f"  - line {ln}: `{text}`")
        out.append("")
        out.append("**Pseudocode:**")
        out.append("```")
        out.append("MODULE (runs top-to-bottom on import/execution):")
        out.extend(render_block(top_level))
        out.append("```")
        out.append("")
        if mermaid:
            fb = FlowBuilder("MODULE")
            entry = fb.node("([", "])", "MODULE start")
            out_ids = fb.process_block(top_level, [entry])
            if out_ids:
                end_id = fb.node("([", "])", "end")
                for e in out_ids:
                    fb.edge(e, end_id)
            out.append("**Flowchart:**")
            out.append("```mermaid")
            out.append("\n".join(fb.lines + fb.edges))
            out.append("```")
            out.append("")
        module_io_items, module_fields = detect_io(tree, {})
        # keep only items whose line is in top-level range (functions report their own)
        module_io_items = [it for it in module_io_items if not in_a_function(it.lineno)]

    all_io = list(module_io_items)
    all_fields = dict(module_fields)

    for node, class_name in iter_functions(tree):
        entry_lines, io_items, fields = build_function_entry(node, path, class_name)
        out.extend(entry_lines)
        if mermaid:
            qualname = f"{class_name}.{node.name}" if class_name else node.name
            out.append("**Flowchart:**")
            out.append("```mermaid")
            out.append(build_mermaid(node, qualname))
            out.append("```")
            out.append("")
        all_io.extend(io_items)
        all_fields.update(fields)

    return "\n".join(out), all_io, all_fields


def find_python_files(target):
    if os.path.isfile(target):
        return [target]
    files = []
    skip_dirs = {".git", "__pycache__", "venv", ".venv", "node_modules", "env"}
    for root, dirs, filenames in os.walk(target):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fn in filenames:
            if fn.endswith(".py"):
                files.append(os.path.join(root, fn))
    return sorted(files)


def build_report(target, mermaid=True):
    files = find_python_files(target)
    sections = [f"# Reverse-Engineered Outline: `{target}`", ""]
    all_io = []
    all_fields = {}

    for path in files:
        try:
            section, io_items, fields = analyze_file(path, mermaid=mermaid)
        except SyntaxError as e:
            sections.append(f"## File: `{path}`\n\n_Skipped: syntax error ({e})_\n")
            continue
        sections.append(section)
        all_io.extend((path, it) for it in io_items)
        for (var, key), ln in fields.items():
            all_fields.setdefault((var, key), (path, ln))

    io_section = ["## Input / Output Summary", ""]
    inputs = [(p, it) for p, it in all_io if it.direction == "input"]
    outputs = [(p, it) for p, it in all_io if it.direction == "output"]

    io_section.append("### Inputs")
    if inputs:
        io_section.append("| Kind | Detail | Location |")
        io_section.append("|---|---|---|")
        for p, it in inputs:
            io_section.append(f"| {it.kind} | `{it.detail}` | `{p}:{it.lineno}` |")
    else:
        io_section.append("_None detected._")
    io_section.append("")

    io_section.append("### Outputs")
    if outputs:
        io_section.append("| Kind | Detail | Location |")
        io_section.append("|---|---|---|")
        for p, it in outputs:
            io_section.append(f"| {it.kind} | `{it.detail}` | `{p}:{it.lineno}` |")
    else:
        io_section.append("_None detected._")
    io_section.append("")

    io_section.append("### Fields Accessed (subscript keys, e.g. DataFrame/dict columns)")
    if all_fields:
        io_section.append("| Variable | Field | First Seen |")
        io_section.append("|---|---|---|")
        for (var, key), (p, ln) in sorted(all_fields.items()):
            io_section.append(f"| `{var}` | `{key}` | `{p}:{ln}` |")
    else:
        io_section.append("_None detected._")
    io_section.append("")

    return "\n".join(sections) + "\n" + "\n".join(io_section)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="Python file or directory to analyze")
    parser.add_argument("-o", "--output", help="Write report to this file (default: stdout)")
    parser.add_argument("--no-mermaid", action="store_true", help="Skip Mermaid flowcharts")
    args = parser.parse_args()

    report = build_report(args.target, mermaid=not args.no_mermaid)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Wrote report to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
