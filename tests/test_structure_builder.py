"""Tests for blank entry discovery; all API interactions are mocked."""

import csv
import pickle
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from procrustes import commands, instructors
from procrustes import structure_builder as module
from procrustes.iterator import Iterator
from procrustes.prompt_gateway import PromptGateway


def fake_builder_gate(settings, responses):
    invoker = Mock()
    invoker.invoke.side_effect = responses
    gate = SimpleNamespace(settings=settings, create_structure_builder_invoker=Mock(return_value=invoker))
    return gate, invoker


def test_is_iterator_subclass():
    assert issubclass(module.StructureBuilder, Iterator)


def test_initializes_without_predefined_entries(monkeypatch, settings):
    monkeypatch.setattr('procrustes.iterator.build_metadata_list', lambda: [])
    gate, invoker = fake_builder_gate(settings, [])
    builder = module.StructureBuilder(gate)
    assert builder.filled_entries == {}
    assert builder.pages == []
    gate.create_structure_builder_invoker.assert_called_once_with()


def test_discovers_deduplicated_empty_slots(monkeypatch, settings):
    monkeypatch.setattr('procrustes.iterator.build_metadata_list', lambda: [object()] * 3)
    monkeypatch.setattr(module, 'metadata_to_bytes', lambda _: b'%PDF-...')
    gate, invoker = fake_builder_gate(settings, [
        {'entries': 'Name\nDate\nAddress'},
        {'entries': 'name\n- Permit ID\nAddress'},
        {'entries': '• Owner\nDate\n'},
    ])
    builder = module.StructureBuilder(gate)
    checkpoints = []
    monkeypatch.setattr(builder, 'save_as_pickle', lambda: checkpoints.append(builder.i))
    builder.resume_inquiry()
    assert builder.filled_entries == {
        'Name': [], 'Date': [], 'Address': [], 'Permit ID': [], 'Owner': []}
    assert builder.i == 3
    assert checkpoints == [1, 2, 3]
    assert invoker.invoke.call_count == 3


def test_resume_only_processes_remaining_pages(monkeypatch, settings):
    monkeypatch.setattr('procrustes.iterator.build_metadata_list', lambda: [object()] * 3)
    monkeypatch.setattr(module, 'metadata_to_bytes', lambda _: b'pdf')
    gate, invoker = fake_builder_gate(settings, [{'entries': 'New slot'}])
    builder = module.StructureBuilder(gate)
    builder.i = 2
    builder.filled_entries = {'Old slot': []}
    monkeypatch.setattr(builder, 'save_as_pickle', lambda: None)
    builder.resume_inquiry()
    assert builder.filled_entries == {'Old slot': [], 'New slot': []}
    assert builder.i == 3
    invoker.invoke.assert_called_once_with(b'pdf')


def test_no_pdf_skips_invocation_and_saving(monkeypatch, settings, capsys):
    monkeypatch.setattr('procrustes.iterator.build_metadata_list', lambda: [])
    gate, invoker = fake_builder_gate(settings, [])
    builder = module.StructureBuilder(gate)
    monkeypatch.setattr(builder, 'save_as_pickle', lambda: pytest.fail('unexpected save'))
    builder.resume_inquiry()
    invoker.invoke.assert_not_called()
    assert 'No PDF files found' in capsys.readouterr().out


@pytest.mark.parametrize('response', [None, [], {}, {'entries': []}, {'entries': None}])
def test_invalid_model_response_does_not_silently_advance(response, monkeypatch, settings):
    monkeypatch.setattr('procrustes.iterator.build_metadata_list', lambda: [object()])
    monkeypatch.setattr(module, 'metadata_to_bytes', lambda _: b'pdf')
    gate, _ = fake_builder_gate(settings, [response])
    builder = module.StructureBuilder(gate)
    with pytest.raises(ValueError, match='entries'):
        builder.resume_inquiry()
    assert builder.i == 0


