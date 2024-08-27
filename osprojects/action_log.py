"""
Created on 27.08.2024

action_log module

@author: wf
"""

import re
from dataclasses import dataclass
from typing import List, Optional

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


class ExtendedGitHub(GitHub):
    """
    Extended GitHub class with additional functionality for workflow analysis.
    """

    def get_workflow_run_logs(
        self, owner: str, repo: str, run_id: int, job_id: int
    ) -> str:
        """
        Fetch the logs for a specific job in a GitHub Actions workflow run.

        Args:
            owner (str): The owner of the repository.
            repo (str): The name of the repository.
            run_id (int): The ID of the workflow run.
            job_id (int): The ID of the job within the run.

        Returns:
            str: The log content.
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/jobs/{job_id}/logs"
        log_url = self.get_response("fetch job logs", url, allow_redirects=False)

        log_response = requests.get(log_url)
        return log_response.content.decode("utf-8-sig")

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
        """
        Extract structured information from workflow run logs.

        Args:
            logs (str): The raw log content from a workflow run.

        Returns:
            WorkflowRunAnalysis: Structured analysis of the workflow run.
        """
        blocks = self.extract_test_blocks(logs)
        failed_tests = [
            test for block in blocks if (test := self.parse_test_block(block))
        ]

        build_status = "failed" if failed_tests else "succeeded"

        test_summary_match = re.search(
            r"Ran (\d+) tests? in (\d+\.\d+)s\n\n(OK|FAILED.*)", logs
        )
        if test_summary_match:
            total_tests = int(test_summary_match.group(1))
            time_taken = float(test_summary_match.group(2))
            num_failures = len(failed_tests)
            test_summary = TestSummary(total_tests, time_taken, num_failures)
        else:
            test_summary = TestSummary(0, 0.0, len(failed_tests))

        return WorkflowRunAnalysis(build_status, failed_tests, test_summary)

    def analyze_workflow_run(
        self, owner: str, repo: str, run_id: int, job_id: int
    ) -> WorkflowRunAnalysis:
        """
        Analyze a GitHub Actions workflow run.

        Args:
            owner (str): The owner of the repository.
            repo (str): The name of the repository.
            run_id (int): The ID of the workflow run.
            job_id (int): The ID of the job within the run.

        Returns:
            WorkflowRunAnalysis: Structured analysis of the workflow run.
        """
        logs = self.get_workflow_run_logs(owner, repo, run_id, job_id)
        return self.extract_log_info(logs)
