from pathlib import Path
import sys
import time
import extractor


ROOT_DIR = Path(__file__).resolve().parent

ANNUAL_REPORTS_DIR = (
    ROOT_DIR / "annual_reports"
)

RESULTS_DIR = (
    ROOT_DIR / "results"
)



def print_line():
    print("=" * 70)


def print_header(title: str):
    print()
    print_line()
    print(title)
    print_line()



def choose_pdf() -> Path:

    try:
        pdf_files = extractor.find_pdf_files(
            ANNUAL_REPORTS_DIR
        )

    except Exception as exc:
        print(
            f"\nERROR: {exc}"
        )
        sys.exit(1)

    if not pdf_files:

        print(
            "\nNo PDF files were found in:"
        )

        print(
            f"  {ANNUAL_REPORTS_DIR}"
        )

        print(
            "\nPut your annual report PDFs inside "
            "the annual_reports folder."
        )

        sys.exit(1)

    print_header(
        f"Annual Reports Found: {len(pdf_files)}"
    )

    for number, pdf_path in enumerate(
        pdf_files,
        start=1,
    ):
        print(
            f"{number}. {pdf_path.name}"
        )

    while True:

        raw = input(
            "\nChoose report number: "
        ).strip()

        try:
            choice = int(raw)

        except ValueError:
            print(
                "Please enter a number."
            )
            continue

        if 1 <= choice <= len(pdf_files):

            selected_pdf = pdf_files[
                choice - 1
            ]

            return selected_pdf

        print(
            f"Please choose a number "
            f"between 1 and {len(pdf_files)}."
        )


def ask_page_range(
    total_pages: int,
    range_number: int,
) -> tuple[int, int]:

    while True:

        print(
            f"\nRange {range_number}"
        )

        raw = input(
            f"Enter page range "
            f"(1-{total_pages}, e.g. 192-196): "
        ).strip()

        try:

            if "-" in raw:

                parts = raw.split(
                    "-",
                    maxsplit=1,
                )

                if len(parts) != 2:
                    raise ValueError

                start_page = int(
                    parts[0].strip()
                )

                end_page = int(
                    parts[1].strip()
                )

            else:

                # A single number means one page.
                start_page = int(raw)
                end_page = start_page

        except ValueError:

            print(
                "Invalid page range."
            )

            continue

        if start_page < 1:

            print(
                "Page number must be at least 1."
            )

            continue

        if end_page > total_pages:

            print(
                f"PDF has only "
                f"{total_pages} pages."
            )

            continue

        if start_page > end_page:

            print(
                "Start page cannot be greater "
                "than end page."
            )

            continue

        return start_page, end_page



def ask_section() -> str:

    print(
        "\nWhat type of section is this?"
    )

    print(
        "1. Consolidated"
    )

    print(
        "2. Standalone"
    )

    print(
        "3. Notes"
    )

    print(
        "4. Custom"
    )

    while True:

        choice = input(
            "\nChoose section type: "
        ).strip()

        if choice == "1":
            return "Consolidated"

        if choice == "2":
            return "Standalone"

        if choice == "3":
            return "Notes"

        if choice == "4":

            while True:

                custom_name = input(
                    "Enter custom section name: "
                ).strip()

                if custom_name:
                    return custom_name

                print(
                    "Section name cannot be empty."
                )

        print(
            "Please choose 1, 2, 3, or 4."
        )


def ask_number_of_ranges() -> int:

    while True:

        raw = input(
            "\nHow many page ranges do you "
            "want to extract? "
        ).strip()

        try:
            number = int(raw)

        except ValueError:

            print(
                "Please enter a whole number."
            )

            continue

        if number < 1:

            print(
                "You need at least 1 range."
            )

            continue

        return number



def ask_tier() -> str:

    print(
        "\nLlamaParse tier:"
    )

    print(
        "1. Agentic"
    )

    print(
        "2. Cost Effective"
    )

    print(
        "3. Fast"
    )

    while True:

        choice = input(
            "\nChoose tier [1]: "
        ).strip()

        if not choice:
            choice = "1"

        if choice == "1":
            return "agentic"

        if choice == "2":
            return "cost_effective"

        if choice == "3":
            return "fast"

        print(
            "Please choose 1, 2, or 3."
        )


