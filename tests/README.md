# Procrustes pytest suite

From the repository root, install dependencies and run:

```bash
python -m pip install -e . pytest
python -m pytest -q
```

The tests use temporary PDF documents, fake API responses, and temporary directories. They do not need real API credentials or make paid model requests. If `google-genai` is absent, a minimal local stand-in is used for unit tests; install project dependencies to verify integration against the actual SDK.

Tests cover command dispatch, settings, CSV output, PDF metadata and extraction, iteration and deduplication, checkpoint serialization and resume, gateway client routing, prompt construction, and OpenAI/Gemini request shapes.

The suite validates the **current pickle-based checkpoint implementation**; it does not implement or verify a replacement persistence format.
