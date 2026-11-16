import sys
from unittest.mock import Mock

import pytest
from procrustes import __main__ as cli, instructors


@pytest.mark.parametrize('command,handler', [
    ('inquire', 'inquire'), ('resume', 'resume'),
    ('reset', 'reset'), ('open-settings', 'open_settings'),
])
def test_cli_dispatch(monkeypatch, command, handler):
    calls = {name: Mock() for name in ('inquire', 'resume', 'reset', 'open_settings')}
    for name, mock in calls.items():
        monkeypatch.setattr(cli, name, mock)
    monkeypatch.setattr(sys, 'argv', ['procrustes', command])
    cli.main()
    for name, mock in calls.items():
        assert mock.call_count == (1 if name == handler else 0)


def test_cli_requires_subcommand(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['procrustes'])
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 2


def test_instructions_include_language_and_context():
    result = instructors.instruct_inquiry('Greek', 'Do not expand abbreviations')
    assert 'Greek' in result
    assert 'Do not expand abbreviations' in result
    assert 'JSON' in result
    assert 'Do not guess' in result
