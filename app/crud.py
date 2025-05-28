from typing import List
import psycopg2
from app.core.config import settings

# from langchain_openai import AzureOpenAIEmbeddings # Per embeddings
# from pgvector.psycopg2 import register_vector # Per registrare il tipo vector con psycopg2

# Placeholder per connessione DB e embeddings
# Per una reale implementazione, inizializza AzureOpenAIEmbeddings qui
# embeddings_model = None
# if settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME:
#     embeddings_model = AzureOpenAIEmbeddings(
#         azure_deployment=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME,
#         chunk_size=1 # o altro valore a seconda del modello
#     )


def get_db_connection():
    if not settings.DATABASE_URL:
        return None
    try:
        conn = psycopg2.connect(settings.DATABASE_URL)
        # register_vector(conn) # Abilita pgvector per questa connessione
        return conn
    except psycopg2.OperationalError as e:
        print(f"Errore connessione DB: {e}")
        return None


async def get_historical_variations(
    standard_clause_snippet: str, limit: int = 4
) -> List[str]:
    """
    Recupera variazioni storiche di una clausola da pgVector.
    Questa è una versione MOCK. La vera implementazione userebbe embeddings e query a pgVector.
    """
    print(
        f"Ricerca variazioni storiche per: '{standard_clause_snippet[:50]}...' (mock)"
    )
    # conn = get_db_connection()
    # if not conn or not embeddings_model:
    #     print("Connessione DB o modello embeddings non disponibile per ricerca storica.")
    #     return [
    #         f"Opzione storica A (mock per '{standard_clause_snippet[:20]}...')",
    #         f"Opzione storica B (mock per '{standard_clause_snippet[:20]}...')",
    #     ]

    # try:
    #     snippet_embedding = embeddings_model.embed_query(standard_clause_snippet)
    #     with conn.cursor() as cur:
    #         # Assumendo una tabella 'contract_clauses' con colonna 'embedding' e 'clause_text'
    #         # E un 'original_clause_id' o un modo per identificare la clausola standard
    #         cur.execute(
    #             "SELECT clause_text FROM contract_clauses ORDER BY embedding <=> %s::vector LIMIT %s",
    #             (snippet_embedding, limit)
    #         )
    #         results = [row[0] for row in cur.fetchall()]
    #         return results
    # except Exception as e:
    #     print(f"Errore durante la query a pgVector: {e}")
    #     return [f"Errore recupero storico: {e}"]
    # finally:
    #     if conn:
    #         conn.close()

    # Mocked response if DB/embeddings are not fully set up
    return [
        f"Opzione storica A (mock per '{standard_clause_snippet[:30]}...')",
        f"Opzione storica B (mock per '{standard_clause_snippet[:30]}...')",
        f"Opzione storica C (mock per '{standard_clause_snippet[:30]}...')",
    ]


# Funzione per popolare il DB (da eseguire separatamente, non parte dell'API di confronto)
# async def store_clause_with_embedding(clause_text: str, document_type: str = "standard", original_clause_id: Optional[int] = None):
#     conn = get_db_connection()
#     if not conn or not embeddings_model:
#         print("Connessione DB o modello embeddings non disponibile per storage.")
#         return

#     try:
#         embedding = embeddings_model.embed_query(clause_text)
#         with conn.cursor() as cur:
#             cur.execute(
#                 """
#                 INSERT INTO contract_clauses (clause_text, embedding, document_type, original_clause_id)
#                 VALUES (%s, %s, %s, %s) RETURNING id;
#                 """,
#                 (clause_text, embedding, document_type, original_clause_id)
#             )
#             clause_id = cur.fetchone()[0]
#             conn.commit()
#             print(f"Clausola '{clause_text[:30]}...' memorizzata con ID: {clause_id}")
#     except Exception as e:
#         print(f"Errore durante il salvataggio della clausola: {e}")
#         conn.rollback()
#     finally:
#         if conn:
#             conn.close()
