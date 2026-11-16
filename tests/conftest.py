# Allow offline unit testing when the optional Google SDK is not installed.
# If the real SDK is available, these stubs are never used.
import sys
from enum import Enum
from types import ModuleType, SimpleNamespace
try:
    from google.genai import types as _real_types
except ImportError:
    google = sys.modules.get('google') or ModuleType('google')
    google.__path__ = getattr(google, '__path__', [])
    genai = ModuleType('google.genai')
    class ThinkingLevel(Enum):
        HIGH = 'high'
        MEDIUM = 'medium'
        LOW = 'low'
        MINIMAL = 'minimal'
    class Part:
        @classmethod
        def from_bytes(cls, data, mime_type):
            return SimpleNamespace(inline_data=SimpleNamespace(data=data, mime_type=mime_type))
    class Config:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
            for key in ('thinking_config', 'temperature', 'top_p'):
                self.__dict__.setdefault(key, None)
    types = ModuleType('google.genai.types')
    types.ThinkingLevel = ThinkingLevel
    types.Part = Part
    types.GenerateContentConfig = Config
    types.ThinkingConfig = Config
    genai.types = types
    genai.Client = None
    google.genai = genai
    sys.modules['google'] = google
    sys.modules['google.genai'] = genai
    sys.modules['google.genai.types'] = types

from pathlib import Path
from types import SimpleNamespace

import pytest
from pypdf import PdfWriter


@pytest.fixture
def settings():
    return {
        'general': {'entries': ['Name', 'Date'], 'language': 'English', 'context_guidelines': 'Be precise'},
        'inquiror': {'model': 'gpt-4o', 'reasoning': False, 'verbosity': False, 'temperature': False, 'top_p': False},
        'api_serial_keys': {'openai': 'test-openai-key', 'google': 'test-google-key'},
    }


@pytest.fixture
def make_pdf(tmp_path):
    def create(name='document.pdf', pages=2):
        path = tmp_path / name
        writer = PdfWriter()
        for _ in range(pages):
            writer.add_blank_page(width=612, height=792)
        with path.open('wb') as handle:
            writer.write(handle)
        return path
    return create


@pytest.fixture
def fake_gate(settings):
    class FakeInquiror:
        def __init__(self):
            self.responses = []
            self.prompts = []
        def invoke(self, pdf):
            self.prompts.append(pdf)
            return self.responses.pop(0)
    return SimpleNamespace(settings=settings, inquiror=FakeInquiror())
