import difflib
from typing import Tuple, List, Dict, Any
from fastapi import UploadFile
from app.utils.text_utils import extract_text
from app.api_models import DifferenceModel
from app.core.config import settings
from app.crud import get_historical_variations

from langchain_openai import AzureChatOpenAI  # , AzureOpenAIEmbeddings

# from langchain.text_splitter import RecursiveCharacterTextSplitter # Per chunking più avanzato
# from langchain.chains.summarize import load_summarize_chain # Per analisi LLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


# Inizializza LLM e Embeddings da Azure OpenAI via Langchain
llm = None
if settings.AZURE_OPENAI_CHAT_DEPLOYMENT_NAME:
    llm = AzureChatOpenAI(
        azure_deployment=settings.AZURE_OPENAI_CHAT_DEPLOYMENT_NAME,
        temperature=0.1,  # Bassa per analisi fattuale
        max_tokens=500,
    )

# embeddings_model = None # Già definito concettualmente in crud.py
# if settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME:
#     embeddings_model = AzureOpenAIEmbeddings(
#         azure_deployment=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME,
#         chunk_size=1 # Adatta se necessario
#     )


async def analyze_difference_with_llm(
    standard_snippet: str, proposal_snippet: str, diff_type: str
) -> Dict[str, Any]:
    """
    Utilizza Azure OpenAI (LLM) per analizzare una differenza e fornire una descrizione.
    """
    if not llm:
        return {"description": "LLM non configurato. Analisi non disponibile."}

    if diff_type == "MODIFIED":
        prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Sei un assistente legale specializzato nell'analisi di modifiche contrattuali. Confronta la clausola standard con quella proposta e descrivi concisamente le differenze chiave. Evidenzia impatti potenziali se evidenti. Rispondi in italiano.",
                ),
                (
                    "user",
                    f"Clausola Standard:\n---\n{standard_snippet}\n---\n\nClausola Proposta:\n---\n{proposal_snippet}\n---\n\nDescrivi le modifiche:",
                ),
            ]
        )
    elif diff_type == "ADDED":
        prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Sei un assistente legale specializzato nell'analisi di clausole contrattuali. Descrivi brevemente il contenuto e lo scopo della seguente clausola aggiunta. Rispondi in italiano.",
                ),
                (
                    "user",
                    f"Clausola Aggiunta:\n---\n{proposal_snippet}\n---\n\nDescrivi la clausola:",
                ),
            ]
        )
    else:  # DELETED_FROM_STANDARD or other types
        return {
            "description": f"Tipo di differenza '{diff_type}' non gestito per l'analisi LLM dettagliata."
        }

    chain = prompt_template | llm | StrOutputParser()

    try:
        description = await chain.ainvoke(
            {}
        )  # {} perché i parametri sono già nel template formattato
        return {"description": description.strip()}
    except Exception as e:
        print(f"Errore durante l'analisi LLM: {e}")
        return {"description": f"Errore analisi LLM: {e}"}


