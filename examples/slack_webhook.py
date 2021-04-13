#!/usr/bin/env python3.6		            '
"""
Sample config.ini
[Slack]
webhook = https://hooks.slack.com/services/TXXXXX/BXXXXX
"""
import configparser
import json
import sys

from slack_webhook import Slack


def main():
    # leaving this so cron picks up this output as doublecheck
    print('repo:', sys.argv[1])
    print(json.dumps(json.loads(sys.argv[2]), indent=2, sort_keys=True))

    # pull Slack webhook out of config file
    # Use ConfigParser to build necessary secrets for integrations
    config = configparser.ConfigParser()
    config.read('config.ini')
    slack = Slack(url=config['Slack']['webhook'])

    # build variables for this wacky json
    # there'll only ever be one repo
    repo = sys.argv[1]
    payload = json.loads(sys.argv[2])

    filepaths = list(payload.keys())
    for filepath in filepaths:
        potential_secrets = payload[filepath]
        for potential_secret in potential_secrets:
            author = potential_secret['author']
            commit = potential_secret['commit']
            detected_type = potential_secret['type']
            line_number = potential_secret['line_number']

            # build the message using Slack's "legacy" attachment
            slack.post(text="<insert funny gerblin gibberish>",
                       attachments=[{
                           "fallback": "Required plain-text summary of the attachment.",
                           "color": "#36a64f",
                           "title": "repo: {}".format(repo),
                           "title_link": "https://www.github.com/{}/blob/{}/{}#L{}".format(repo, commit, filepath, line_number),
                           "text": "File: {}".format(filepath),
                           "fields": [
                               {
                                   "title": "Type",
                                   "value": detected_type,
                                   "short": "true"
                               },
                               {
                                   "title": "Author",
                                   "value": author,
                                   "short": "true"
                               }, {
                                   "title": "Commit",
                                   "value": commit,
                                   "short": "false"
                               }
                           ]
                       }]
                       )


if __name__ == '__main__':
    main()
