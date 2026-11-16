from pathlib import Path

import pytest
from pypdf import PdfReader
from io import BytesIO

from procrustes import iterator as module


def test_metadata_finds_each_page_and_sorts_filenames(make_pdf, tmp_path):
    make_pdf('z.pdf', 2)
    make_pdf('a.pdf', 1)
    result = module.build_metadata_list(tmp_path)
    assert [(p.pdf_name, p.page_number, p.page_index) for p in result] == [
        ('a.pdf', 1, 0), ('z.pdf', 1, 0), ('z.pdf', 2, 1)]


def test_metadata_ignores_non_pdf_and_handles_bad_pdf(make_pdf, tmp_path, capsys):
    make_pdf('ok.pdf', 1)
    (tmp_path / 'broken.pdf').write_text('not a PDF')
    (tmp_path / 'notes.txt').write_text('ignore')
    result = module.build_metadata_list(tmp_path)
    assert [p.pdf_name for p in result] == ['ok.pdf']
    assert 'Skipping broken.pdf' in capsys.readouterr().out


def test_metadata_empty_directory(tmp_path):
    assert module.build_metadata_list(tmp_path) == []


def test_metadata_to_bytes_extracts_one_page(make_pdf, tmp_path):
    make_pdf('sample.pdf', 3)
    entry = module.build_metadata_list(tmp_path)[1]
    output = module.metadata_to_bytes(entry)
    assert output.startswith(b'%PDF-')
    assert len(PdfReader(BytesIO(output)).pages) == 1


def test_iterator_initializes_entries(monkeypatch, fake_gate):
    monkeypatch.setattr(module, 'build_metadata_list', lambda: [])
    obj = module.Iterator(fake_gate)
    assert obj.i == 0
    assert obj.filled_entries == {'Name': [], 'Date': []}
    assert obj.pages == []


def test_empty_inquiry_does_not_call_model_or_save(monkeypatch, fake_gate, capsys):
    monkeypatch.setattr(module, 'build_metadata_list', lambda: [])
    obj = module.Iterator(fake_gate)
    monkeypatch.setattr(obj, 'save_as_pickle', lambda: pytest.fail('unexpected save'))
    obj.resume_inquiry()
    assert 'No PDF files found.' in capsys.readouterr().out
    assert fake_gate.inquiror.prompts == []


def test_inquiry_deduplicates_and_normalizes_values(monkeypatch, fake_gate):
    monkeypatch.setattr(module, 'build_metadata_list', lambda: [object()] * 3)
    monkeypatch.setattr(module, 'metadata_to_bytes', lambda p: b'pdf')
    fake_gate.inquiror.responses = [
        {'Name': ' Alice ', 'Date': '-', 'Extra': 'one'},
        {'Name': 'alice', 'Date': '2026', 'Extra': 'ONE'},
        {'Name': 'Bob', 'Date': None, 'Extra': 'two'},
    ]
    obj = module.Iterator(fake_gate)
    saves = []
    monkeypatch.setattr(obj, 'save_as_pickle', lambda: saves.append(obj.i))
    obj.resume_inquiry()
    assert obj.filled_entries == {'Name': ['Alice', 'Bob'], 'Date': ['2026'], 'Extra': ['one', 'two']}
    assert obj.i == 3
    assert saves == [1, 2, 3]
    assert fake_gate.inquiror.prompts == [b'pdf'] * 3


@pytest.mark.parametrize('value', [None, '', '  ', '-', ' - '])
def test_inquiry_skips_blank_values(monkeypatch, fake_gate, value):
    monkeypatch.setattr(module, 'build_metadata_list', lambda: [object()])
    monkeypatch.setattr(module, 'metadata_to_bytes', lambda _: b'pdf')
    fake_gate.inquiror.responses = [{'Name': value}]
    obj = module.Iterator(fake_gate)
    monkeypatch.setattr(obj, 'save_as_pickle', lambda: None)
    obj.resume_inquiry()
    assert obj.filled_entries['Name'] == []


def test_resume_starts_from_saved_index(monkeypatch, fake_gate):
    monkeypatch.setattr(module, 'build_metadata_list', lambda: [object()] * 3)
    monkeypatch.setattr(module, 'metadata_to_bytes', lambda _: b'pdf')
    fake_gate.inquiror.responses = [{'Name': 'new'}]
    obj = module.Iterator(fake_gate)
    obj.i = 2
    obj.filled_entries['Name'] = ['old']
    monkeypatch.setattr(obj, 'save_as_pickle', lambda: None)
    obj.resume_inquiry()
    assert obj.i == 3
    assert obj.filled_entries['Name'] == ['old', 'new']
    assert len(fake_gate.inquiror.prompts) == 1


def test_pickle_checkpoint_roundtrip(monkeypatch, tmp_path, fake_gate):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(module, 'build_metadata_list', lambda: [])
    # Use a picklable object instead of the test fixture's locally defined fake class.
    from types import SimpleNamespace
    obj = module.Iterator(SimpleNamespace(settings=fake_gate.settings, inquiror=None))
    obj.i = 4
    obj.filled_entries['Name'] = ['Alice']
    obj.save_as_pickle()
    import pickle
    with Path(module.PICKLE_NAME).open('rb') as f:
        restored = pickle.load(f)
    assert restored.i == 4
    assert restored.filled_entries['Name'] == ['Alice']
