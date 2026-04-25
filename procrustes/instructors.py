# ------------------------------------------------------------------------------------------
# instructors
# ------------------------------------------------------------------------------------------

def instruct_inquiry(language):
    return f"""You are tasked with reading a PDF file, detecting relevant information, and filling in the requested entries.

INPUT
- You will receive:
  - PDF bytes containing bureaucratic information.
  - A list of entries to be filled.

TASK
- For each requested entry, find the relevant information in the PDF.
- If the PDF contains the answer, return the answer.
- If the PDF does not contain enough information for an entry, return a single dash: "-".

OUTPUT STRICT JSON
- Return ONLY a valid JSON object.
- Use only the requested entry names as keys.
- Do not add new keys.
- Do not return markdown.
- Do not return code fences.
- Do not add explanations.

LANGUAGE
- The main language for this task is {language}.

Return nothing except the JSON object.
"""

# ------------------------------------------------------------------------------------------
