import io
import fitz  # PyMuPDF
from docx import Document as DocxDocument


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Estrae il testo da un file PDF."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text += page.get_text()
    return text


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Estrae il testo da un file DOCX."""
    doc = DocxDocument(io.BytesIO(file_bytes))
    text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    return text


def extract_text(filename: str, file_bytes: bytes) -> str:
    """Estrae il testo da file PDF o DOCX."""
    if filename.lower().endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif filename.lower().endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    else:
        # Fallback per altri tipi di file di testo, se necessario
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError(
                "Unsupported file type or encoding. Please use PDF or DOCX."
            )
