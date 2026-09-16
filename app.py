from __future__ import annotations

import io
import os
import zipfile
from pathlib import Path

import fitz  # PyMuPDF
import streamlit as st

import extractor


st.set_page_config(
    page_title="Annual Report Markdown Extractor",
    page_icon="📄",
    layout="wide",
)


def get_secret(name: str, default: str = "") -> str:
    try:
        return st.secrets.get(name, default)
    except Exception:
        return os.environ.get(name, default)


APP_PASSWORD = get_secret("APP_PASSWORD")
LLAMA_CLOUD_API_KEY = get_secret("LLAMA_CLOUD_API_KEY")

if LLAMA_CLOUD_API_KEY:
    os.environ["LLAMA_CLOUD_API_KEY"] = LLAMA_CLOUD_API_KEY


def check_password() -> bool:

    if st.session_state.get("authenticated"):
        return True

    st.title("🔒 Annual Report Markdown Extractor")

    if not APP_PASSWORD:
        st.error(
            "No APP_PASSWORD is configured for this app. "
            "Add APP_PASSWORD to your Streamlit secrets "
            "before deploying."
        )
        st.stop()

    with st.form("login_form"):
        pwd = st.text_input("Enter app password", type="password")
        submitted = st.form_submit_button("Enter")

    if submitted:
        if pwd == APP_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password.")

    return False


if not check_password():
    st.stop()


