import os
import tempfile
from pathlib import Path
from typing import Any

def create_page_slice(
    pdf_path: Path,
    start_page: int,
    end_page: int,
) -> Path:
    from pypdf import PdfReader, PdfWriter

    if start_page < 1:
        raise ValueError("start_page must be >= 1")

    if end_page < start_page:
        raise ValueError(
            "end_page must be >= start_page"
        )

    reader = PdfReader(str(pdf_path))

    total_pages = len(reader.pages)

    if end_page > total_pages:
        raise ValueError(
            f"Page range {start_page}-{end_page} is outside "
            f"the PDF. PDF has {total_pages} pages."
        )

    writer = PdfWriter()

    for page_index in range(
        start_page - 1,
        end_page,
    ):
        writer.add_page(
            reader.pages[page_index]
        )

    fd, temp_path = tempfile.mkstemp(
        suffix=".pdf"
    )

    os.close(fd)

    temp_path = Path(temp_path)

    try:
        with open(temp_path, "wb") as output_file:
            writer.write(output_file)

    except Exception:
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass

        raise

    return temp_path


def parse_with_llamaparse(
    pdf_path: Path,
    tier: str = "agentic",
) -> str:

    try:
        from llama_cloud import LlamaCloud

    except ImportError as exc:
        raise RuntimeError(
            "llama-cloud package is not installed. "
            "Run: pip install -r requirements.txt"
        ) from exc

    api_key = os.environ.get(
        "LLAMA_CLOUD_API_KEY"
    )

    if not api_key:
        raise RuntimeError(
            "LLAMA_CLOUD_API_KEY environment variable "
            "is not set."
        )
    client = LlamaCloud(
        api_key=api_key
    )

    print(
        "      Uploading temporary PDF to LlamaParse...",
        flush=True,
    )

    uploaded_file = client.files.create(
        file=str(pdf_path),
        purpose="parse",
    )

    print(
        "      Upload complete.",
        flush=True,
    )

    print(
        "      Starting LlamaParse extraction...",
        flush=True,
    )

    result = client.parsing.parse(
        file_id=uploaded_file.id,
        tier=tier,
        version="latest",
        expand=["markdown"],
    )

    print(
        "      LlamaParse extraction returned.",
        flush=True,
    )

    markdown_result = getattr(
        result,
        "markdown",
        None,
    )

    if not markdown_result:
        return ""


    pages = getattr(
        markdown_result,
        "pages",
        None,
    )

    if pages:

        extracted_pages: list[str] = []

        for page in pages:

            page_markdown = getattr(
                page,
                "markdown",
                None,
            )

            if isinstance(
                page_markdown,
                str,
            ):
                extracted_pages.append(
                    page_markdown
                )

        if extracted_pages:

            return "\n\n".join(
                extracted_pages
            )

    if isinstance(
        markdown_result,
        str,
    ):
        return markdown_result

    return ""



def extract_range(
    pdf_path: Path,
    start_page: int,
    end_page: int,
    tier: str = "agentic",
) -> str:

    print(
        f"      Creating temporary PDF for pages "
        f"{start_page}-{end_page}...",
        flush=True,
    )

    temporary_pdf = create_page_slice(
        pdf_path=pdf_path,
        start_page=start_page,
        end_page=end_page,
    )

    print(
        "      Temporary PDF created.",
        flush=True,
    )

    try:

        markdown = parse_with_llamaparse(
            pdf_path=temporary_pdf,
            tier=tier,
        )

        if not markdown.strip():
            raise RuntimeError(
                f"No Markdown was returned for pages "
                f"{start_page}-{end_page}."
            )

        print(
            "      Markdown successfully extracted.",
            flush=True,
        )

        return markdown

    finally:

        print(
            "      Cleaning up temporary PDF...",
            flush=True,
        )

        try:
            temporary_pdf.unlink()

            print(
                "      Temporary PDF deleted.",
                flush=True,
            )

        except FileNotFoundError:
            pass

        except PermissionError:
            print(
                "      Warning: temporary PDF could not "
                "be deleted immediately.",
                flush=True,
            )



SECTION_TYPES = (
    "Consolidated",
    "Standalone",
    "Notes",
    "Custom",
)


def normalize_section_name(
    section: str,
) -> str:

    section = section.strip()

    if not section:
        raise ValueError(
            "Section name cannot be empty."
        )

    safe_name = "".join(
        character
        if character.isalnum()
        or character in ("-", "_")
        else "_"
        for character in section
    )

    return safe_name.strip("_")



def make_unique_output_path(
    results_dir: Path,
    pdf_path: Path,
    section: str,
    start_page: int,
    end_page: int,
) -> Path:

    results_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_section = normalize_section_name(
        section
    )

    base_name = (
        f"{pdf_path.stem}_"
        f"{safe_section}_"
        f"p{start_page}-{end_page}"
    )

    output_path = (
        results_dir /
        f"{base_name}.md"
    )

    counter = 2

    while output_path.exists():

        output_path = (
            results_dir /
            f"{base_name}_{counter}.md"
        )

        counter += 1

    return output_path


def save_separate_markdown(
    results_dir: Path,
    pdf_path: Path,
    section: str,
    start_page: int,
    end_page: int,
    markdown: str,
) -> Path:
    print(
        "      Saving Markdown file...",
        flush=True,
    )

    output_path = make_unique_output_path(
        results_dir=results_dir,
        pdf_path=pdf_path,
        section=section,
        start_page=start_page,
        end_page=end_page,
    )

    output_path.write_text(
        markdown,
        encoding="utf-8",
    )

    print(
        f"      Saved: {output_path.name}",
        flush=True,
    )

    return output_path


