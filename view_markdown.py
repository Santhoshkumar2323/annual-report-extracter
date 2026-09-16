from pathlib import Path
import html
import webbrowser
import tempfile


def find_markdown_files() -> list[Path]:

    root_dir = Path(__file__).resolve().parent
    results_dir = root_dir / "results"

    if not results_dir.exists():
        print("\nERROR: 'results' folder does not exist.")
        print(f"Expected location:\n{results_dir}")
        return []

    markdown_files = sorted(
        results_dir.glob("*.md"),
        key=lambda p: p.name.lower()
    )

    return markdown_files


def choose_markdown_file(files: list[Path]) -> Path:

    if len(files) == 1:
        print(f"\nFound Markdown file: {files[0].name}")
        return files[0]

    print("\nMultiple Markdown files found:\n")

    for i, file in enumerate(files, start=1):
        print(f"  {i}. {file.name}")

    print()

    while True:
        choice = input(
            f"Which file do you want to open? (1-{len(files)}): "
        ).strip()

        if choice.isdigit():
            index = int(choice)

            if 1 <= index <= len(files):
                return files[index - 1]

        print("Invalid choice. Please enter a valid number.")


def markdown_to_html(markdown_text: str) -> str:
    try:
        import markdown
    except ImportError:
        print("\nERROR: The 'markdown' package is not installed.")
        print("\nInstall it with:")
        print("    pip install markdown")
        raise SystemExit(1)

    return markdown.markdown(
        markdown_text,
        extensions=[
            "tables",
            "fenced_code",
            "toc",
            "nl2br",
            "sane_lists",
        ],
    )


def build_html(title: str, content_html: str) -> str:

    safe_title = html.escape(title)

    return f"""<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>{safe_title}</title>

<style>

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    background: #f4f6f8;
    color: #202124;

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        Roboto,
        Helvetica,
        Arial,
        sans-serif;

    line-height: 1.65;
}}

.page {{
    width: min(1200px, calc(100% - 40px));

    margin: 40px auto;

    background: white;

    padding: 50px 60px;

    border-radius: 12px;

    box-shadow:
        0 4px 20px rgba(0, 0, 0, 0.08);
}}

h1 {{
    font-size: 32px;
    line-height: 1.25;

    margin-top: 0;
    margin-bottom: 28px;

    border-bottom: 2px solid #e5e7eb;

    padding-bottom: 18px;
}}

h2 {{
    font-size: 26px;

    margin-top: 42px;

    padding-bottom: 8px;

    border-bottom: 1px solid #e5e7eb;
}}

h3 {{
    font-size: 21px;
    margin-top: 32px;
}}

h4 {{
    font-size: 18px;
    margin-top: 25px;
}}

p {{
    margin: 12px 0;
}}

ul,
ol {{
    padding-left: 30px;
}}

li {{
    margin: 5px 0;
}}

strong {{
    font-weight: 700;
}}

blockquote {{
    margin: 20px 0;

    padding: 12px 20px;

    border-left: 4px solid #888;

    background: #f7f7f7;

    color: #555;
}}

code {{
    background: #f1f3f4;

    padding: 2px 6px;

    border-radius: 4px;

    font-family:
        Consolas,
        "Courier New",
        monospace;

    font-size: 0.9em;
}}

pre {{
    background: #1e1e1e;

    color: #f5f5f5;

    padding: 18px;

    border-radius: 8px;

    overflow-x: auto;

    line-height: 1.5;
}}

pre code {{
    background: transparent;
    padding: 0;
    color: inherit;
}}

table {{
    width: 100%;

    border-collapse: collapse;

    margin: 25px 0;

    font-size: 14px;
}}

th {{
    background: #f0f2f4;

    font-weight: 700;

    text-align: left;
}}

th,
td {{
    border: 1px solid #d9dde1;

    padding: 10px 12px;

    vertical-align: top;
}}

tr:nth-child(even) {{
    background: #fafafa;
}}

img {{
    max-width: 100%;
    height: auto;
}}

a {{
    color: #0969da;
    text-decoration: none;
}}

a:hover {{
    text-decoration: underline;
}}

hr {{
    border: 0;

    border-top: 1px solid #ddd;

    margin: 35px 0;
}}

.file-info {{
    color: #666;

    font-size: 14px;

    margin-bottom: 30px;
}}

@media (max-width: 700px) {{

    .page {{
        width: 100%;

        margin: 0;

        padding: 25px 20px;

        border-radius: 0;
    }}

    h1 {{
        font-size: 27px;
    }}

    h2 {{
        font-size: 23px;
    }}

    table {{
        display: block;

        overflow-x: auto;
    }}

}}

</style>

</head>

<body>

<div class="page">

    <h1>{safe_title}</h1>

    <div class="file-info">
        Source: results/{html.escape(title)}.md
    </div>

    {content_html}

</div>

</body>

</html>
"""


def open_markdown_file(markdown_path: Path):

    print(f"\nReading: {markdown_path.name}")

    try:
        markdown_text = markdown_path.read_text(
            encoding="utf-8"
        )
    except UnicodeDecodeError:
        print(
            "\nERROR: Could not read the Markdown file as UTF-8."
        )
        return

    print("Converting Markdown to HTML...")

    content_html = markdown_to_html(markdown_text)

    page_title = markdown_path.stem

    full_html = build_html(
        page_title,
        content_html
    )

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".html",
        delete=False,
        encoding="utf-8"
    ) as f:

        f.write(full_html)

        html_path = Path(f.name)

    print("Opening browser...")

    webbrowser.open(
        html_path.resolve().as_uri()
    )

    print(f"\nOpened: {markdown_path.name}")
    print("Done.")


def main():

    print("=" * 70)
    print("MARKDOWN VIEWER")
    print("=" * 70)

    markdown_files = find_markdown_files()

    if not markdown_files:
        print(
            "\nNo Markdown files found in the results folder."
        )
        print(
            "\nExpected folder:"
        )
        print(
            f"    {Path(__file__).resolve().parent / 'results'}"
        )
        return

    if len(markdown_files) == 1:
        selected_file = markdown_files[0]

    else:
        selected_file = choose_markdown_file(
            markdown_files
        )

    open_markdown_file(selected_file)


if __name__ == "__main__":
    main()

