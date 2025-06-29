# app/core/llm_service.py

import os
import json
from typing import Dict, Any, List
import re  # ← aggiungi questa riga
import httpx
from app.models.documents import ChatRequest

# -------------------------------------------------------------------
# CONFIGURAZIONE OPENROUTER
# -------------------------------------------------------------------
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "mistralai/mistral-small-3.2-24b-instruct:free"  # o un altro modello gratuito a tua scelta

# -------------------------------------------------------------------
# PROMPT TEMPLATE PER CHAT INTERATTIVA
# -------------------------------------------------------------------
CHAT_PROMPT_TEMPLATE = """
Sei un assistente legale specializzato nell'analisi di contratti per Cassa Depositi e Prestiti (CDP).
Ti è stato fornito il risultato di un'analisi comparativa tra un contratto standard di CDP e una versione modificata da un'azienda cliente.
Il tuo compito è rispondere alle domande dell'utente basandoti ESCLUSIVAMENTE sul contesto fornito. Non inventare informazioni.

--- INIZIO CONTESTO ANALISI ---
{analysis_context}
--- FINE CONTESTO ANALISI ---

Domanda dell'utente: "{question}"

Rispondi in modo chiaro e conciso.
"""


def _format_context_for_chat(context: List[Dict[str, Any]]) -> str:
    output = ""
    for clause in context:
        output += f"Clausola: {clause.get('clause_id')}\n"
        output += f"Stato: {clause.get('status')}\n"
        if clause.get("status") in ["modified", "new"] and clause.get("llm_analysis"):
            output += f"  - Raccomandazione IA: {clause['llm_analysis'].get('recommendation')}\n"
            output += (
                f"  - Riepilogo Modifica: {clause['llm_analysis'].get('summary')}\n"
            )
        output += "---\n"
    return output


# -------------------------------------------------------------------
# PROMPT ENGINEERING PER ANALISI CLAUSOLA
# -------------------------------------------------------------------
PROMPT_TEMPLATE = """
Sei un analista legale esperto per Cassa Depositi e Prestiti (CDP). Il tuo compito è analizzare una clausola contrattuale proposta da un'azienda cliente, confrontarla con lo standard CDP e fornire una raccomandazione chiara basata su precedenti storici.

**Contesto della Clausola:**
- **ID Clausola:** {clause_id}
- **Testo Standard CDP:**
{standard_text}
- **Testo Proposto dall'Azienda:**
{company_text}

**Precedenti Storici Rilevanti (Trovati tramite ricerca semantica):**
{historical_precedents}

**Il tuo Compito:**
Analizza le informazioni fornite e restituisci una risposta in formato JSON con la seguente struttura:
{{
  "summary": "Un riassunto conciso della modifica introdotta dall'azienda.",
  "risk_assessment": "Una valutazione del rischio. Indica se la modifica è simile a precedenti approvati o rifiutati. Sii specifico.",
  "recommendation": "Una raccomandazione chiara e diretta. Scegli tra: 'ACCEPT', 'REJECT', 'COUNTER-PROPOSAL'.",
  "suggested_counter_proposal": "Se la raccomandazione è 'COUNTER-PROPOSAL', fornisci qui un testo di controproposta ben formulato. Altrimenti, lascia la stringa vuota."
}}
"""


def _format_precedents_for_prompt(precedents: List[Dict[str, Any]]) -> str:
    if not precedents:
        return "Nessun precedente storico rilevante trovato."
    formatted = ""
    for i, p in enumerate(precedents, start=1):
        status = p["metadata"].get("status", "N/D").upper()
        cp = p["metadata"].get("counter_proposal_text", "")
        formatted += f"{i}. Stato: {status}\n"
        formatted += f"   Testo: \"{p['text']}\"\n"
        if status == "REJECTED" and cp:
            formatted += f'   Controproposta CDP: "{cp}"\n'
    return formatted


