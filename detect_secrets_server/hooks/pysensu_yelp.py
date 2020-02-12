"""
Example config file (yaml) format:

    # Name needs to be one word
    name: SecretFound
    alert_after: 0

    # -1 denotes exponential backoff
    realert_every: -1
    runbook: no-runbook-available
    dependencies: []
    team: team-security
    irc_channels: []
    notification_email: to-whom-it-may-concern@example.com
    ticket: False
    project: False
    page: False
    tip: detect_secrets found a secret

    # status needs to be 1 (warning) or higher to send the email
    status: 1

    # null turns into None
    ttl: null

This will send an alert to Sensu, with the above configurations.
See https://github.com/Yelp/pysensu-yelp for more details.
"""
import pysensu_yelp
import yaml

from .base import BaseHook


class PySensuYelpHook(BaseHook):

    def __init__(self, config):
        """
        :type config: str, yaml formatted
        """
        self.config_data = yaml.safe_load(config)

    def alert(self, repo_name, secrets):
        self.config_data['output'] = "In repo " + repo_name + "\n" + str(secrets)
        pysensu_yelp.send_event(**self.config_data)
