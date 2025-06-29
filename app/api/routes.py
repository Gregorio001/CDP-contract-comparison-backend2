import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Annotated, List
from pathlib import Path

# Importiamo il nostro nuovo modello di risposta
from app.models.documents import AnalyzedClause
from app.core import processor
from app.models.documents import (
    AnalyzedClause,
    ChatRequest,
    ChatResponse,
)  # Aggiorna l'import
from app.core import processor, llm_service  # Aggiorna l'import

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def handle_chat(request: ChatRequest):
    """
    Endpoint per la chat contestuale sull'analisi di un documento.
    """
    answer = await llm_service.generate_chat_response(request)
    return ChatResponse(answer=answer)


@router.post("/analyze", response_model=List[AnalyzedClause])
@router.post("/analyze", response_model=List[AnalyzedClause])
async def analyze_document(
    standard_id: Annotated[str, Form()],
    company_document: Annotated[UploadFile, File()],
):
    # 1. Controllo estensione
    if not company_document.filename.lower().endswith((".docx", ".pdf")):
        raise HTTPException(
            status_code=400, detail="Formato file non supportato. Usare .docx o .pdf"
        )

    try:
        # —––– DEBUG: leggi e poi stampa
        company_content = await company_document.read()
        print(f"File ricevuto: {company_document.filename}")
        print(f"Dimensione contenuto: {len(company_content)} bytes")

        # 2. Estrai testo dal file
        company_raw_text = processor.parse_document_content(
            company_document.filename, company_content
        )
        company_clauses = processor.segment_text_into_clauses(company_raw_text)

        # 3. Trova lo standard: prova .docx poi .pdf
        std_path: Optional[Path] = None
        for ext in (".pdf", ".docx"):
            p = Path("standards") / f"{standard_id}{ext}"
            if p.exists():
                std_path = p
                break

        if std_path is None:
            raise HTTPException(
                status_code=404,
                detail=f"Nessun documento standard trovato con ID '{standard_id}'",
            )

        # DEBUG standard
        print(f"Usato standard: {std_path}")

        # 4. Leggi e processa lo standard
        standard_content = std_path.read_bytes()
        standard_raw_text = processor.parse_document_content(
            std_path.name, standard_content
        )
        standard_clauses = processor.segment_text_into_clauses(standard_raw_text)

        print(
            f"Clausole azienda: {len(company_clauses)}, "
            f"Clausole standard: {len(standard_clauses)}"
        )

        # 5. Confronta e genera risultati
        analysis_results = await processor.compare_clauses(
            company_clauses, standard_clauses
        )
        return analysis_results

    except HTTPException:
        # rilancialo (404 per standard mancante, 400 per estensione)
        raise
    except Exception as e:
        # mostra lo stack nel log e torna 500 con dettaglio
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Errore durante l'analisi: {e}")
