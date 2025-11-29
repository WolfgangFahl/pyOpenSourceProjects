"""Created on 2024-08-27.

@author: wf
"""

import time
import unittest

from osprojects.github_api import GitHubAction, GitHubApi
from tests.basetest import BaseTest


class TestGitHubApi(BaseTest):
    """Test the GithHubApi functionalities."""

    def setUp(self, debug=False, profile=True):
        BaseTest.setUp(self, debug=debug, profile=profile)
        self.github = GitHubApi.get_instance()

    def test_repos_for_owner(self):
        """Test the repos_for_owner method for two owners, with caching in
        between."""
        owners = ["WolfgangFahl", "BITPlan"]
        cache_expiry = 300  # 5 minutes

        for owner in owners:
            repos = {}
            for trial in range(5):
                # First request - should hit the API
                repos[trial] = self.github.repos_for_owner(
                    owner, cache_expiry=cache_expiry
                )

                # Wait a bit before the next request
                time.sleep(0.05)
                if trial > 0:
                    # Assert that both responses are the same
                    self.assertEqual(
                        repos[0], repos[trial], f"Cache was not used for {owner}"
                    )

    @unittest.skipIf(BaseTest.inPublicCI(), "missing admin rights in public CI")
    def test_github_action_from_url(self):
        """Test creating GitHubAction instances from URLs."""
        test_cases = [
            (
                "single_failure",
                "https://github.com/WolfgangFahl/pyOnlineSpreadSheetEditing/actions/runs/10571934380/job/29288830929",
            ),
            (
                "success",
                "https://github.com/WolfgangFahl/py-sidif/actions/runs/10228791653/job/28301694479",
            ),
            (
                "multiple_failures",
                "https://github.com/WolfgangFahl/scan2wiki/actions/runs/10557241724/job/29244366904",
            ),
            (
                "authorization",
                "https://github.com/WolfgangFahl/pyOpenSourceProjects/actions/runs/10573294825/job/29292512092",
            ),
        ]

        for name, url in test_cases:
            for _trial in range(4):
                with self.subTest(name=name):
                    # Create GitHubAction instance from URL
                    action = GitHubAction.from_url(url)

                    # Assert that the action instance was created successfully
                    self.assertIsNotNone(
                        action, f"GitHubAction instance creation failed for {name}"
                    )

                    # Fetch logs to ensure no exceptions are raised
                    action.fetch_logs()

                    # Assert that logs were fetched successfully
                    self.assertTrue(
                        len(action.log_content) > 0, f"Failed to fetch logs for {name}"
                    )
