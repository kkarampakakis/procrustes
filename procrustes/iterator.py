# ------------------------------------------------------------------------------------------
# iterator
# ------------------------------------------------------------------------------------------

import pickle
from io import BytesIO
from pypdf import PdfReader, PdfWriter
from pathlib import Path
from dataclasses import dataclass
from typing import List

from .prompt_gateway import PromptGateway

# ------------------------------------------------------------------------------------------

PICKLE_NAME = "procrustean_pickle.pkl"

# ------------------------------------------------------------------------------------------

@dataclass
class PDFPageEntry:
    pdf_name: str
    pdf_path: Path
    page_number: int   # 1-based
    page_index: int    # 0-based

# ------------------------------------------------------------------------------------------

class Iterator:

    def __init__(self, gate: PromptGateway):
        self.gate = gate

        print("Building metadata list...")
        self.pages = build_metadata_list()
        self.i = 0
        self.filled_entries = {}
        
        for x in self.gate.settings["general"]["entries"]:
            self.filled_entries.update({x: []})

        
    def save_as_pickle(self):
        with open(PICKLE_NAME, "wb") as f:
            pickle.dump(self, f)


    def resume_inquiry(self):
        length = len(self.pages)

        if length == 0:
            print("No PDF files found.")
            return

        for i in range(self.i, length):
            print(f"{(self.i / length) * 100:.2f}% completed")

            temp_entries = self.gate.inquiror.invoke(metadata_to_bytes(self.pages[i]))

            for key, value in temp_entries.items():
                if value is None:
                    continue

                value = str(value).strip()

                if not value or value == "-":
                    continue

                if key in self.filled_entries:
                    exists_already = False

                    for x in self.filled_entries[key]:
                        if value.lower() == x.lower():
                            exists_already = True
                            break

                    if not exists_already:
                        self.filled_entries[key].append(value)

                else:
                    self.filled_entries[key] = [value]
        
            self.i += 1
            self.save_as_pickle()
        
# ------------------------------------------------------------------------------------------

def build_metadata_list(folder: str | Path = ".") -> List[PDFPageEntry]:
    """
    Scan all PDFs in the folder and return a list of all pages.
    One list item = one page in one PDF.
    """
    folder = Path(folder)
    page_list: List[PDFPageEntry] = []

    for pdf_path in sorted(folder.glob("*.pdf")):
        try:
            reader = PdfReader(pdf_path)
            for i, _page in enumerate(reader.pages):
                page_list.append(
                    PDFPageEntry(
                        pdf_name=pdf_path.name,
                        pdf_path=pdf_path,
                        page_number=i + 1,
                        page_index=i,
                    )
                )
        except Exception as e:
            print(f"Skipping {pdf_path.name}: {e}")

    return page_list

# ------------------------------------------------------------------------------------------

def metadata_to_bytes(entry: PDFPageEntry) -> bytes:
    """
    Convert one PDFPageEntry into a one-page PDF as raw bytes.
    """
    reader = PdfReader(entry.pdf_path)
    writer = PdfWriter()
    writer.add_page(reader.pages[entry.page_index])

    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()

# ------------------------------------------------------------------------------------------