def test_empty_string_creates_no_slots(monkeypatch, settings):
    monkeypatch.setattr('procrustes.iterator.build_metadata_list', lambda: [object()])
    monkeypatch.setattr(module, 'metadata_to_bytes', lambda _: b'pdf')
    gate, _ = fake_builder_gate(settings, [{'entries': ''}])
    builder = module.StructureBuilder(gate)
    monkeypatch.setattr(builder, 'save_as_pickle', lambda: None)
    builder.resume_inquiry()
    assert builder.filled_entries == {}
    assert builder.i == 1


def test_separate_checkpoint(monkeypatch, tmp_path, settings):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr('procrustes.iterator.build_metadata_list', lambda: [])
    gate, _ = fake_builder_gate(settings, [])
    builder = module.StructureBuilder(gate)
    # Swap out mocked invoker to keep checkpoint fixture picklable.
    builder.gate = SimpleNamespace(settings=settings)
    builder.builder = None
    builder.filled_entries = {'Field': []}
    builder.save_as_pickle()
    assert (tmp_path / module.STRUCTURE_PICKLE_NAME).exists()
    assert not (tmp_path / 'procrustean_pickle.pkl').exists()
    with (tmp_path / module.STRUCTURE_PICKLE_NAME).open('rb') as handle:
        restored = pickle.load(handle)
    assert isinstance(restored, module.StructureBuilder)
    assert restored.filled_entries == {'Field': []}


def test_instructions_do_not_request_values():
    prompt = instructors.instruct_structure('Greek', 'Permit forms')
    assert 'Greek' in prompt
    assert 'Permit forms' in prompt
    assert 'DO NOT provide field values' in prompt
    assert 'entries' in prompt


def test_gateway_factory_uses_structure_prompt(monkeypatch, settings):
    gate = PromptGateway.__new__(PromptGateway)
    gate.settings = settings
    factory = Mock(return_value='builder')
    monkeypatch.setattr(gate, 'create_invoker', factory)
    assert gate.create_structure_builder_invoker() == 'builder'
    args = factory.call_args.args
    assert args[1] == ['entries']
    assert 'Be precise' in args[2]


def test_structure_command_exports_empty_slots(monkeypatch, tmp_path, settings):
    path = tmp_path / 'settings.toml'
    path.write_text('configured')
    monkeypatch.setattr(commands, 'settings_path', path)
    monkeypatch.setattr(commands, '_load_settings', lambda _: settings)
    monkeypatch.setattr(commands, 'PromptGateway', Mock(return_value=object()))
    builder = Mock()
    builder.filled_entries = {'Permit ID': [], 'Owner': []}
    monkeypatch.setattr(commands, 'StructureBuilder', Mock(return_value=builder))
    monkeypatch.chdir(tmp_path)
    commands.build_structure()
    builder.resume_inquiry.assert_called_once_with()
    with (tmp_path / 'procrustean_structure.csv').open(encoding='utf-8-sig', newline='') as handle:
        assert list(csv.reader(handle)) == [['Permit ID'], ['Owner']]


def test_resume_structure_rejects_wrong_checkpoint(monkeypatch):
    monkeypatch.setattr(commands, '_load_pickle', lambda _: object())
    with pytest.raises(TypeError, match='StructureBuilder'):
        commands.resume_structure()


def test_restored_builder_rebinds_its_client(monkeypatch, settings):
    from procrustes.gpt_invoker import GPT_Invoker
    client = object()
    gate = PromptGateway.__new__(PromptGateway)
    gate.settings = settings
    gate.openai_client = None
    gate.google_client = None
    gate.inquiror = GPT_Invoker(None, ['Name'], '', 'gpt-4o', None, None, None, None)
    builder = module.StructureBuilder.__new__(module.StructureBuilder)
    builder.gate = gate
    builder.pages = []
    builder.i = 0
    builder.filled_entries = {'Field': []}
    builder.builder = GPT_Invoker(None, ['entries'], '', 'gpt-4o', None, None, None, None)
    monkeypatch.setattr(PromptGateway, 'create_client', lambda self, model: client)
    restored = pickle.loads(pickle.dumps(builder))
    assert restored.builder.client is client
    assert restored.gate.inquiror.client is client
