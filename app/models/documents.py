from pydantic import BaseModel
from typing import List, Optional, Literal, Dict, Any


class Clause(BaseModel):
    """Rappresenta una singola clausola estratta da un documento."""

    clause_id: str
    text: str


class HistoricalPrecedent(BaseModel):
    """Rappresenta un precedente storico trovato nel Vector Store."""

    historical_id: str
    text: str
    metadata: Dict[str, Any]
    similarity_score: float


class AnalyzedClause(BaseModel):
    clause_id: str
    status: Literal["unchanged", "modified", "new", "deleted"]
    company_text: Optional[str] = None
    standard_text: Optional[str] = None
    historical_precedents: List[HistoricalPrecedent] = []
    llm_analysis: Optional[Dict[str, Any]] = None  # <-- AGGIUNGI QUESTO CAMPO


class DocumentAnalysisRequest(BaseModel):
    """Richiesta di analisi di un documento."""

    company_document_content: bytes  # Contenuto del file caricato
    standard_document_id: str  # ID dello standard con cui confrontare


class DocumentAnalysisResponse(BaseModel):
    """Risposta con l'analisi del documento."""

    message: str
    modified_clauses: List[Clause]


class ChatRequest(BaseModel):
    """Richiesta per l'endpoint di chat."""

    question: str
    analysis_context: List[
        AnalyzedClause
    ]  # Il frontend invierà il contesto dell'analisi


class ChatResponse(BaseModel):
    """Risposta dall'endpoint di chat."""

    answer: str
