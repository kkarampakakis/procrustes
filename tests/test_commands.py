import csv
import pickle
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from procrustes import commands


def test_load_settings(tmp_path):
    p = tmp_path / 'settings.toml'
    p.write_text('[general]\nlanguage = "English"\n', encoding='utf-8')
    assert commands._load_settings(p) == {'general': {'language': 'English'}}


def test_load_settings_bad_toml(tmp_path):
    p = tmp_path / 'bad.toml'
    p.write_text('broken = [', encoding='utf-8')
    with pytest.raises(Exception):
        commands._load_settings(p)


def test_reset_copies_defaults(monkeypatch, tmp_path):
    source = tmp_path / 'default_settings.toml'
    source.write_text('[general]\nentries = []\n', encoding='utf-8')
    target = tmp_path / 'settings.toml'
    monkeypatch.setattr(commands, 'package_folder', tmp_path)
    monkeypatch.setattr(commands, 'settings_path', target)
    commands.reset()
    assert target.read_text(encoding='utf-8') == source.read_text(encoding='utf-8')


def test_reset_missing_defaults_raises(monkeypatch, tmp_path):
    monkeypatch.setattr(commands, 'package_folder', tmp_path)
    with pytest.raises(FileNotFoundError):
        commands.reset()


def test_open_settings_creates_missing_file(monkeypatch, tmp_path, capsys):
    target = tmp_path / 'settings.toml'
    monkeypatch.setattr(commands, 'settings_path', target)
    create = Mock(side_effect=lambda: target.write_text('created'))
    opener = Mock()
    monkeypatch.setattr(commands, 'reset', create)
    monkeypatch.setattr(commands, '_open_file', opener)
    commands.open_settings()
    create.assert_called_once_with()
    opener.assert_called_once_with(target)
    assert 'not found' in capsys.readouterr().out


def test_open_existing_settings_does_not_reset(monkeypatch, tmp_path):
    target = tmp_path / 'settings.toml'
    target.write_text('existing')
    monkeypatch.setattr(commands, 'settings_path', target)
    reset = Mock()
    opener = Mock()
    monkeypatch.setattr(commands, 'reset', reset)
    monkeypatch.setattr(commands, '_open_file', opener)
    commands.open_settings()
    reset.assert_not_called()
    opener.assert_called_once_with(target)


def test_csv_output_preserves_unicode_and_columns(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    commands._print_to_csv({'Name': ['Αθήνα', '東京'], 'Date': [], 'Other': ['a,b']})
    with (tmp_path / 'procrustean_output.csv').open(encoding='utf-8-sig', newline='') as f:
        assert list(csv.reader(f)) == [['Name', 'Αθήνα', '東京'], ['Date'], ['Other', 'a,b']]


def test_load_pickle_roundtrip(tmp_path):
    p = tmp_path / 'checkpoint.pkl'
    with p.open('wb') as f:
        pickle.dump({'index': 3}, f)
    assert commands._load_pickle(p) == {'index': 3}


def test_inquire_without_settings_opens_editor(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(commands, 'settings_path', tmp_path / 'missing.toml')
    opener = Mock()
    monkeypatch.setattr(commands, 'open_settings', opener)
    commands.inquire()
    opener.assert_called_once_with()
    assert 'try again' in capsys.readouterr().out


def test_inquire_with_settings_runs_and_exports(monkeypatch, tmp_path, settings):
    path = tmp_path / 'settings.toml'
    path.write_text('configured')
    monkeypatch.setattr(commands, 'settings_path', path)
    monkeypatch.setattr(commands, '_load_settings', lambda _: settings)
    gate = object()
    monkeypatch.setattr(commands, 'PromptGateway', Mock(return_value=gate))
    inquiry = Mock()
    inquiry.filled_entries = {'Name': ['Alice']}
    monkeypatch.setattr(commands, 'Iterator', Mock(return_value=inquiry))
    export = Mock()
    monkeypatch.setattr(commands, '_print_to_csv', export)
    commands.inquire()
    inquiry.resume_inquiry.assert_called_once_with()
    export.assert_called_once_with(inquiry.filled_entries)


def test_resume_loads_checkpoint_runs_and_exports(monkeypatch):
    inquiry = Mock()
    inquiry.filled_entries = {'Name': ['Alice']}
    loader = Mock(return_value=inquiry)
    exporter = Mock()
    monkeypatch.setattr(commands, '_load_pickle', loader)
    monkeypatch.setattr(commands, '_print_to_csv', exporter)
    commands.resume()
    loader.assert_called_once_with(commands.PICKLE_NAME)
    inquiry.resume_inquiry.assert_called_once_with()
    exporter.assert_called_once_with(inquiry.filled_entries)


@pytest.mark.parametrize('system,expected', [('Linux', 'xdg-open'), ('Darwin', 'open')])
def test_open_file_unix(monkeypatch, tmp_path, system, expected):
    monkeypatch.setattr(commands.platform, 'system', lambda: system)
    run = Mock()
    monkeypatch.setattr(commands.subprocess, 'run', run)
    commands._open_file(tmp_path / 'settings.toml')
    run.assert_called_once_with([expected, tmp_path / 'settings.toml'], check=True)


def test_open_file_unsupported_os(monkeypatch, tmp_path):
    monkeypatch.setattr(commands.platform, 'system', lambda: 'Unknown')
    with pytest.raises(RuntimeError, match='Unsupported'):
        commands._open_file(tmp_path / 'settings.toml')