defaults = {
    "pdf_bytes": None,
    "pdf_name": None,
    "pdf_doc": None,
    "total_pages": 0,
    "page_cache": {},          
    "page_cache_order": [],    
    "viewer_page": 1,
    "results": [],           
    "extraction_error": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


PAGE_CACHE_LIMIT = 80



def load_pdf(uploaded_file) -> None:

    pdf_bytes = uploaded_file.getvalue()

    if pdf_bytes == st.session_state.pdf_bytes:
        return

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    st.session_state.pdf_bytes = pdf_bytes
    st.session_state.pdf_name = uploaded_file.name
    st.session_state.pdf_doc = doc
    st.session_state.total_pages = doc.page_count
    st.session_state.page_cache = {}
    st.session_state.page_cache_order = []
    st.session_state.viewer_page = 1
    st.session_state.results = []
    st.session_state.extraction_error = None


def render_page_image(page_number: int, dpi: int = 120) -> bytes:

    cache_key = (page_number, dpi)
    cache = st.session_state.page_cache

    if cache_key in cache:
        return cache[cache_key]

    doc = st.session_state.pdf_doc
    page = doc.load_page(page_number - 1)
    pix = page.get_pixmap(dpi=dpi)
    png_bytes = pix.tobytes("png")

    cache[cache_key] = png_bytes
    order = st.session_state.page_cache_order
    order.append(cache_key)

    if len(order) > PAGE_CACHE_LIMIT:
        oldest = order.pop(0)
        cache.pop(oldest, None)

    return png_bytes


def markdown_preview_html(markdown_text: str) -> str:

    import markdown as md_lib

    body_html = md_lib.markdown(
        markdown_text,
        extensions=["tables", "fenced_code", "toc", "nl2br", "sane_lists"],
    )

    return f"""
    <div style="
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
                     Roboto, Helvetica, Arial, sans-serif;
        line-height: 1.6;
        background: white;
        color: #202124;
        padding: 24px 28px;
        border-radius: 10px;
        border: 1px solid #e5e7eb;
        max-height: 520px;
        overflow-y: auto;
    ">
    <style>
        table {{ width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 14px; }}
        th, td {{ border: 1px solid #d9dde1; padding: 8px 10px; text-align: left; vertical-align: top; }}
        th {{ background: #f0f2f4; }}
        tr:nth-child(even) {{ background: #fafafa; }}
        code {{ background: #f1f3f4; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }}
        pre {{ background: #1e1e1e; color: #f5f5f5; padding: 14px; border-radius: 8px; overflow-x: auto; }}
        pre code {{ background: transparent; padding: 0; color: inherit; }}
        img {{ max-width: 100%; }}
    </style>
    {body_html}
    </div>
    """


def build_zip(files: list[dict]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            zf.writestr(f["filename"], f["markdown"])
    return buffer.getvalue()


SECTION_OPTIONS = ["Consolidated", "Standalone", "Notes", "Custom"]
TIER_OPTIONS = {
    "Agentic (best quality)": "agentic",
    "Cost Effective": "cost_effective",
    "Fast": "fast",
}



st.title("📄 Annual Report Markdown Extractor")
st.caption(
    "Upload a PDF, inspect any page, choose your page ranges, "
    "and extract clean Markdown with LlamaParse."
)

col_logout = st.columns([6, 1])[1]
with col_logout:
    if st.button("Log out"):
        st.session_state.authenticated = False
        st.rerun()



st.header("1. Upload a PDF")

uploaded_file = st.file_uploader("Annual report PDF", type=["pdf"])

if uploaded_file is not None:
    load_pdf(uploaded_file)

if st.session_state.pdf_doc is None:
    st.info("Upload a PDF to get started.")
    st.stop()

st.success(
    f"**{st.session_state.pdf_name}** — "
    f"{st.session_state.total_pages} pages loaded."
)



st.header("2. Inspect the PDF")
st.caption(
    "Browse any page, as many times as you need, to figure out "
    "which pages belong to which section before you extract."
)

total_pages = st.session_state.total_pages

nav_cols = st.columns([1, 1, 3, 1, 1])

with nav_cols[0]:
    if st.button("⏮ First"):
        st.session_state.viewer_page = 1

with nav_cols[1]:
    if st.button("◀ Prev") and st.session_state.viewer_page > 1:
        st.session_state.viewer_page -= 1

with nav_cols[2]:
    st.session_state.viewer_page = st.number_input(
        "Go to page",
        min_value=1,
        max_value=total_pages,
        value=min(st.session_state.viewer_page, total_pages),
        step=1,
        label_visibility="collapsed",
    )

with nav_cols[3]:
    if st.button("Next ▶") and st.session_state.viewer_page < total_pages:
        st.session_state.viewer_page += 1

with nav_cols[4]:
    if st.button("Last ⏭"):
        st.session_state.viewer_page = total_pages

quality = st.select_slider(
    "Preview quality",
    options=["Fast", "Balanced", "Sharp"],
    value="Balanced",
    help="Higher quality is slower to render on very large PDFs.",
)
dpi_map = {"Fast": 90, "Balanced": 120, "Sharp": 160}

current_page = int(st.session_state.viewer_page)
png_bytes = render_page_image(current_page, dpi=dpi_map[quality])

st.image(
    png_bytes,
    caption=f"Page {current_page} of {total_pages}",
    use_container_width=False,
)


# ============================================================
# 3. HOW MANY RANGES (the only free-typed number)
# ============================================================

st.header("3. How many page ranges do you want to extract?")

number_of_ranges = st.number_input(
    "Number of ranges",
    min_value=1,
    max_value=200,
    value=1,
    step=1,
)


st.header("4. Configure each range")

ranges: list[dict] = []
config_valid = True

for i in range(int(number_of_ranges)):
    with st.expander(f"Range {i + 1}", expanded=True):
        c1, c2, c3 = st.columns([1, 1, 2])

        with c1:
            start_page = st.number_input(
                "Start page",
                min_value=1,
                max_value=total_pages,
                value=1,
                step=1,
                key=f"start_{i}",
            )

        with c2:
            end_page = st.number_input(
                "End page",
                min_value=1,
                max_value=total_pages,
                value=1,
                step=1,
                key=f"end_{i}",
            )

        with c3:
            section_choice = st.selectbox(
                "Section type",
                SECTION_OPTIONS,
                key=f"section_{i}",
            )

            section_name = section_choice

            if section_choice == "Custom":
                custom_name = st.text_input(
                    "Custom section name",
                    key=f"custom_section_{i}",
                )
                section_name = custom_name.strip()

        if end_page < start_page:
            st.warning("End page must be ≥ start page.")
            config_valid = False

        if section_choice == "Custom" and not section_name:
            st.warning("Enter a name for this custom section.")
            config_valid = False

        st.caption(f"👀 Preview page {start_page} of this range:")
        try:
            preview_bytes = render_page_image(int(start_page), dpi=90)
            st.image(preview_bytes, width=260)
        except Exception:
            pass

        ranges.append(
            {
                "start_page": int(start_page),
                "end_page": int(end_page),
                "section": section_name,
            }
        )


# ============================================================
# 5. TIER + OUTPUT MODE (click-only)
# ============================================================

st.header("5. Extraction settings")

c1, c2 = st.columns(2)

with c1:
    tier_label = st.selectbox("LlamaParse tier", list(TIER_OPTIONS.keys()))
    tier = TIER_OPTIONS[tier_label]

with c2:
    if number_of_ranges > 1:
        output_mode_label = st.radio(
            "How should the Markdown be saved?",
            ["Separate files (one per range)", "One compiled file"],
        )
        output_mode = (
            "separate"
            if output_mode_label.startswith("Separate")
            else "compiled"
        )
    else:
        output_mode = "separate"
        st.caption("Single range → one Markdown file.")


st.header("6. Review & extract")

st.table(
    [
        {
            "#": i + 1,
            "Section": r["section"],
            "Pages": f"{r['start_page']}-{r['end_page']}",
        }
        for i, r in enumerate(ranges)
    ]
)

if not LLAMA_CLOUD_API_KEY:
    st.error(
        "No LLAMA_CLOUD_API_KEY is configured for this app. "
        "Add it to your Streamlit secrets before extracting."
    )

extract_clicked = st.button(
    "🚀 Start extraction",
    type="primary",
    disabled=not config_valid or not LLAMA_CLOUD_API_KEY,
)

if extract_clicked:
    st.session_state.results = []
    st.session_state.extraction_error = None

    import tempfile

    tmp_dir = tempfile.mkdtemp()
    pdf_path = Path(tmp_dir) / st.session_state.pdf_name
    pdf_path.write_bytes(st.session_state.pdf_bytes)

    progress = st.progress(0.0)
    status = st.empty()

    extractions = []
    total = len(ranges)

    try:
        for idx, r in enumerate(ranges, start=1):
            status.info(
                f"[{idx}/{total}] Extracting **{r['section']}** — "
                f"pages {r['start_page']}-{r['end_page']}..."
            )

            markdown_text = extractor.extract_range(
                pdf_path=pdf_path,
                start_page=r["start_page"],
                end_page=r["end_page"],
                tier=tier,
            )

            extractions.append(
                {
                    "start_page": r["start_page"],
                    "end_page": r["end_page"],
                    "section": r["section"],
                    "markdown": markdown_text,
                }
            )

            progress.progress(idx / total)

        status.info("Saving results...")

        results = []

        if output_mode == "separate":
            for e in extractions:
                safe_section = extractor.normalize_section_name(e["section"])
                filename = (
                    f"{pdf_path.stem}_{safe_section}_"
                    f"p{e['start_page']}-{e['end_page']}.md"
                )
                results.append(
                    {
                        "filename": filename,
                        "markdown": e["markdown"],
                        "label": f"{e['section']} (pages {e['start_page']}-{e['end_page']})",
                    }
                )
        else:
            compiled = extractor.build_compiled_markdown(
                pdf_path=pdf_path,
                extractions=extractions,
            )
            results.append(
                {
                    "filename": f"{pdf_path.stem}_compiled.md",
                    "markdown": compiled,
                    "label": "Compiled Markdown",
                }
            )

        st.session_state.results = results
        status.success("Extraction complete!")
        progress.progress(1.0)

    except Exception as exc:
        st.session_state.extraction_error = str(exc)
        status.error(f"Extraction failed: {exc}")

        if extractions:
            st.warning(
                f"{len(extractions)} of {total} range(s) completed "
                "before the error. Nothing was saved for them since "
                "the batch stopped early."
            )


if st.session_state.results:
    st.header("7. Results")

    results = st.session_state.results

    if len(results) > 1:
        zip_bytes = build_zip(results)
        st.download_button(
            "⬇️ Download all as ZIP",
            data=zip_bytes,
            file_name=f"{Path(st.session_state.pdf_name).stem}_extracted.zip",
            mime="application/zip",
        )

    for r in results:
        with st.expander(f"📄 {r['label']} — {r['filename']}", expanded=False):
            st.download_button(
                "⬇️ Download Markdown",
                data=r["markdown"],
                file_name=r["filename"],
                mime="text/markdown",
                key=f"dl_{r['filename']}",
            )
            st.components.v1.html(
                markdown_preview_html(r["markdown"]),
                height=540,
                scrolling=True,
            )