# -------------------------------------------------------------------
# FUNZIONE COMUNE PER CHIAMARE OPENROUTER
# -------------------------------------------------------------------
# -------------------------------------------------------------------
# FUNZIONE COMUNE PER CHIAMARE OPENROUTER (versione migliorata)
# -------------------------------------------------------------------
async def _call_openrouter(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024,
    }
    print("DEBUG openrouter request:", payload)  # log payload
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            url=OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "Referer": "https://tuosito.com",
                "X-Title": "istruttoria-cdp",
            },
            json=payload,
        )
        # se status!=200, logga il corpo di risposta per capire l'errore
        if resp.status_code != 200:
            print("ERROR openrouter response code:", resp.status_code)
            print("ERROR openrouter response body:", resp.text)
        resp.raise_for_status()
        return resp.json()

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            url=OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "Referer": "https://tuosito.com",  # Header corretto
                "X-Title": "istruttoria-cdp",  # Opzionale per leaderboard
            },
            json={
                "model": OPENROUTER_MODEL,
                "messages": messages,
            },
        )
        resp.raise_for_status()
        return resp.json()


# -------------------------------------------------------------------
# GENERAZIONE RISPOSTA CHAT
# -------------------------------------------------------------------
async def generate_chat_response(request: ChatRequest) -> str:
    context_str = _format_context_for_chat(
        [clause.dict() for clause in request.analysis_context]
    )
    prompt = CHAT_PROMPT_TEMPLATE.format(
        analysis_context=context_str, question=request.question
    )

    try:
        data = await _call_openrouter(
            [{"role": "system", "content": ""}, {"role": "user", "content": prompt}]
        )
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print("ERROR generate_chat_response:", e)
        return "Mi dispiace, si è verificato un errore durante l'elaborazione della tua domanda."


def parse_json_output(output_str: str):
    """
    Pulisce la risposta dell'LLM da eventuali delimitatori markdown e restituisce un dizionario JSON valido.
    """
    # Rimuove eventuali blocchi ```json ... ```
    cleaned = re.sub(
        r"^```json|^```|```$", "", output_str.strip(), flags=re.MULTILINE
    ).strip()

    # Prova a caricarlo come JSON
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"Errore di parsing JSON: {e}")
        return None


# -------------------------------------------------------------------
# GENERAZIONE ANALISI CLAUSOLA
# -------------------------------------------------------------------
# dentro app/core/llm_service.py, sostituisci generate_clause_analysis con:


async def generate_clause_analysis(clause_data: Dict[str, Any]) -> Dict[str, Any]:
    # Salta le clausole non modificate o senza testo proposto dall'azienda
    if clause_data.get("status") not in ["modified", "new"] or not clause_data.get(
        "company_text"
    ):
        return {}

    # Estrai dati e crea il prompt
    standard_text = clause_data.get("standard_text", "")
    precedents_str = _format_precedents_for_prompt(
        clause_data.get("historical_precedents", [])
    )
    full_prompt = PROMPT_TEMPLATE.format(
        clause_id=clause_data["clause_id"],
        standard_text=standard_text,
        company_text=clause_data["company_text"],
        historical_precedents=precedents_str,
    )

    try:
        # Chiamata al modello via OpenRouter
        data = await _call_openrouter(
            [
                {"role": "system", "content": ""},
                {"role": "user", "content": full_prompt},
            ]
        )
        output_str = data["choices"][0]["message"]["content"]
        print("DEBUG generate_clause_analysis output_str:", output_str)

        # Parsing sicuro del JSON
        result = parse_json_output(output_str)
        if result is None:
            print("WARNING: risposta non JSON, restituisco fallback.")
            print("Non-JSON content:", output_str)
            return {
                "summary": "Risposta non valida dall'LLM.",
                "risk_assessment": "N/D",
                "recommendation": "ERROR",
                "suggested_counter_proposal": "",
            }

        return result

    except Exception as e:
        print(f"ERROR generate_clause_analysis: {e}")
        return {
            "summary": "Errore durante la generazione dell'analisi.",
            "risk_assessment": str(e),
            "recommendation": "ERROR",
            "suggested_counter_proposal": "",
        }
