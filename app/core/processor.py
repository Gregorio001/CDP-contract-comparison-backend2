import io
import re
from app.config import HUGGINGFACE_API_KEY
from typing import List, IO
from docx import Document as DocxDocument
from pypdf import PdfReader
from app.models.documents import Clause
from app.core import vector_store
import asyncio  # Aggiungi questo import
from app.core import vector_store, llm_service  # Aggiungi llm_service


def _extract_text_from_docx(file_stream: IO[bytes]) -> str:
    """Estrae il testo da un file DOCX."""
    document = DocxDocument(file_stream)
    full_text = [para.text for para in document.paragraphs]
    return "\n".join(full_text)


def _extract_text_from_pdf(file_stream: IO[bytes]) -> str:
    """Estrae il testo da un file PDF."""
    reader = PdfReader(file_stream)
    full_text = [page.extract_text() for page in reader.pages if page.extract_text()]
    return "\n".join(full_text)


def parse_document_content(filename: str, content: bytes) -> str:
    """
    Funzione di alto livello per orchestrare l'estrazione del testo
    in base all'estensione del file.
    """
    file_stream = io.BytesIO(content)
    if filename.endswith(".docx"):
        return _extract_text_from_docx(file_stream)
    elif filename.endswith(".pdf"):
        return _extract_text_from_pdf(file_stream)
    else:
        # Questo caso è già gestito a livello di API, ma è buona norma averlo.
        raise ValueError("Formato file non supportato.")


def segment_text_into_clauses(text: str) -> List[Clause]:
    """
    Suddivide un testo lungo in una lista di clausole, usando regex
    per identificare gli inizi delle clausole (es. "Art. 1", "1.2.3").
    """
    # Questo pattern regex cerca righe che iniziano con:
    # - "Art." o "Articolo" seguito da un numero (es. Art. 1)
    # - "Clausola" seguita da un numero (es. Clausola 231)
    # - Numerazione a più livelli (es. 1., 1.1., 1.2.3.)
    # re.MULTILINE fa sì che ^ corrisponda all'inizio di ogni riga.
    pattern = re.compile(
        r"^\s*(Art(?:icolo)?\.?\s*\d+|Clausola\s*\d+|\d+(?:\.\d+)*\.)\s+",
        re.IGNORECASE | re.MULTILINE,
    )

    clauses = []

    # Troviamo tutti i titoli delle clausole che matchano il pattern
    titles = pattern.findall(text)
    # Usiamo il pattern per splittare il testo. Il risultato saranno i corpi delle clausole.
    bodies = pattern.split(text)[
        1:
    ]  # Ignoriamo il primo elemento che è il testo prima della prima clausola

    if not titles:
        # Se nessuna clausola è stata trovata, consideriamo l'intero documento come un'unica clausola
        return [Clause(clause_id="documento_intero", text=text.strip())]

    for i, title in enumerate(titles):
        clause_id = title.strip()
        clause_text = bodies[i].strip() if i < len(bodies) else ""
        clauses.append(Clause(clause_id=clause_id, text=clause_text))

    return clauses


# Modifica la funzione compare_clauses per renderla asincrona
async def compare_clauses(
    company_clauses: List[Clause], standard_clauses: List[Clause]
) -> List[dict]:
    standard_map = {c.clause_id.lower().strip(): c.text for c in standard_clauses}
    company_map = {c.clause_id.lower().strip(): c.text for c in company_clauses}
    all_ids = sorted(list(set(standard_map.keys()) | set(company_map.keys())))

    final_results = []
    tasks_for_llm = []

    for clause_id in all_ids:
        # ... (la logica per determinare lo status rimane identica a prima) ...
        standard_text = standard_map.get(clause_id)
        company_text = company_map.get(clause_id)

        analysis = {"clause_id": clause_id.upper(), "historical_precedents": []}
        # ... (riempi analysis con status, testi, e precedenti come nello Step 4) ...

        # Identifica lo stato della clausola (unchanged, modified, new, deleted)
        status = ""
        if company_text and standard_text:
            status = (
                "modified"
                if company_text.strip() != standard_text.strip()
                else "unchanged"
            )
        elif company_text and not standard_text:
            status = "new"
        elif standard_text and not company_text:
            status = "deleted"

        analysis["status"] = status
        analysis["company_text"] = company_text
        analysis["standard_text"] = standard_text

        # Se la clausola è modificata o nuova, la prepariamo per l'LLM
        if status in ["modified", "new"]:
            analysis["historical_precedents"] = vector_store.find_similar_clauses(
                company_text
            )
            tasks_for_llm.append(
                analysis
            )  # Aggiungi l'intera analisi alla lista dei task
        else:
            final_results.append(
                analysis
            )  # Le clausole non modificate vanno direttamente nei risultati

    # Esegui le analisi LLM in parallelo per la massima efficienza
    if tasks_for_llm:
        llm_analyses = await asyncio.gather(
            *(llm_service.generate_clause_analysis(task) for task in tasks_for_llm)
        )
        # Unisci i risultati dell'LLM con i dati delle clausole
        for i, task_data in enumerate(tasks_for_llm):
            task_data["llm_analysis"] = llm_analyses[i]
            final_results.append(task_data)

    # Ordina i risultati finali per ID di clausola
    final_results.sort(key=lambda x: x["clause_id"])
    return final_results
