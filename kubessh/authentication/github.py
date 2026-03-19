import os
import sys

from kubessh.authentication import Authenticator
import aiohttp
import asyncssh
from traitlets import List, Unicode

# async_timeout is built into asyncio from Python 3.11+
if sys.version_info >= (3, 11):
    from asyncio import timeout as async_timeout
else:
    from async_timeout import timeout as async_timeout


class GitHubAuthenticator(Authenticator):
    """
    Authenticate with GitHub SSH keys.

    Users are allowed if they appear in ``allowed_users`` OR are a member
    of any team listed in ``ALLOWED_TEAMS`` under the ``GITHUB_ORG``
    organisation.

    Configuration can be provided via traitlets config or environment
    variables:
        GITHUB_TOKEN   – personal access token with read:org scope
        GITHUB_ORG     – GitHub organisation name
        ALLOWED_TEAMS  – comma-separated list of team slugs
    """
    allowed_users = List(
        [],
        config=True,
        help="""
        List of GitHub usernames allowed to log in.
        """
    )

    allowed_teams = List(
        [],
        config=True,
        help="""
        List of GitHub org/team slugs (e.g. 'myorg/myteam') whose members
        are allowed to log in.  If ``github_org`` is set, bare team names
        are automatically prefixed with the org.
        """
    )

    github_token = Unicode(
        '',
        config=True,
        help="""
        GitHub personal access token with read:org scope.
        Required when ``allowed_teams`` is set.
        """
    )

    github_org = Unicode(
        '',
        config=True,
        help="""
        Default GitHub organisation.  When set, team slugs in
        ``allowed_teams`` that don't contain a '/' are treated as
        teams within this org.
        """
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._load_env()
        self.log.debug(
            f"GitHubAuthenticator initialized: "
            f"github_org={self.github_org!r}, "
            f"allowed_teams={self.allowed_teams!r}, "
            f"allowed_users={self.allowed_users!r}, "
            f"github_token={'set' if self.github_token else 'NOT SET'}"
        )

    def _load_env(self):
        """Populate config from environment variables when present.

        Environment variables always take precedence over traitlets config
        so that deploy-time values (set via the Helm env block) win.
        """
        token = os.environ.get('GITHUB_TOKEN', '')
        if token:
            self.github_token = token

        org = os.environ.get('GITHUB_ORG', '')
        if org:
            self.github_org = org

        teams_env = os.environ.get('ALLOWED_TEAMS', '')
        if teams_env:
            # Strip surrounding brackets in case the value comes from a
            # serialised list (e.g. Terraform interpolation: "[team1,team2]")
            teams_env = teams_env.strip('[] ')
            self.allowed_teams = [
                t.strip() for t in teams_env.split(',') if t.strip()
            ]

    def _resolve_teams(self):
        """Return a list of fully-qualified org/team slugs."""
        resolved = []
        for slug in self.allowed_teams:
            if '/' in slug:
                resolved.append(slug)
            elif self.github_org:
                resolved.append(f'{self.github_org}/{slug}')
            else:
                self.log.warning(
                    f"Team slug '{slug}' has no org and github_org is not set, skipping"
                )
        return resolved

    def connection_made(self, conn):
        self.conn = conn

    def public_key_auth_supported(self):
        return True

    async def _is_team_member(self, username):
        """Check if username belongs to any of the allowed teams."""
        teams = self._resolve_teams()
        if not teams or not self.github_token:
            return False

        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json',
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            for team_slug in teams:
                org, team = team_slug.split('/', 1)
                url = (
                    f'https://api.github.com/orgs/{org}'
                    f'/teams/{team}/members/{username}'
                )
                try:
                    async with async_timeout(5):
                        async with session.get(url) as resp:
                            if resp.status == 204:
                                self.log.info(
                                    f"User {username} is a member of {team_slug}"
                                )
                                return True
                            elif resp.status == 404:
                                continue
                            else:
                                self.log.warning(
                                    f"GitHub API returned {resp.status} checking "
                                    f"{username} membership in {team_slug}"
                                )
                except Exception as e:
                    self.log.warning(
                        f"Error checking team membership for {username}: {e}"
                    )
        return False

    async def begin_auth(self, username):
        """
        Fetch and save user's keys for comparison later.
        """
        if username not in self.allowed_users:
            if not await self._is_team_member(username):
                self.log.info(
                    f"User {username} not in allowed_users or allowed_teams, "
                    f"authentication denied"
                )
                return True

        url = f'https://github.com/{username}.keys'
        async with aiohttp.ClientSession() as session, async_timeout(5):
            async with session.get(url) as response:
                keys = await response.text()
        if keys:
            self.conn.set_authorized_keys(asyncssh.import_authorized_keys(keys))
        return True
