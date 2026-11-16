import pickle
import sys
from types import ModuleType
from unittest.mock import Mock

import pytest

from procrustes import prompt_gateway as module


def test_gateway_initializes_with_inquiry_instructions(monkeypatch, settings):
    invoker = Mock()
    monkeypatch.setattr(module.PromptGateway, 'create_invoker', lambda self, x, entries, instructions: invoker)
    gate = module.PromptGateway(settings)
    assert gate.inquiror is invoker
    assert gate.settings is settings
    assert gate.openai_client is None
    assert gate.google_client is None


@pytest.mark.parametrize('model,invoker_module,invoker_name', [
    ('gpt-4o', 'procrustes.gpt_invoker', 'GPT_Invoker'),
    ('gemini-2.5-pro', 'procrustes.gemini_invoker', 'Gemini_Invoker'),
])
def test_create_invoker_converts_false_to_none(monkeypatch, settings, model, invoker_module, invoker_name):
    settings['inquiror']['model'] = model
    gate = module.PromptGateway.__new__(module.PromptGateway)
    gate.settings = settings
    gate.openai_client = None
    gate.google_client = None
    client = object()
    monkeypatch.setattr(gate, 'create_client', lambda _: client)
    imported = __import__(invoker_module, fromlist=[invoker_name])
    cls = Mock()
    monkeypatch.setattr(imported, invoker_name, cls)
    gate.create_invoker(settings['inquiror'], ['Name'], 'instructions')
    cls.assert_called_once_with(client, ['Name'], 'instructions', model, None, None, None, None)


def test_unknown_model_rejected(settings):
    gate = module.PromptGateway.__new__(module.PromptGateway)
    with pytest.raises(ValueError, match='Unknown LLM model'):
        gate.create_invoker({**settings['inquiror'], 'model': 'unknown'}, [], '')


def test_openai_client_is_cached_without_network(monkeypatch, settings):
    fake_module = ModuleType('openai')
    fake_module.OpenAI = Mock(return_value=object())
    monkeypatch.setitem(sys.modules, 'openai', fake_module)
    gate = module.PromptGateway.__new__(module.PromptGateway)
    gate.settings = settings
    gate.openai_client = None
    gate.google_client = None
    assert gate.create_client('gpt-4o') is gate.create_client('gpt-4o-mini')
    fake_module.OpenAI.assert_called_once_with(api_key='test-openai-key')


def test_openai_key_from_text_file(monkeypatch, tmp_path, settings):
    (tmp_path / 'secret.txt').write_text('  file-key  ', encoding='utf-8')
    settings['api_serial_keys']['openai'] = 'secret.txt'
    monkeypatch.setattr(module, 'parent_folder', tmp_path)
    fake_module = ModuleType('openai')
    fake_module.OpenAI = Mock(return_value=object())
    monkeypatch.setitem(sys.modules, 'openai', fake_module)
    gate = module.PromptGateway.__new__(module.PromptGateway)
    gate.settings, gate.openai_client, gate.google_client = settings, None, None
    gate.create_client('gpt-4o')
    fake_module.OpenAI.assert_called_once_with(api_key='file-key')


@pytest.mark.parametrize('provider,model', [('openai', 'gpt-4o'), ('google', 'gemini-2.5-pro')])
def test_blank_api_key_is_rejected(settings, provider, model):
    settings['api_serial_keys'][provider] = '  '
    gate = module.PromptGateway.__new__(module.PromptGateway)
    gate.settings, gate.openai_client, gate.google_client = settings, None, None
    with pytest.raises(ValueError, match='No API key'):
        gate.create_client(model)


def test_gemini_client_is_cached(monkeypatch, settings):
    import google.genai
    client_cls = Mock(return_value=object())
    monkeypatch.setattr(google.genai, 'Client', client_cls)
    gate = module.PromptGateway.__new__(module.PromptGateway)
    gate.settings, gate.openai_client, gate.google_client = settings, None, None
    assert gate.create_client('gemini-2.5-pro') is gate.create_client('gemini-2.5-flash')
    client_cls.assert_called_once_with(api_key='test-google-key')


def test_gateway_pickle_drops_clients_and_rebinds(monkeypatch, settings):
    gate = module.PromptGateway.__new__(module.PromptGateway)
    gate.settings = settings
    gate.openai_client = object()
    gate.google_client = object()
    from procrustes.gpt_invoker import GPT_Invoker
    gate.inquiror = GPT_Invoker(object(), ['Name'], '', 'gpt-4o', None, None, None, None)
    restored_state = gate.__getstate__()
    assert 'openai_client' not in restored_state
    assert 'google_client' not in restored_state
    fresh_client = object()
    monkeypatch.setattr(module.PromptGateway, 'create_client', lambda self, model: fresh_client)
    restored = pickle.loads(pickle.dumps(gate))
    assert restored.openai_client is None
    assert restored.google_client is None
    assert restored.inquiror.client is fresh_client


def test_unknown_client_model_rejected(settings):
    gate = module.PromptGateway.__new__(module.PromptGateway)
    gate.settings, gate.openai_client, gate.google_client = settings, None, None
    with pytest.raises(ValueError, match='Unknown model'):
        gate.create_client('other-model')
