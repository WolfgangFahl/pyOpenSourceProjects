"""
Created on 27.08.2024

action_log module

@author: wf
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse
import os
import requests

from osprojects.osproject import GitHub


@dataclass
class FailedTest:
    """
    Represents a failed test in a workflow run.

    Attributes:
        name (str): The name of the failed test.
        error (str): The error message associated with the test failure.
        file (str): The file where the test failure occurred. Empty string if unknown.
        line (int): The line number where the test failure occurred. 0 if unknown.
    """

    name: str
    error: str
    file: str = ""
    line: int = 0

    def show(self):
        """
        Display the details of the failed test.
        """
        print(f"Failed test: {self.name}")
        print(f"Error: {self.error}")
        if self.file and self.line:
            print(f"Location: {self.file}:{self.line}")
        print()


@dataclass
class TestSummary:
    """
    Summarizes the results of a test run.

    Attributes:
        total_tests (int): The total number of tests run.
        time_taken (float): The time taken to run all tests, in seconds.
        num_failures (int): The number of tests that failed.
    """

    total_tests: int
    time_taken: float
    num_failures: int

    def show(self):
        """
        Display the test summary.
        """
        print(f"Test Summary:")
        print(f"Total tests: {self.total_tests}")
        print(f"Time taken: {self.time_taken:.2f}s")
        print(f"Number of failures: {self.num_failures}")


@dataclass
class WorkflowRunAnalysis:
    """
    Represents the analysis of a workflow run.

    Attributes:
        build_status (str): The overall status of the build ("succeeded" or "failed").
        failed_tests (List[FailedTest]): A list of FailedTest objects for any failed tests.
        test_summary (TestSummary): A TestSummary object summarizing the test run.
    """

    build_status: str
    failed_tests: List[FailedTest]
    test_summary: TestSummary

    def show(self):
        """
        Display the complete workflow run analysis.
        """
        print(f"Build Status: {self.build_status}")
        if self.build_status == "failed":
            print("\nFailed Tests:")
            for test in self.failed_tests:
                test.show()
        self.test_summary.show()

@dataclass
class GitHubAction:
    """
    Represents a GitHub Action with its identifying information and log content.

    Attributes:
        owner (str): The owner of the repository.
        repo (str): The name of the repository.
        run_id (int): The ID of the workflow run.
        job_id (int): The ID of the job within the run.
        log_content (str): The log content of the action.
    """
    owner: str
    repo: str
    run_id: int
    job_id: int
    log_content: str = field(default="", repr=False)

    @classmethod
    def from_url(cls, url: str, github: GitHub) -> 'GitHubAction':
        """
        Create a GitHubAction instance from a GitHub Actions URL and fetch its logs.

        Args:
            url (str): The GitHub Actions URL.
            github (GitHub): An instance of the GitHub class for making API requests.

        Returns:
            GitHubAction: An instance of GitHubAction containing parsed information and log content.

        Raises:
            ValueError: If the URL format is invalid or missing required components.
        """
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.split('/')

        if len(path_parts) < 8 or path_parts[3] != 'actions' or path_parts[4] != 'runs':
            raise ValueError("Invalid GitHub Actions URL format")

        try:
            action = cls(
                owner=path_parts[1],
                repo=path_parts[2],
                run_id=int(path_parts[5]),
                job_id=int(path_parts[7])
            )
            action.fetch_logs(github)
            return action
        except (IndexError, ValueError) as e:
            raise ValueError(f"Failed to parse GitHub Actions URL: {e}")

    def fetch_logs(self, github: GitHub):
        """
        Fetch the logs for this GitHub Action.

        Args:
            github (GitHub): An instance of the GitHub class for making API requests.
        """
        api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/actions/jobs/{self.job_id}/logs"
        log_response = github.get_response("fetch job logs", api_url, allow_redirects=True)
        self.log_content = log_response.content.decode("utf-8-sig")

    def save_log(self):
        """
        Save the log content to a local file.
        """
        if not self.log_content:
            raise ValueError("No log content to save. Make sure to fetch logs first.")

        home_dir = os.path.expanduser("~")
        log_dir = os.path.join(home_dir, ".github")
        os.makedirs(log_dir, exist_ok=True)

        log_id = f"{self.owner}_{self.repo}_{self.run_id}_{self.job_id}"
        log_file = os.path.join(log_dir, f"action_log_{log_id}.txt")

        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(self.log_content)

        print(f"Log saved to: {log_file}")

class ExtendedGitHub(GitHub):
    """
    Extended GitHub class with additional functionality for workflow analysis.
    """

    def analyze_workflow_run(self, url: str, save_log: bool = False) -> WorkflowRunAnalysis:
        """
        Analyze a GitHub Actions workflow run.

        Args:
            url (str): The GitHub Actions URL.
            save_log (bool): Whether to save a copy of the log locally.

        Returns:
            WorkflowRunAnalysis: Structured analysis of the workflow run.
        """
        action = GitHubAction.from_url(url, self)

        if save_log:
            action.save_log()

        return self.extract_log_info(action.log_content)

    def extract_test_blocks(self, logs: str) -> List[str]:
        """
        Extract individual test result blocks from the log.

        Args:
            logs (str): The complete log content.

        Returns:
            List[str]: A list of individual test result blocks.
        """
        # This pattern looks for blocks starting with "======" or "FAIL:" and ending with a blank line or end of string
        blocks = re.findall(r"((?:======|FAIL:).*?(?:\n\n|\Z))", logs, re.DOTALL)
        return blocks

    def parse_test_block(self, block: str) -> Optional[FailedTest]:
        """
        Parse a single test block and extract relevant information.

        Args:
            block (str): A single test result block.

        Returns:
            Optional[FailedTest]: A FailedTest object if the test failed, None otherwise.
        """
        if "ERROR:" in block or "FAIL:" in block:
            test_name_match = re.search(r"(ERROR|FAIL): (.+?)(\s\(|$)", block)
            error_message_match = re.search(
                r"(AssertionError|Error|ImportError): (.+?)$", block, re.MULTILINE
            )
            file_info_match = re.search(r'File "(.+?)", line (\d+)', block)

            if test_name_match:
                name = test_name_match.group(2)
                error = (
                    error_message_match.group(2)
                    if error_message_match
                    else "Unknown error"
                )
                file = file_info_match.group(1) if file_info_match else ""
                line = int(file_info_match.group(2)) if file_info_match else 0

                return FailedTest(name, error, file, line)
        return None

    def extract_log_info(self, logs: str) -> WorkflowRunAnalysis:
        failed_tests = []
        total_tests = 0
        time_taken = 0.0

        # Extract failed and error tests
        test_blocks = re.findall(r'((?:FAIL|ERROR): .*?(?=\n\n|\Z))', logs, re.DOTALL)
        for block in test_blocks:
            name_match = re.search(r'(?:FAIL|ERROR): (.+)', block)
            error_match = re.search(r'(AssertionError|Error|Exception|ImportError): (.+?)$', block, re.MULTILINE)
            file_match = re.search(r'File "(.+?)", line (\d+)', block)

            if name_match and error_match:
                failed_tests.append(FailedTest(
                    name=name_match.group(1),
                    error=error_match.group(2),
                    file=file_match.group(1) if file_match else "",
                    line=int(file_match.group(2)) if file_match else 0
                ))

        # Extract total tests and time taken
        summary_match = re.search(r'Ran (\d+) tests? in (\d+\.\d+)s', logs)
        if summary_match:
            total_tests = int(summary_match.group(1))
            time_taken = float(summary_match.group(2))

        # Check for overall failure
        failure_summary = re.search(r'FAILED \((.+?)\)', logs)
        if failure_summary:
            build_status = "failed"
        else:
            build_status = "succeeded"

        test_summary = TestSummary(total_tests, time_taken, len(failed_tests))

        return WorkflowRunAnalysis(build_status, failed_tests, test_summary)

