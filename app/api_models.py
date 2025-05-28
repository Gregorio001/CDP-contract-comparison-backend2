from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class DifferenceModel(BaseModel):
    type: str  # e.g., "MODIFIED", "ADDED", "DELETED_FROM_STANDARD"
    proposal_start_index: int
    proposal_end_index: int
    proposal_text_snippet: str
    llm_analysis: Dict[
        str, Any
    ]  # e.g., {"description": "...", "historical_variations": ["option A", "option B"]}
    page_number: Optional[int] = None  # Placeholder
    bounding_boxes: Optional[List[List[float]]] = None  # Placeholder


class ComparisonResponse(BaseModel):
    full_proposal_text: str
    differences: List[DifferenceModel]
    highlighted_proposal_pdf_url: Optional[str] = None
