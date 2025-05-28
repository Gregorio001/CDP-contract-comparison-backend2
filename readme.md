# Backend per Confronto Contratti CDP

Questo backend fornisce un'API per confrontare due documenti contrattuali (uno standard e uno proposto)
e identificare le differenze. Utilizza Azure OpenAI per l'analisi del testo e (concettualmente)
PostgreSQL con pgVector per la gestione e la ricerca di variazioni storiche delle clausole.

## Prerequisiti

- Python 3.9+
- pip (Python package installer)
- Un'istanza di PostgreSQL con l'estensione pgVector installata e configurata (opzionale per il funzionamento base senza storico, ma necessario per la feature completa).
- Accesso a Azure OpenAI Service con deployment per embeddings e chat models.

## Setup Ambiente Locale

1.  **Clona il repository (se applicabile) o crea la struttura di file come descritto.**

2.  **Crea e attiva un ambiente virtuale Python:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Su Windows: venv\Scripts\activate
    ```

3.  **Installa le dipendenze:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configura le variabili d'ambiente:**
    Crea un file `.env` nella directory principale del progetto (`cdp_contract_backend/`)
    e riempilo con le tue credenziali e i tuoi endpoint, come mostrato nell'esempio del file `.env`.

5.  **(Opzionale) Setup PostgreSQL e pgVector:**
    - Assicurati che PostgreSQL sia in esecuzione.
    - Connettiti al tuo database PostgreSQL e installa l'estensione pgVector:
      ```sql
      CREATE EXTENSION IF NOT EXISTS vector;
      ```
    - Crea la tabella per le clausole (vedi commenti in `app/crud.py` per una possibile struttura):
      ```sql
      CREATE TABLE IF NOT EXISTS contract_clauses (
          id SERIAL PRIMARY KEY,
          clause_text TEXT NOT NULL,
          embedding VECTOR(1536), -- La dimensione dipende dal modello di embedding (es. 1536 per text-embedding-ada-002)
          document_type VARCHAR(50), -- 'standard', 'historical_variant'
          original_clause_id INTEGER REFERENCES contract_clauses(id),
          source_contract_id VARCHAR(100),
          version_notes TEXT,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
      -- Crea un indice per la ricerca di similarità (esempio con IVFFlat, HNSW è un'altra opzione)
      -- CREATE INDEX ON contract_clauses USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
      -- Oppure:
      -- CREATE INDEX ON contract_clauses USING hnsw (embedding vector_cosine_ops);
      ```
    - Dovrai popolare questa tabella con le clausole standard e le loro variazioni storiche, includendo i loro embeddings. Questo processo di popolamento è separato dalla logica di confronto dell'API.

## Esecuzione Locale

Per avviare il server backend localmente:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 7071