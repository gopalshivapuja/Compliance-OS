"""
Document Auto-Categorization Service (V2)

Automatically categorize uploaded evidence using Claude Haiku
"""

from typing import Optional


async def categorize_uploaded_evidence(file_path: str) -> Optional[str]:
    """
    Classify document into one of 15 categories using Claude Haiku

    Categories:
    - Invoice
    - Form 16 (TDS certificate)
    - Bank Statement
    - Challan (tax payment receipt)
    - GST Return
    - Salary Register
    - Board Resolution
    - Power of Attorney
    - Audit Report
    - Other

    Args:
        file_path: Path to uploaded file (local or S3)

    Returns:
        str: Category name

    NOTE: V1 stub - returns "Other"
          V2 implementation will use Claude Haiku for classification
          Cost: ~$0.001 per document (very cheap with Haiku)
    """
    # V1: Return "Other" (manual categorization)
    return "Other"

    # V2 implementation:
    # from anthropic import Anthropic
    #
    # client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    #
    # # Extract first page
    # first_page = extract_first_page(file_path)
    #
    # # Categorize using Claude Haiku
    # response = client.messages.create(
    #     model="claude-3-5-haiku-20241022",
    #     max_tokens=50,
    #     messages=[{
    #         "role": "user",
    #         "content": [
    #             {"type": "image", "source": {"type": "base64", "data": first_page}},
    #             {"type": "text", "text": categorization_prompt}
    #         ]
    #     }]
    # )
    #
    # return response.content[0].text.strip()
