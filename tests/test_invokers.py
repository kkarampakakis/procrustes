import base64
import json
import pickle
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from procrustes.gpt_invoker import GPT_Invoker, template_to_string_schema as gpt_schema
from procrustes.gemini_invoker import Gemini_Invoker, template_to_string_schema as gemini_schema


@pytest.mark.parametrize('schema', [gpt_schema, gemini_schema])
def test_strict_schema(schema):
    assert schema(['Name', 'Date']) == {
        'type': 'object',
        'properties': {'Name': {'type': 'string'}, 'Date': {'type': 'string'}},
        'required': ['Name', 'Date'],
        'additionalProperties': False,
    }


def test_gpt_request_and_decoded_result():
    client = Mock()
    client.responses.create.return_value = SimpleNamespace(output_text='{"Name":"Alice"}')
    invoker = GPT_Invoker(client, ['Name'], 'default', 'gpt-4o', 'low', 'low', 0.2, 0.8)
    assert invoker.invoke(b'%PDF', instructions='override') == {'Name': 'Alice'}
    kwargs = client.responses.create.call_args.kwargs
    assert kwargs['instructions'] == 'override'
    assert kwargs['model'] == 'gpt-4o'
    assert kwargs['reasoning'] == {'effort': 'low'}
    assert kwargs['text']['verbosity'] == 'low'
    assert kwargs['text']['format']['schema'] == gpt_schema(['Name'])
    assert kwargs['temperature'] == 0.2
    assert kwargs['top_p'] == 0.8
    assert kwargs['input'][0]['content'][0]['file_data'] == 'data:application/pdf;base64,' + base64.b64encode(b'%PDF').decode()


def test_gpt_omits_optional_parameters():
    client = Mock()
    client.responses.create.return_value = SimpleNamespace(output_text='{}')
    invoker = GPT_Invoker(client, [], 'default', 'gpt-4o', None, None, None, None)
    invoker.invoke(b'data')
    kwargs = client.responses.create.call_args.kwargs
    assert kwargs['instructions'] == 'default'
    assert 'reasoning' not in kwargs
    assert 'verbosity' not in kwargs['text']
    assert 'temperature' not in kwargs
    assert 'top_p' not in kwargs


def test_gpt_invalid_json_raises():
    client = Mock()
    client.responses.create.return_value = SimpleNamespace(output_text='invalid')
    invoker = GPT_Invoker(client, [], '', 'gpt-4o', None, None, None, None)
    with pytest.raises(json.JSONDecodeError):
        invoker.invoke(b'data')


def test_gemini_request_and_parsed_result():
    client = Mock()
    client.models.generate_content.return_value = SimpleNamespace(parsed={'Name': 'Alice'})
    invoker = Gemini_Invoker(client, ['Name'], 'default', 'gemini-2.5-pro', 'high', 'ignored', 0.3, 0.9)
    assert invoker.invoke(b'%PDF', instructions='override') == {'Name': 'Alice'}
    kwargs = client.models.generate_content.call_args.kwargs
    assert kwargs['model'] == 'gemini-2.5-pro'
    assert kwargs['config'].system_instruction == 'override'
    assert kwargs['config'].temperature == 0.3
    assert kwargs['config'].top_p == 0.9
    assert kwargs['config'].response_mime_type == 'application/json'
    assert kwargs['config'].response_json_schema == gemini_schema(['Name'])
    assert kwargs['config'].thinking_config is not None
    assert kwargs['contents'][0].inline_data.data == b'%PDF'


def test_gemini_optional_parameters_and_default_instructions():
    client = Mock()
    client.models.generate_content.return_value = SimpleNamespace(parsed={})
    invoker = Gemini_Invoker(client, [], 'original', 'gemini-test', None, None, None, None)
    invoker.invoke(b'pdf')
    config = client.models.generate_content.call_args.kwargs['config']
    assert config.system_instruction == 'original'
    assert config.thinking_config is None
    assert config.temperature is None
    assert config.top_p is None


@pytest.mark.parametrize('cls', [GPT_Invoker, Gemini_Invoker])
def test_invoker_pickle_excludes_client_and_supports_rebind(cls):
    invoker = cls(object(), ['Name'], 'instructions', 'gpt-4o', None, None, None, None)
    restored = pickle.loads(pickle.dumps(invoker))
    assert restored.client is None
    client = object()
    restored.bind_client(client)
    assert restored.client is client
    assert restored.entries == ['Name']
