"""
This is a collection of utility functions for easier, DRY testing.
"""
from collections import namedtuple
from contextlib import contextmanager
from subprocess import CalledProcessError

import mock


@contextmanager
def mock_git_calls(*cases):
    """We perform several subprocess.check_output calls for git commands,
    but we only want to mock one at a time. This function helps us do that.

    However, the idea is that we *never* want to call out to git in tests,
    so we should mock out everything that does that.

    :type cases: iterable(SubprocessMock)
    """
    # We need to use a dictionary, because python2.7 does not support
    # the `nonlocal` keyword (and needs to share scope with
    # _mock_single_git_call function)
    current_case = {'index': 0}

    def _mock_subprocess_git_call(cmds, **kwargs):
        command = ' '.join(cmds)

        try:
            case = cases[current_case['index']]
        except IndexError:
            raise AssertionError(
                '\nExpected: ""\n'
                'Actual: "{}"'.format(
                    command
                )
            )
        current_case['index'] += 1

        if command != case.expected_input:
            # Pretty it up a little, for display
            if not case.expected_input.startswith('git'):
                case.expected_input = 'git ' + case.expected_input

            raise AssertionError(
                '\nExpected: "{}"\n'
                'Actual: "{}"'.format(
                    case.expected_input,
                    command,
                )
            )

        if case.should_throw_exception:
            raise CalledProcessError(1, '', case.mocked_output)

        return case.mocked_output

    def _mock_single_git_call(directory, *args):
        return _mock_subprocess_git_call(['git'] + list(args))

    # mock_subprocess is needed for `clone_repo_to_location`.
    with mock.patch(
        'detect_secrets_server.storage.core.git._git'
    ) as mock_git, mock.patch(
        'detect_secrets_server.storage.core.git.subprocess.check_output'
    ) as mock_subprocess:
        mock_git.side_effect = _mock_single_git_call
        mock_subprocess.side_effect = _mock_subprocess_git_call

        yield

    if current_case['index'] != len(cases):
        raise AssertionError(
            '\nExpected: "{}"\n'
            'Actual: ""'.format(cases[current_case['index']].expected_input)
        )


class SubprocessMock(namedtuple(
    'SubprocessMock',
    [
        'expected_input',
        'mocked_output',
        'should_throw_exception',
    ]
)):
    """For use with mock_subprocess.

    :type expected_input: string
    :param expected_input: only return mocked_output if input matches this

    :type mocked_output: mixed
    :param mocked_output: value you want to return, when expected_input matches.

    :type should_throw_exception: bool
    :param should_throw_exception: if True, will throw subprocess.CalledProcessError
                                   with mocked output as error message
    """
    def __new__(cls, expected_input, mocked_output='', should_throw_exception=False):
        return super(SubprocessMock, cls).__new__(
            cls,
            expected_input,
            mocked_output,
            should_throw_exception
        )