def build_compiled_markdown(
    pdf_path: Path,
    extractions: list[dict[str, Any]],
) -> str:

    parts: list[str] = []

    title = (
        f"# {pdf_path.stem} — "
        f"Extracted Sections"
    )

    parts.append(title)

    parts.append("")

    for extraction in extractions:

        section = extraction["section"]
        start_page = extraction["start_page"]
        end_page = extraction["end_page"]
        markdown = extraction["markdown"]

        parts.append(
            f"# {section}"
        )

        parts.append("")

        parts.append(
            f"## Pages {start_page}-{end_page}"
        )

        parts.append("")

        parts.append(markdown.strip())

        parts.append("")

    return "\n".join(parts).strip() + "\n"



def save_compiled_markdown(
    results_dir: Path,
    pdf_path: Path,
    markdown: str,
) -> Path:

    print(
        "      Saving compiled Markdown file...",
        flush=True,
    )

    results_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    base_name = (
        f"{pdf_path.stem}_compiled"
    )

    output_path = (
        results_dir /
        f"{base_name}.md"
    )

    counter = 2

    while output_path.exists():

        output_path = (
            results_dir /
            f"{base_name}_{counter}.md"
        )

        counter += 1

    output_path.write_text(
        markdown,
        encoding="utf-8",
    )

    print(
        f"      Saved: {output_path.name}",
        flush=True,
    )

    return output_path


def extract_multiple_ranges(
    pdf_path: Path,
    ranges: list[dict[str, Any]],
    results_dir: Path,
    output_mode: str = "separate",
    tier: str = "agentic",
) -> list[Path]:


    if not ranges:
        raise ValueError(
            "At least one page range is required."
        )

    if output_mode not in (
        "separate",
        "compiled",
    ):
        raise ValueError(
            "output_mode must be "
            "'separate' or 'compiled'."
        )

    extractions: list[dict[str, Any]] = []

    output_paths: list[Path] = []

    total_ranges = len(ranges)

    print()
    print("=" * 70)
    print(
        f"Extraction engine: {total_ranges} range(s)"
    )
    print("=" * 70)


    for index, extraction in enumerate(
        ranges,
        start=1,
    ):

        start_page = int(
            extraction["start_page"]
        )

        end_page = int(
            extraction["end_page"]
        )

        section = str(
            extraction["section"]
        ).strip()

        if not section:
            raise ValueError(
                "Every extraction must have a section."
            )

        print()
        print("-" * 70)
        print(
            f"[{index}/{total_ranges}] "
            f"Extracting {section} — "
            f"pages {start_page}-{end_page}"
        )
        print("-" * 70)

        markdown = extract_range(
            pdf_path=pdf_path,
            start_page=start_page,
            end_page=end_page,
            tier=tier,
        )

        if not markdown.strip():
            raise RuntimeError(
                f"No Markdown was returned for "
                f"{section} pages "
                f"{start_page}-{end_page}."
            )

        extractions.append(
            {
                "start_page": start_page,
                "end_page": end_page,
                "section": section,
                "markdown": markdown,
            }
        )

        print(
            f"      ✓ Range {index}/{total_ranges} "
            f"complete.",
            flush=True,
        )


    if output_mode == "separate":

        print()
        print("=" * 70)
        print("Saving separate Markdown files")
        print("=" * 70)

        for index, extraction in enumerate(
            extractions,
            start=1,
        ):

            output_path = save_separate_markdown(
                results_dir=results_dir,
                pdf_path=pdf_path,
                section=extraction["section"],
                start_page=extraction["start_page"],
                end_page=extraction["end_page"],
                markdown=extraction["markdown"],
            )

            output_paths.append(
                output_path
            )

            print(
                f"      ✓ Saved file "
                f"{index}/{total_ranges}.",
                flush=True,
            )

        return output_paths


    print()
    print("=" * 70)
    print("Building compiled Markdown")
    print("=" * 70)

    compiled_markdown = build_compiled_markdown(
        pdf_path=pdf_path,
        extractions=extractions,
    )

    output_path = save_compiled_markdown(
        results_dir=results_dir,
        pdf_path=pdf_path,
        markdown=compiled_markdown,
    )

    output_paths.append(
        output_path
    )

    print(
        "      ✓ Compiled Markdown complete.",
        flush=True,
    )

    return output_paths


def find_pdf_files(
    annual_reports_dir: Path,
) -> list[Path]:

    if not annual_reports_dir.exists():

        raise FileNotFoundError(
            f"Annual reports directory does not exist: "
            f"{annual_reports_dir}"
        )

    if not annual_reports_dir.is_dir():

        raise NotADirectoryError(
            f"Not a directory: "
            f"{annual_reports_dir}"
        )

    pdf_files = sorted(
        [
            path
            for path in annual_reports_dir.iterdir()
            if path.is_file()
            and path.suffix.lower() == ".pdf"
        ],
        key=lambda path: path.name.lower(),
    )

    return pdf_files


def get_pdf_page_count(
    pdf_path: Path,
) -> int:

    from pypdf import PdfReader

    reader = PdfReader(
        str(pdf_path)
    )

    return len(reader.pages)