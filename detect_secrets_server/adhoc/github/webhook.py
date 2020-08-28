"""
For organizations that integrate with Github, they have the ability to setup
a webhook to receive events for all repos under the entire organization. In
such cases, this script allows you to scan other fields in which secrets may
be leaked, rather than just focusing on secrets in code.
"""
import io
try:
    from contextlib import redirect_stdout
except ImportError:  # pragma: no cover
    import sys
    from contextlib import contextmanager

    @contextmanager
    def redirect_stdout(target):
        original = sys.stdout
        sys.stdout = target
        yield
        sys.stdout = original

from detect_secrets.main import main as run_detect_secrets


def scan_for_secrets(event_type, body, *args):
    """
    :type event_type: str
    :param event_type: a full list can be found
        https://developer.github.com/v3/activity/events/types/
    :type body: Dict[str, Any]
    :param body: a GitHub webhook event
    :type args: List
    :param args: parameters to pass to detect-secrets directly

    :rtype: Optional[str]
    :returns: link to field with leaked secret
    """
    mapping = {
        'commit_comment': _parse_comment,
        'issue_comment': _parse_comment,
        'pull_request_review_comment': _parse_comment,
        'issues': _parse_issue,
        'pull_request': _parse_pull_request,

        # NOTE: We're currently ignoring `project*` events, because we don't use
        #       it. Pull requests welcome!
    }
    try:
        payload, attribution_link = mapping[event_type](body)
    except KeyError:
        # Not an applicable event.
        return None

    f = io.StringIO()
    with redirect_stdout(f):
        run_detect_secrets([
            'scan',
            '--string', payload,
            *args,
        ])

    has_results = any([
        line
        for line in f.getvalue().splitlines()

        # NOTE: Expected format: '<DetectorName>: [True/False]'
        if 'True' in line.split(':')[1]
    ])

    return attribution_link if has_results else None


def _parse_comment(body):
    """
    :type body: Dict[str, Any]
    :rtype: Tuple[str, str]
    """
    if body.get('action', 'created') == 'deleted':
        # This indicates that this is not an applicable event.
        raise KeyError

    return (
        body['comment']['body'],
        body['comment']['html_url'],
    )


def _parse_issue(body):
    """
    :type body: Dict[str, Any]
    :rtype: Tuple[str, str]
    """
    if body['action'] not in {'opened', 'edited', }:
        # This indicates that this is not an applicable event.
        raise KeyError

    # NOTE: Explicitly ignoring the issue "title" here, because
    # I trust developers enough (hopefully, not famous last words).
    # I think a secret in the title falls under the same threat
    # vector as a secret in the labels.
    return (
        body['issue']['body'],
        body['issue']['html_url'],
    )


def _parse_pull_request(body):
    """
    :type body: Dict[str, Any]
    :rtype: Tuple[str, str]
    """
    if body['action'] not in {'opened', 'edited', }:
        # This indicates that this is not an applicable event.
        raise KeyError

    return (
        body['pull_request']['body'],
        body['pull_request']['html_url'],
    )
