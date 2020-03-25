import json
import os

import pytest

from detect_secrets_server.adhoc.github.webhook import scan_for_secrets
from testing.util import EICAR


@pytest.mark.parametrize(
    'action',
    {
        'created',
        'edited',
    },
)
@pytest.mark.parametrize(
    'event',
    {
        'commit_comment',
        'issue_comment',
        'pull_request_review_comment',
    },
)
def test_comment_with_secret(event, action):
    payload = get_payload(event)

    # We make sure to add "multiple words" here, since we want to make
    # sure that it supports multi-word bodies (as we would expect in
    # regular usage).
    payload['comment']['body'] = 'multiple words {}'.format(EICAR)
    if 'action' in payload:
        payload['action'] = action

    assert scan_for_secrets(event, payload)


@pytest.mark.parametrize(
    'action',
    {
        'created',
        'edited',
    },
)
@pytest.mark.parametrize(
    'event',
    {
        'commit_comment',
        'issue_comment',
        'pull_request_review_comment',
    },
)
def test_comment_no_secret(event, action):
    payload = get_payload(event)
    if 'action' in payload:
        payload['action'] = action

    assert not scan_for_secrets(event, payload)


@pytest.mark.parametrize(
    'event',
    {
        'commit_comment',
        'issue_comment',
        'pull_request_review_comment',
    },
)
def test_comment_deleted(event):
    payload = get_payload(event)
    payload['comment']['body'] = 'multiple words {}'.format(EICAR)
    if 'action' in payload:
        payload['action'] = 'deleted'

    assert not scan_for_secrets(event, payload)


@pytest.mark.parametrize(
    'event_key',
    {
        'issues,issue',
        'pull_request,pull_request',
    },
)
@pytest.mark.parametrize(
    'action',
    {
        'opened',
        'edited',
    },
)
def test_issue_success(event_key, action):
    event, key = event_key.split(',')
    payload = get_payload(event)
    payload['action'] = action
    payload[key]['body'] = 'multiple words {}'.format(EICAR)

    assert scan_for_secrets(event, payload)


@pytest.mark.parametrize(
    'event_key',
    {
        'issues,issue',
        'pull_request,pull_request',
    },
)
@pytest.mark.parametrize(
    'action',
    {
        'opened',
        'edited',
    },
)
def test_issue_no_secret(event_key, action):
    event, key = event_key.split(',')
    payload = get_payload(event)
    payload['action'] = action

    assert not scan_for_secrets(event, payload)


@pytest.mark.parametrize(
    'event_key',
    {
        'issues,issue',
        'pull_request,pull_request',
    },
)
def test_issue_not_applicable(event_key):
    event, key = event_key.split(',')
    payload = get_payload(event)
    payload['action'] = 'deleted'
    payload[key]['body'] = 'multiple words {}'.format(EICAR)

    assert not scan_for_secrets(event, payload)


def get_payload(name):
    filepath = os.path.join(
        os.path.dirname(__file__),
        '../../../testing/github/',
        '{}.json'.format(name),
    )

    with open(filepath) as f:
        return json.loads(f.read())
