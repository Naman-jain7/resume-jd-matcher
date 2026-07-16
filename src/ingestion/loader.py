import pdfplumber

# ====================== STREAMLIT LOADER (pdfplumber) ======================

def load_pdf_streamlit(file_obj) -> str:
    """
    Extract structured text from a PDF using pdfplumber.

    Designed for Streamlit's file uploader (returns a BytesIO-compatible object).
    Preserves spatial layout by grouping words into visual line-blocks based on
    their vertical (y) position. Tables are extracted as structured data and
    rendered as markdown tables inline at the correct page position.

    Args:
        file_obj: Streamlit UploadedFile / any BytesIO-compatible object.

    Returns:
        A single string with markdown-like structural markers:
          - "## Page N" header per page
          - Tables rendered as markdown (| col | col |)
          - Text blocks reconstructed from spatial word groupings
    """
    output_pages = []

    with pdfplumber.open(file_obj) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            page_parts = []  # ordered list of (y_top, content_string) tuples  # noqa: F841

            # ------------------------------------------------------------------
            # 1. Extract tables and record their bounding-box y-ranges so we
            #    can skip words that fall inside a table cell (avoid duplication)
            # ------------------------------------------------------------------
            table_bboxes = []   # list of (y0, y1) for each table
            table_blocks  = []  # list of (y_top, markdown_string) for each table

            tables = page.extract_tables()
            table_settings_list = page.find_tables()  # pdfplumber Table objects

            for tbl_obj, tbl_data in zip(table_settings_list, tables):
                bbox = tbl_obj.bbox          # (x0, y0, x1, y1)
                y0, y1 = bbox[1], bbox[3]
                table_bboxes.append((y0, y1))

                # Build markdown table from raw 2-D list
                if not tbl_data or not tbl_data[0]:
                    continue

                # Treat first row as header
                header = tbl_data[0]
                rows   = tbl_data[1:]

                # Sanitise cells: replace None / newlines
                def _clean(cell):
                    if cell is None:
                        return ""
                    return str(cell).replace("\n", " ").strip()

                header_md  = "| " + " | ".join(_clean(c) for c in header) + " |"
                divider_md = "| " + " | ".join("---" for _ in header) + " |"
                row_mds    = [
                    "| " + " | ".join(_clean(c) for c in row) + " |"
                    for row in rows
                ]
                md_table = "\n".join([header_md, divider_md] + row_mds)
                table_blocks.append((y0, md_table))

            # ------------------------------------------------------------------
            # 2. Extract words and skip any that live inside a table bbox
            # ------------------------------------------------------------------
            words = page.extract_words(
                x_tolerance=3,       # words within 3pt horizontally → same token
                y_tolerance=3,       # words within 3pt vertically   → same line
                keep_blank_chars=False,
                use_text_flow=True,  # respect reading-order flow
            )

            def _in_table(word):
                wy0, wy1 = word["top"], word["bottom"]
                for (ty0, ty1) in table_bboxes:
                    if wy0 >= ty0 - 2 and wy1 <= ty1 + 2:
                        return True
                return False

            filtered_words = [w for w in words if not _in_table(w)]

            # ------------------------------------------------------------------
            # 3. Group words into visual lines using y-position proximity
            #    (words whose "top" values are within LINE_TOL pts → same line)
            # ------------------------------------------------------------------
            LINE_TOL = 4   # points; tweak if lines merge / split incorrectly

            lines: dict[float, list] = {}   # anchor_y → [word, ...]
            anchor_ys: list[float]   = []

            for word in filtered_words:
                y = word["top"]
                matched = None
                for ay in anchor_ys:
                    if abs(y - ay) <= LINE_TOL:
                        matched = ay
                        break
                if matched is None:
                    anchor_ys.append(y)
                    lines[y] = [word]
                else:
                    lines[matched].append(word)

            # Sort anchor_ys top → bottom, then sort words left → right per line
            text_blocks = []
            for ay in sorted(anchor_ys):
                line_words = sorted(lines[ay], key=lambda w: w["x0"])
                line_text  = " ".join(w["text"] for w in line_words)
                text_blocks.append((ay, line_text))

            # ------------------------------------------------------------------
            # 4. Merge text blocks and table blocks in top-to-bottom order
            # ------------------------------------------------------------------
            all_blocks = text_blocks + table_blocks
            all_blocks.sort(key=lambda b: b[0])

            page_content = "\n".join(content for _, content in all_blocks)

            # ------------------------------------------------------------------
            # 5. Add page header and collect
            # ------------------------------------------------------------------
            output_pages.append(f"## Page {page_num}\n\n{page_content}")

    return "\n\n".join(output_pages)