def ask_output_mode(
    number_of_ranges: int,
) -> str:

    if number_of_ranges == 1:
        return "separate"

    print(
        "\nYou selected "
        f"{number_of_ranges} page ranges."
    )

    print(
        "\nHow should the Markdown be saved?"
    )

    print(
        "1. Separate Markdown files"
    )

    print(
        "2. One compiled Markdown file"
    )

    while True:

        choice = input(
            "\nChoose output mode: "
        ).strip()

        if choice == "1":
            return "separate"

        if choice == "2":
            return "compiled"

        print(
            "Please choose 1 or 2."
        )



def display_ranges(
    ranges: list[dict],
):
    print_header(
        "Extraction Plan"
    )

    for number, extraction in enumerate(
        ranges,
        start=1,
    ):

        print(
            f"{number}. "
            f"{extraction['section']} "
            f"— pages "
            f"{extraction['start_page']}-"
            f"{extraction['end_page']}"
        )



def confirm_extraction() -> bool:

    while True:

        choice = input(
            "\nStart extraction? [Y/n]: "
        ).strip().lower()

        if not choice:
            return True

        if choice in (
            "y",
            "yes",
        ):
            return True

        if choice in (
            "n",
            "no",
        ):
            return False

        print(
            "Please enter Y or N."
        )



def run_extraction(
    pdf_path: Path,
    ranges: list[dict],
    output_mode: str,
    tier: str,
):
    print_header(
        "Starting Extraction"
    )

    print(
        f"PDF: {pdf_path.name}"
    )

    print(
        f"Ranges: {len(ranges)}"
    )

    print(
        f"Tier: {tier}"
    )

    print(
        f"Output: {output_mode}"
    )

    start_time = time.time()

    try:

        output_paths = (
            extractor.extract_multiple_ranges(
                pdf_path=pdf_path,
                ranges=ranges,
                results_dir=RESULTS_DIR,
                output_mode=output_mode,
                tier=tier,
            )
        )

    except Exception as exc:

        print_header(
            "Extraction Failed"
        )

        print(
            f"ERROR: {exc}"
        )

        return False

    elapsed = (
        time.time() - start_time
    )

    print_header(
        "Extraction Complete"
    )

    print(
        f"Time: {elapsed:.1f} seconds"
    )

    print(
        "\nCreated file(s):"
    )

    for output_path in output_paths:

        print(
            f"  {output_path}"
        )

    print(
        "\nResults folder:"
    )

    print(
        f"  {RESULTS_DIR}"
    )

    return True


def main():

    print_header(
        "Annual Report Markdown Extractor"
    )

    print(
        "This tool extracts selected page ranges "
        "from annual report PDFs using LlamaParse."
    )

    pdf_path = choose_pdf()

    print(
        f"\nSelected PDF:"
    )

    print(
        f"  {pdf_path.name}"
    )


    try:

        total_pages = (
            extractor.get_pdf_page_count(
                pdf_path
            )
        )

    except Exception as exc:

        print(
            "\nERROR: Could not read PDF."
        )

        print(
            f"{exc}"
        )

        sys.exit(1)

    print(
        f"Total pages: {total_pages}"
    )

    print(
        "\nExtraction mode:"
    )

    print(
        "1. Single page range"
    )

    print(
        "2. Multiple page ranges"
    )

    while True:

        mode = input(
            "\nChoose extraction mode: "
        ).strip()

        if mode in ("1", "2"):
            break

        print(
            "Please choose 1 or 2."
        )


    if mode == "1":
        number_of_ranges = 1

    else:
        number_of_ranges = (
            ask_number_of_ranges()
        )


    ranges: list[dict] = []

    for range_number in range(
        1,
        number_of_ranges + 1,
    ):

        start_page, end_page = (
            ask_page_range(
                total_pages=total_pages,
                range_number=range_number,
            )
        )

        section = ask_section()

        ranges.append(
            {
                "start_page": start_page,
                "end_page": end_page,
                "section": section,
            }
        )


    tier = ask_tier()


    output_mode = ask_output_mode(
        number_of_ranges
    )


    display_ranges(
        ranges
    )

    print(
        f"\nOutput mode: "
        f"{output_mode}"
    )

    print(
        f"Tier: "
        f"{tier}"
    )


    if not confirm_extraction():

        print(
            "\nExtraction cancelled."
        )

        return


    run_extraction(
        pdf_path=pdf_path,
        ranges=ranges,
        output_mode=output_mode,
        tier=tier,
    )


if __name__ == "__main__":
    main()

