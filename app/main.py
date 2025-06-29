from fastapi import FastAPI
from app.api import routes
from app.config import HUGGINGFACE_API_KEY
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="CDP Financial Analysis API",
    description="API per l'analisi automatica dei contratti finanziari.",
    version="1.0.0",
)


origins = [
    "http://localhost:3000",
    "http://127.0.0.1:8000",
    # aggiungi altre origini se serve
]
# --- Setup CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in prod sostituisci "*" con la lista dei tuoi domini!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Includiamo le rotte definite nel nostro modulo `routes`
app.include_router(routes.router, prefix="/api/v1", tags=["Analysis"])


@app.get("/")
def read_root():
    return {"status": "API Server is running"}
