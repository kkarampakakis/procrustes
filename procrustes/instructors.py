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


def instruct_structure(language: str, context_guidelines: str = "") -> str:
    """Prompt for field *names*, not information to fill those fields."""
    return f"""You are designing an empty data-entry template based on a PDF page.

TASK
- Examine the provided PDF page and identify the names of data fields that
  would be useful to record from paperwork of this kind.
- Return field names only: DO NOT provide field values, names of actual people,
  addresses, dates, or other document-specific answers.
- Prefer headings, form labels, and explicitly identifiable data categories.
- Do not fabricate categories unsupported by the page.
- Keep each label short, precise, and specific enough to be reusable.
- If the page contains no identifiable fields, return an empty string.
- Do not number the fields or include commentary.

STRICT JSON OUTPUT
Return only a valid JSON object with exactly one key, \"entries\".
Its value MUST be a string with one field name per line, separated by newline
characters. No other keys, markdown, or explanations.

LANGUAGE
Use {language} for the field labels unless official terms should remain
in their original language.

CONTEXT GUIDELINES
{context_guidelines}
"""
