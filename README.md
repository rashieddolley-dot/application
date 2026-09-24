# Smart Burndown (app.py)

A Streamlit budget dashboard that plots your planned vs. actual monthly spending burndown.

## Run it (any machine, including Android via Termux)

```bash
pip install -r requirements.txt
streamlit run app.py
```

Streamlit prints a `http://localhost:8501` link — open it in a browser. On Android/Termux, open that link in your phone's regular browser app (Termux itself has no browser).

---

# Reverse Engineer

`reverse_engineer.py` reads Python source code and produces a Markdown outline you can turn straight into diagrams — no manual note-taking required.

For every function (and the top-level script body) it lists:

- **Every function**, with its file and line number
- **Loops** (`for`/`while`), listed individually with line numbers
- **Conditions** (`if`/`elif`), listed individually with line numbers
- **Pseudocode** — a plain-English, indented rewrite of the logic (`IF`, `FOR`, `WHILE`, `RETURN`, ...)
- **A Mermaid flowchart** (` ```mermaid ` block) — paste it into [mermaid.live](https://mermaid.live) or any Markdown viewer that renders Mermaid (GitHub, Notion, Obsidian, VS Code) to get an instant diagram
- **Fields accessed** — e.g. `df['Category']` — so you can see what data a function reads

At the end of the report it also lists, across the whole codebase:

- **Inputs**: file reads (`open()`, `pd.read_csv`, ...), Streamlit input widgets (`st.number_input`, `st.file_uploader`, ...)
- **Outputs**: file writes (`.to_csv`, ...), Streamlit output widgets (`st.metric`, `st.plotly_chart`, ...)
- **Fields**: every dict/DataFrame key accessed via `var['key']`, across the whole codebase

## Usage

```bash
# Analyze a single file, print to stdout
python3 reverse_engineer.py app.py

# Analyze a whole directory (recurses, skips .git/venv/__pycache__)
python3 reverse_engineer.py . -o outline.md

# Skip the Mermaid flowcharts (faster, shorter output)
python3 reverse_engineer.py app.py --no-mermaid
```

## Example

Running it on `app.py` in this repo produces, for `calculate_velocity`:

```
FUNCTION calculate_velocity(df):
IF df.empty:
    RETURN 50.0
total_days = (pd.to_datetime(df['Date']).max() - pd.to_datetime(df['Date…
IF total_days <= 0:
    total_days = 30
cat_spend = df.groupby('Category')['Amount'].sum() / total_days
RETURN cat_spend
```

plus a Mermaid flowchart with a diamond decision node for each `IF`, and a table entry noting it reads the `Date` and `Amount`/`Category` fields off the `df` argument.

## How it works

It's a static analyzer built on Python's built-in `ast` module — no third-party dependencies, no code execution. It walks the syntax tree of each `.py` file, so it works even on code that can't currently run (missing imports, no data files present, etc).

## Scope

- Python only (the `ast` module is Python-specific). If you need this for another language, the same approach (parse → walk the tree → render control flow) applies, but would need that language's own parser.
- The pseudocode and flowcharts are a faithful *structural* summary (control flow, calls, assignments) — they don't attempt to explain business intent, since that requires reading, not parsing.
