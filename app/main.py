from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import (
    CORSMiddleware,
)  # Per CORS se il frontend è su un dominio diverso
from app.api_models import ComparisonResponse
from app.services import compare_documents_logic
from app.core.config import settings  # Per accedere alle config se necessario qui

app = FastAPI(title="Contract Comparison API")

# Configurazione CORS (adatta alle tue esigenze)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],  # O specifica i domini del frontend es. ["http://localhost:xxxx"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    if not all(
        [
            settings.AZURE_OPENAI_API_KEY,
            settings.AZURE_OPENAI_ENDPOINT,
            settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME,
            settings.AZURE_OPENAI_CHAT_DEPLOYMENT_NAME,
        ]
    ):
        print(
            "ATTENZIONE: Una o più variabili d'ambiente Azure OpenAI non sono impostate."
        )
        print("L'analisi LLM e le funzionalità di embedding potrebbero non funzionare.")


@app.post("/api/compare_documents", response_model=ComparisonResponse)
async def compare_documents_endpoint(
    model_document: UploadFile = File(...), proposal_document: UploadFile = File(...)
):
    """
    Endpoint per confrontare due documenti (modello standard e proposta).
    Riceve due file (model_document, proposal_document) e restituisce
    il testo completo della proposta con un elenco delle differenze identificate.
    """
    if not model_document.filename.endswith((".docx", ".pdf")):
        raise HTTPException(
            status_code=400, detail="Il file modello deve essere .docx o .pdf"
        )
    if not proposal_document.filename.endswith((".docx", ".pdf")):
        raise HTTPException(
            status_code=400, detail="Il file proposta deve essere .docx o .pdf"
        )

    try:
        full_proposal_text, diffs = await compare_documents_logic(
            model_document, proposal_document
        )

        return ComparisonResponse(
            full_proposal_text=full_proposal_text,
            differences=diffs,
            highlighted_proposal_pdf_url=None,  # Non implementato in questo backend
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # Log dell'eccezione per debug
        print(f"Errore imprevisto durante il confronto: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Errore interno del server: {e}")


if __name__ == "__main__":
    import uvicorn

    # Per eseguire localmente: uvicorn app.main:app --reload --port 7071
    # Nota: L'URL base sarà http://localhost:7071, quindi l'endpoint sarà http://localhost:7071/api/compare_documents
    uvicorn.run(app, host="0.0.0.0", port=7071)
