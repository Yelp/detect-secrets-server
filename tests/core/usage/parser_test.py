import pytest

import detect_secrets_server
from detect_secrets_server.core.usage.parser import ServerParserBuilder
from detect_secrets_server.util.version import is_python_2


def test_version(capsys):
    with pytest.raises(SystemExit) as e:
        ServerParserBuilder().parse_args(['--version'])

    assert str(e.value) == '0'

    # Oh, the joys of writing compatible code
    if is_python_2():  # pragma: no cover
        assert capsys.readouterr().err.strip() == detect_secrets_server.__version__
    else:  # pragma: no cover
        assert capsys.readouterr().out.strip() == detect_secrets_server.__version__
