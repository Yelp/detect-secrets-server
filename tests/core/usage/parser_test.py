import sys

import pytest

import detect_secrets_server
from detect_secrets_server.core.usage.parser import ServerParserBuilder


def test_version(capsys):
    with pytest.raises(SystemExit) as e:
        ServerParserBuilder().parse_args(['--version'])

    assert str(e.value) == '0'

    # Oh, the joys of writing compatible code
    if sys.version_info[0] < 3:     # pragma: no cover
        assert capsys.readouterr().err.strip() == detect_secrets_server.__version__
    else:
        assert capsys.readouterr().out.strip() == detect_secrets_server.__version__
