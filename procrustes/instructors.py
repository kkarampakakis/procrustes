# ------------------------------------------------------------------------------------------
# instructors
# ------------------------------------------------------------------------------------------

def instruct_inquiry(language: str, context_guidelines: str = "") -> str:
    return f"""You are tasked with reading a PDF file and extracting information for specific requested entries.

INPUT
- You will receive:
  - PDF content containing bureaucratic information.
  - A list of entry names to be filled.

TASK
- For each requested entry, search the PDF for information that directly answers it.
- Use only information explicitly present in the PDF.
- Do not guess.
- Do not infer missing information.
- Do not use outside knowledge.
- If the PDF does not contain enough information for an entry, return exactly "-".
- Keep answers concise.
- Preserve names, dates, numbers, document titles, addresses, identification numbers, and official wording as they appear in the PDF when possible.

OUTPUT STRICT JSON
- Return ONLY one valid JSON object.
- Use exactly the requested entry names as keys.
- Do not add new keys.
- Do not omit requested keys.
- Do not return markdown.
- Do not return code fences.
- Do not add explanations.
- Every value must be a string.

LANGUAGE
- The main language for this task is {language}.
- Do not translate official names, document titles, dates, addresses, identification numbers, or quoted text.
- If the relevant answer appears in the PDF in another language and translating it would change its official meaning, preserve the original wording.

CONTEXT GUIDELINES
{context_guidelines}
"""
