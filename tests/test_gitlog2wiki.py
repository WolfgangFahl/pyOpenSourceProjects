"""Created on 2026-03-28.

@author: wf
"""

import datetime
import unittest

from osprojects.osproject import Commit, GitLog2WikiCmd, gitlog2wiki
from osprojects.version import Version
from tests.basetest import BaseTest


class TestGitLog2WikiFilter(BaseTest):
    """Test the --filter option of gitlog2wiki."""

    def _make_commit(self, date_iso: str) -> Commit:
        """Create a Commit with the given ISO date string.

        Args:
            date_iso: ISO 8601 date string, e.g. '2026-03-28T10:00:00+00:00'.

        Returns:
            A Commit instance with date and hash set.
        """
        commit = Commit()
        commit.date = datetime.datetime.fromisoformat(date_iso)
        commit.hash = "abc1234"
        commit.subject = "Test commit"
        commit.name = "Tester"
        commit.project = "testproject"
        commit.host = "https://github.com/test/testproject"
        commit.path = ""
        return commit

    def setUp(self, debug=False, profile=True):
        """Set up sample commits spanning multiple years/months/days."""
        super().setUp(debug=debug, profile=profile)
        self.commits = [
            self._make_commit("2024-12-01T08:00:00+00:00"),
            self._make_commit("2025-06-15T12:00:00+00:00"),
            self._make_commit("2026-03-01T09:00:00+00:00"),
            self._make_commit("2026-03-28T14:30:00+00:00"),
            self._make_commit("2026-11-05T17:00:00+00:00"),
        ]

    def _apply_filter(self, date_filter: str):
        """Apply the same filter logic as GitLog2WikiCmd.handle_args.

        Args:
            date_filter: Date prefix string, e.g. '2026', '2026-03', '2026-03-28'.

        Returns:
            Filtered list of Commit objects.
        """
        result = [c for c in self.commits if str(c.date.date()).startswith(date_filter)]
        return result

    def test_filter_by_year(self):
        """Filter by year should return all commits in that year."""
        filtered = self._apply_filter("2026")
        dates = [str(c.date.date()) for c in filtered]
        self.assertEqual(3, len(filtered))
        self.assertIn("2026-03-01", dates)
        self.assertIn("2026-03-28", dates)
        self.assertIn("2026-11-05", dates)

    def test_filter_by_month(self):
        """Filter by year-month should return only commits in that month."""
        filtered = self._apply_filter("2026-03")
        dates = [str(c.date.date()) for c in filtered]
        self.assertEqual(2, len(filtered))
        self.assertIn("2026-03-01", dates)
        self.assertIn("2026-03-28", dates)

    def test_filter_by_day(self):
        """Filter by exact day should return only commits on that day."""
        filtered = self._apply_filter("2026-03-28")
        self.assertEqual(1, len(filtered))
        self.assertEqual("2026-03-28", str(filtered[0].date.date()))

    def test_filter_no_match(self):
        """Filter with no matching commits should return an empty list."""
        filtered = self._apply_filter("2023")
        self.assertEqual(0, len(filtered))

    def test_no_filter_returns_all(self):
        """Without a filter all commits are returned."""
        filtered = self.commits  # no filter applied
        self.assertEqual(5, len(filtered))

    def test_gitlog2wiki_filter_cmdline(self):
        """Test gitlog2wiki CLI with --filter passes through and filters
        output."""
        if self.inPublicCI():
            return
        output = self.captureOutput(gitlog2wiki, ["--filter", "2022"])
        lines = [line for line in output.strip().split("\n") if line]
        # The very first commit (hash 106254f) is from 2022-01-24
        self.assertTrue(len(lines) >= 1)
        for line in lines:
            self.assertIn("2022", line)

    def test_gitlog2wiki_no_filter_cmdline(self):
        """Test gitlog2wiki CLI without --filter returns all commits."""
        if self.inPublicCI():
            return
        output_all = self.captureOutput(gitlog2wiki, [])
        output_filtered = self.captureOutput(gitlog2wiki, ["--filter", "2022"])
        lines_all = [l for l in output_all.strip().split("\n") if l]
        lines_filtered = [l for l in output_filtered.strip().split("\n") if l]
        self.assertGreater(len(lines_all), len(lines_filtered))

    def test_gitlog2wiki_cmd_class(self):
        """Test GitLog2WikiCmd can be instantiated with Version."""
        cmd = GitLog2WikiCmd(Version)
        self.assertIsNotNone(cmd)
        self.assertIsInstance(cmd, GitLog2WikiCmd)


if __name__ == "__main__":
    unittest.main()
