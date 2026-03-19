from ruamel.yaml import YAML
from kubessh.authentication.github import GitHubAuthenticator
from kubessh.authentication.gitlab import GitLabAuthenticator
from kubessh.authentication.dummy import DummyAuthenticator

yaml = YAML()

c.KubeSSH.host_key_path = '/etc/kubessh/secrets/kubessh.host-key'

with open('/etc/kubessh/config/values.yaml') as f:
    config = yaml.load(f)

# Log level: accept 'DEBUG' or 'INFO' from values, default to INFO
log_level = config.get('logLevel', 'INFO').upper()
c.KubeSSH.debug = (log_level == 'DEBUG')

if config['auth']['type'] == 'github':
    c.KubeSSH.authenticator_class = GitHubAuthenticator
    c.GitHubAuthenticator.allowed_users = config['auth']['github'].get('allowedUsers', [])
    c.GitHubAuthenticator.allowed_teams = config['auth']['github'].get('allowedTeams', [])
    # GitHub token is sourced from GITHUB_TOKEN env var only (not stored in ConfigMap)
elif config['auth']['type'] == 'gitlab':
    c.KubeSSH.authenticator_class = GitLabAuthenticator
    c.KubeSSH.authenticator_class.instance_url = config['auth']['gitlab']['instanceUrl']
    c.KubeSSH.authenticator_class.allowed_users = config['auth']['gitlab']['allowedUsers']

elif config['auth']['type'] == 'dummy':
    c.KubeSSH.authenticator_class = DummyAuthenticator

if 'defaultNamespace' in config:
    c.KubeSSH.default_namespace = config['defaultNamespace']

if 'podTemplate' in config:
    c.UserPod.pod_template = config['podTemplate']

if 'deleteGracePeriod' in config:
    c.UserPod.delete_grace_period = int(config['deleteGracePeriod'])

if 'pvcTemplates' in config:
    c.UserPod.pvc_templates = config['pvcTemplates']
