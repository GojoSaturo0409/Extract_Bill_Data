from pydantic import BaseModel
from typing import List, Optional

class BillItem(BaseModel):
    item_name: str
    item_amount: float
    item_rate: float
    item_quantity: float

class PageLineItems(BaseModel):
    page_no: str
    page_type: str
    bill_items: List[BillItem]

class TokenUsage(BaseModel):
    total_tokens: int
    input_tokens: int
    output_tokens: int

class ExtractionData(BaseModel):
    pagewise_line_items: List[PageLineItems]
    total_item_count: int

class ExtractionResponse(BaseModel):
    is_success: bool
    token_usage: TokenUsage
    data: Optional[ExtractionData] = None
    error: Optional[str] = None

    def dict(self, **kwargs):
        d = super().dict(**kwargs)
        if not self.is_success and self.data is None:
            d['data'] = None
        return d
