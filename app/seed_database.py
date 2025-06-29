import chromadb
from sentence_transformers import SentenceTransformer
import uuid

# --- I NOSTRI DATI STORICI DI ESEMPIO ---
# In un'applicazione reale, questi dati proverrebbero da un database,
# da file Excel, o da un'analisi di vecchi contratti.
historical_clauses = [
    {
        "text": "La Società si impegna a mantenere standard etici e di reputazione in linea con le migliori pratiche di mercato e con i principi di Cassa Depositi e Prestiti.",
        "metadata": {
            "original_clause_id": "231 - Reputazione",
            "version": "Standard Corrente",
            "status": "approved",
        },
    },
    {
        "text": "La Società si impegna a mantenere standard etici e di reputazione in linea con le migliori pratiche del settore di riferimento.",
        "metadata": {
            "original_clause_id": "231 - Reputazione",
            "version": "A - Approvata 2023",
            "status": "approved",
        },
    },
    {
        "text": "La Società dichiara di aderire ai principi etici indicati nel proprio codice interno.",
        "metadata": {
            "original_clause_id": "231 - Reputazione",
            "version": "B - Rifiutata 2022",
            "status": "rejected",
            "counter_proposal_text": "La clausola deve fare esplicito riferimento agli standard di CDP. Proposta di modifica: 'La Società dichiara di aderire ai principi etici indicati nel proprio codice interno e agli standard di reputazione di CDP.'",
        },
    },
    {
        "text": "La Società può procedere alla distribuzione di dividendi e riserve solo previa autorizzazione scritta di CDP.",
        "metadata": {
            "original_clause_id": "8 - Distribuzioni",
            "version": "Standard Corrente",
            "status": "approved",
        },
    },
    {
        "text": "La Società può procedere alla distribuzione di dividendi e riserve, a condizione che il debt service coverage ratio (DSCR) si mantenga superiore a 1.2x.",
        "metadata": {
            "original_clause_id": "8 - Distribuzioni",
            "version": "C - Approvata 2024",
            "status": "approved",
        },
    },
]


def setup_database():
    print(
        "Inizializzazione del modello di embedding (potrebbe richiedere un download la prima volta)..."
    )
    # Usiamo un modello multilingua efficiente, ottimo per iniziare.
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

    print("Inizializzazione del client del database vettoriale ChromaDB...")
    # Creiamo un client che salverà i dati su disco nella cartella 'cdb_storage'
    client = chromadb.PersistentClient(path="cdb_storage")

    # Otteniamo o creiamo una "collection" (simile a una tabella in SQL)
    # Usiamo get_or_create per evitare errori se lo script viene eseguito più volte.
    collection = client.get_or_create_collection(
        name="historical_clauses",
        metadata={
            "hnsw:space": "cosine"
        },  # Usiamo la distanza coseno, ottima per similarità testuale
    )

    print(
        f"Popolamento del database con {len(historical_clauses)} clausole storiche..."
    )

    # Prepariamo i dati per l'inserimento in blocco
    ids = [
        str(uuid.uuid4()) for _ in historical_clauses
    ]  # Creiamo un ID unico per ogni clausola
    texts = [item["text"] for item in historical_clauses]
    metadatas = [item["metadata"] for item in historical_clauses]

    # Generiamo gli embeddings per tutti i testi in un unico batch (molto efficiente)
    embeddings = model.encode(texts).tolist()

    # Aggiungiamo i dati alla collection
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,  # ChromaDB memorizza anche il testo originale
        metadatas=metadatas,
    )

    print("-" * 50)
    print("✅ Database popolato con successo!")
    print(f"Dati salvati in: cdb_storage/")
    print(f"Numero di elementi nella collection: {collection.count()}")
    print("-" * 50)


if __name__ == "__main__":
    setup_database()