async def compare_documents_logic(
    model_file: UploadFile, proposal_file: UploadFile
) -> Tuple[str, List[DifferenceModel]]:
    """
    Logica principale per confrontare due documenti.
    """
    model_bytes = await model_file.read()
    proposal_bytes = await proposal_file.read()

    standard_text = extract_text(model_file.filename, model_bytes)
    proposal_text = extract_text(proposal_file.filename, proposal_bytes)

    differences: List[DifferenceModel] = []

    # Utilizzo di difflib.SequenceMatcher per un confronto testuale
    # Questo è un approccio base. Per "riconoscere la medesima clausola sebbene scritta con wording differente"
    # servirebbe un approccio più avanzato basato su embeddings per allineare le clausole prima del diff.

    sequence_matcher = difflib.SequenceMatcher(
        None,
        standard_text.splitlines(keepends=True),
        proposal_text.splitlines(keepends=True),
    )
    # Convertiamo gli indici di riga in indici di carattere

    # Mappatura degli indici di riga a indici di carattere per standard_text
    std_line_starts = [0] * (len(standard_text.splitlines(keepends=True)) + 1)
    current_pos = 0
    for i, line in enumerate(standard_text.splitlines(keepends=True)):
        std_line_starts[i + 1] = current_pos + len(line)
        current_pos += len(line)
    if not standard_text.splitlines(keepends=True):  # caso testo vuoto
        std_line_starts = [0]

    # Mappatura degli indici di riga a indici di carattere per proposal_text
    prop_line_starts = [0] * (len(proposal_text.splitlines(keepends=True)) + 1)
    current_pos = 0
    for i, line in enumerate(proposal_text.splitlines(keepends=True)):
        prop_line_starts[i + 1] = current_pos + len(line)
        current_pos += len(line)
    if not proposal_text.splitlines(keepends=True):  # caso testo vuoto
        prop_line_starts = [0]

    for tag, i1, i2, j1, j2 in sequence_matcher.get_opcodes():
        standard_snippet_lines = standard_text.splitlines(keepends=True)[i1:i2]
        proposal_snippet_lines = proposal_text.splitlines(keepends=True)[j1:j2]

        standard_snippet = "".join(standard_snippet_lines)
        proposal_snippet = "".join(proposal_snippet_lines)

        # Calcolo indici di carattere per proposal_text
        # Se j1 o j2 sono fuori range per prop_line_starts (testo vuoto), gestisci
        prop_start_char = (
            prop_line_starts[j1]
            if j1 < len(prop_line_starts)
            else (prop_line_starts[-1] if prop_line_starts else 0)
        )
        prop_end_char = (
            prop_line_starts[j2]
            if j2 < len(prop_line_starts)
            else (prop_line_starts[-1] if prop_line_starts else 0)
        )

        # Calcolo indici di carattere per standard_text
        std_start_char = (
            std_line_starts[i1]
            if i1 < len(std_line_starts)
            else (std_line_starts[-1] if std_line_starts else 0)
        )
        std_end_char = (
            std_line_starts[i2]
            if i2 < len(std_line_starts)
            else (std_line_starts[-1] if std_line_starts else 0)
        )

        if tag == "replace":  # Testo modificato
            llm_analysis_content = await analyze_difference_with_llm(
                standard_snippet, proposal_snippet, "MODIFIED"
            )
            # Recupera variazioni storiche basate sulla clausola standard originale
            historical_vars = await get_historical_variations(standard_snippet)
            llm_analysis_content["historical_variations"] = historical_vars

            differences.append(
                DifferenceModel(
                    type="MODIFIED",
                    proposal_start_index=prop_start_char,
                    proposal_end_index=prop_end_char,
                    proposal_text_snippet=proposal_snippet,
                    llm_analysis=llm_analysis_content,
                )
            )
        elif tag == "delete":  # Testo presente nello standard ma non nella proposta
            # Questo tipo di differenza è più difficile da visualizzare direttamente nel proposal_text
            # Lo includiamo per completezza, ma la UI potrebbe aver bisogno di gestirlo diversamente.
            # Non ha proposal_start_index/end_index validi nel contesto del proposal_text.
            # Potremmo volerlo loggare o passare in modo diverso.
            # Per ora, lo aggiungiamo con indici "segnaposto" o lo omettiamo dalla visualizzazione diretta.
            print(f"DELETED from standard: {standard_snippet[:100]}...")
            # differences.append(DifferenceModel(
            #     type="DELETED_FROM_STANDARD",
            #     # Questi indici non si applicano al testo della proposta
            #     proposal_start_index=prop_start_char, # Potrebbe essere l'inizio della sezione precedente nella proposta
            #     proposal_end_index=prop_start_char,   # o la fine
            #     proposal_text_snippet=f"[STANDARD TEXT DELETED: {standard_snippet[:50]}...]",
            #     llm_analysis={"description": f"Il seguente testo standard è stato rimosso: {standard_snippet}"}
            # ))
        elif tag == "insert":  # Testo aggiunto nella proposta
            llm_analysis_content = await analyze_difference_with_llm(
                "", proposal_snippet, "ADDED"
            )
            # Per le aggiunte, la ricerca storica potrebbe basarsi su parole chiave o sull'intera clausola aggiunta
            # a seconda di come si vuole definire la "similarità" per clausole nuove.
            historical_vars = await get_historical_variations(
                proposal_snippet
            )  # Cerca simili alla clausola aggiunta
            llm_analysis_content["historical_variations"] = historical_vars

            differences.append(
                DifferenceModel(
                    type="ADDED",
                    proposal_start_index=prop_start_char,
                    proposal_end_index=prop_end_char,
                    proposal_text_snippet=proposal_snippet,
                    llm_analysis=llm_analysis_content,
                )
            )
        # 'equal' significa che le sezioni sono uguali, non facciamo nulla.

    # Filtra le differenze vuote (può capitare con splitlines e join se le linee erano solo newline)
    differences = [d for d in differences if d.proposal_text_snippet.strip()]

    return proposal_text, differences
