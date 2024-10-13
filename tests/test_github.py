"""
Created on 27.08.2024

@author: wf
"""

import os
import unittest

from osprojects.action_log import (
    GitHubWorkflowAnalyzer,
    TestSummary,
    WorkflowRunAnalysis,
)
from osprojects.osproject import GitHubRepo, OsProject, OsProjects
from tests.basetest import BaseTest


class TestGitHub(BaseTest):
    """
    tests GitHub class
    """

    def setUp(self, debug=True, profile=True):
        BaseTest.setUp(self, debug=debug, profile=profile)

    def test_GitHubRepo_from_url(self):
        """
        tests the creating GitHubRepos from the project url
        """
        urlCases = [
            {
                "owner": "WolfgangFahl",
                "project": "pyOpenSourceProjects",
                "variants": [
                    "https://github.com/WolfgangFahl/pyOpenSourceProjects",
                    "http://github.com/WolfgangFahl/pyOpenSourceProjects",
                    "git@github.com:WolfgangFahl/pyOpenSourceProjects",
                ],
            },
            {
                "owner": "ad-freiburg",
                "project": "qlever",
                "variants": ["https://github.com/ad-freiburg/qlever"],
            },
        ]
        for urlCase in urlCases:
            urlVariants = urlCase["variants"]
            expectedOwner = urlCase["owner"]
            expectedProject = urlCase["project"]
            for url in urlVariants:
                github_repo = GitHubRepo.from_url(url)
                self.assertEqual(expectedOwner, github_repo.owner)
                self.assertEqual(expectedProject, github_repo.project_id)

    def testOsProjects(self):
        """
        tests the list_projects_as_os_projects method
        """
        owner = "WolfgangFahl"
        project_id = "pyOpenSourceProjects"
        osprojects = OsProjects.from_owners([owner])

        debug = self.debug
        # debug = True
        if debug:
            index = 0
            for owner, projects in osprojects.projects.items():
                for project in projects:
                    index += 1
                    print(f"{index:3}:{owner}:{project}")
        self.assertTrue(owner in osprojects.projects)
        projects = osprojects.projects[owner]
        self.assertIsInstance(projects, dict)
        self.assertTrue(len(projects) > 0, "No projects found for WolfgangFahl")
        # Check if pyOpenSourceProjects is in the list
        self.assertTrue(project_id in projects)
        pyosp_found = projects[project_id]
        self.assertTrue(
            pyosp_found, "pyOpenSourceProjects not found in the list of projects"
        )

        # Test a sample project's structure
        sample_project = projects["py-yprinciple-gen"]
        expected_attributes = {
            "project_id",
            "owner",
            "title",
            "url",
            "description",
            "language",
            "created_at",
            "updated_at",
            "stars",
            "forks",
        }
        self.assertTrue(
            all(hasattr(sample_project, attr) for attr in expected_attributes),
            "OsProject instance is missing expected attributes",
        )

        # Check if all items are OsProject instances
        self.assertTrue(
            all(isinstance(project, OsProject) for project in projects.values()),
            "Not all items are OsProject instances",
        )

    @unittest.skipIf(
        BaseTest.inPublicCI(),
        "Tests querying wikidata which is often blocked on public CI",
    )
    def test_projects_from_folder(self):
        """
        test projects from a specific folder
        """
        debug = self.debug
        # debug=True
        home_dir = os.path.expanduser("~")
        folder_path = os.path.join(home_dir, "py-workspace")
        osprojects = OsProjects.from_folder(folder_path)
        count = len(osprojects.local_projects)
        if debug:
            print(f"found {count} local projects")
        self.assertTrue(count > 30)
        pass

    def test_log_analysis(self):
        """
        test example logs
        """
        logs = [
            {
                "url": "https://github.com/WolfgangFahl/scan2wiki/actions/runs/10557241724/job/29244366904",
                "log": """EEEEEEEE
======================================================================
ERROR: tests.test_amazon (unittest.loader._FailedTest)
----------------------------------------------------------------------
ImportError: Failed to import test module: tests.test_amazon
Traceback (most recent call last):
  File "/opt/hostedtoolcache/Python/3.10.14/x64/lib/python3.10/unittest/loader.py", line 436, in _find_test_path
    module = self._get_module_from_name(name)
  File "/opt/hostedtoolcache/Python/3.10.14/x64/lib/python3.10/unittest/loader.py", line 377, in _get_module_from_name
    __import__(name)
  File "/home/runner/work/scan2wiki/scan2wiki/tests/test_amazon.py", line 6, in <module>
    from ngwidgets.basetest import Basetest
ModuleNotFoundError: No module named 'ngwidgets'


======================================================================
ERROR: tests.test_barcode (unittest.loader._FailedTest)
----------------------------------------------------------------------
ImportError: Failed to import test module: tests.test_barcode
Traceback (most recent call last):
  File "/opt/hostedtoolcache/Python/3.10.14/x64/lib/python3.10/unittest/loader.py", line 436, in _find_test_path
    module = self._get_module_from_name(name)
  File "/opt/hostedtoolcache/Python/3.10.14/x64/lib/python3.10/unittest/loader.py", line 377, in _get_module_from_name
    __import__(name)
  File "/home/runner/work/scan2wiki/scan2wiki/tests/test_barcode.py", line 8, in <module>
    from ngwidgets.basetest import Basetest
ModuleNotFoundError: No module named 'ngwidgets'


======================================================================
ERROR: tests.test_product (unittest.loader._FailedTest)
----------------------------------------------------------------------
ImportError: Failed to import test module: tests.test_product
Traceback (most recent call last):
  File "/opt/hostedtoolcache/Python/3.10.14/x64/lib/python3.10/unittest/loader.py", line 436, in _find_test_path
    module = self._get_module_from_name(name)
  File "/opt/hostedtoolcache/Python/3.10.14/x64/lib/python3.10/unittest/loader.py", line 377, in _get_module_from_name
    __import__(name)
  File "/home/runner/work/scan2wiki/scan2wiki/tests/test_product.py", line 9, in <module>
    from ngwidgets.basetest import Basetest
ModuleNotFoundError: No module named 'ngwidgets'


======================================================================
ERROR: tests.test_scans (unittest.loader._FailedTest)
----------------------------------------------------------------------
ImportError: Failed to import test module: tests.test_scans
Traceback (most recent call last):
  File "/opt/hostedtoolcache/Python/3.10.14/x64/lib/python3.10/unittest/loader.py", line 436, in _find_test_path
    module = self._get_module_from_name(name)
  File "/opt/hostedtoolcache/Python/3.10.14/x64/lib/python3.10/unittest/loader.py", line 377, in _get_module_from_name
    __import__(name)
  File "/home/runner/work/scan2wiki/scan2wiki/tests/test_scans.py", line 9, in <module>
    from ngwidgets.basetest import Basetest
ModuleNotFoundError: No module named 'ngwidgets'


======================================================================
ERROR: tests.testdms (unittest.loader._FailedTest)
----------------------------------------------------------------------
ImportError: Failed to import test module: tests.testdms
Traceback (most recent call last):
  File "/opt/hostedtoolcache/Python/3.10.14/x64/lib/python3.10/unittest/loader.py", line 436, in _find_test_path
    module = self._get_module_from_name(name)
  File "/opt/hostedtoolcache/Python/3.10.14/x64/lib/python3.10/unittest/loader.py", line 377, in _get_module_from_name
    __import__(name)
  File "/home/runner/work/scan2wiki/scan2wiki/tests/testdms.py", line 6, in <module>
    from ngwidgets.basetest import Basetest
ModuleNotFoundError: No module named 'ngwidgets'


======================================================================
ERROR: tests.testfolderwatch (unittest.loader._FailedTest)
----------------------------------------------------------------------
ImportError: Failed to import test module: tests.testfolderwatch
Traceback (most recent call last):
  File "/opt/hostedtoolcache/Python/3.10.14/x64/lib/python3.10/unittest/loader.py", line 436, in _find_test_path
    module = self._get_module_from_name(name)
  File "/opt/hostedtoolcache/Python/3.10.14/x64/lib/python3.10/unittest/loader.py", line 377, in _get_module_from_name
    __import__(name)
  File "/home/runner/work/scan2wiki/scan2wiki/tests/testfolderwatch.py", line 9, in <module>
    from apscheduler.schedulers.background import BackgroundScheduler
ModuleNotFoundError: No module named 'apscheduler'


======================================================================
ERROR: tests.testpdfextract (unittest.loader._FailedTest)
----------------------------------------------------------------------
ImportError: Failed to import test module: tests.testpdfextract
Traceback (most recent call last):
  File "/opt/hostedtoolcache/Python/3.10.14/x64/lib/python3.10/unittest/loader.py", line 436, in _find_test_path
    module = self._get_module_from_name(name)
  File "/opt/hostedtoolcache/Python/3.10.14/x64/lib/python3.10/unittest/loader.py", line 377, in _get_module_from_name
    __import__(name)
  File "/home/runner/work/scan2wiki/scan2wiki/tests/testpdfextract.py", line 6, in <module>
    from ngwidgets.basetest import Basetest
ModuleNotFoundError: No module named 'ngwidgets'


======================================================================
ERROR: tests.testupload (unittest.loader._FailedTest)
----------------------------------------------------------------------
ImportError: Failed to import test module: tests.testupload
Traceback (most recent call last):
  File "/opt/hostedtoolcache/Python/3.10.14/x64/lib/python3.10/unittest/loader.py", line 436, in _find_test_path
    module = self._get_module_from_name(name)
  File "/opt/hostedtoolcache/Python/3.10.14/x64/lib/python3.10/unittest/loader.py", line 377, in _get_module_from_name
    __import__(name)
  File "/home/runner/work/scan2wiki/scan2wiki/tests/testupload.py", line 8, in <module>
    from ngwidgets.basetest import Basetest
ModuleNotFoundError: No module named 'ngwidgets'


----------------------------------------------------------------------
Ran 8 tests in 0.001s

FAILED (errors=8))
    """,
                "expectations": {
                    "build_status": "failed",
                    "num_failed_tests": 8,
                    "failed_test_name": "tests.test_amazon (unittest.loader._FailedTest)",
                    "error_message": "Failed to import test module: tests.test_amazon",
                },
            },
            {
                "url": "https://github.com/WolfgangFahl/py-sidif/actions/runs/10228791653/job/28301694395",
                "log": """Ran 5 tests in 0.527s
    Starting test testExamples, debug=False ...
    test testExamples, debug=False took 0.4 s
    Starting test testGrammars, debug=False ...
    test testGrammars, debug=False took 0.0 s
    Starting test testIsA, debug=False ...
    test testIsA, debug=False took 0.1 s
    Starting test testURLRegex, debug=False ...
    test testURLRegex, debug=False took 0.0 s

    OK""",
                "expectations": {
                    "build_status": "succeeded",
                    "num_failed_tests": 0,
                    "total_tests": 5,
                    "time_taken": 0.527,
                },
            },
            {
                "url": "https://github.com/WolfgangFahl/pyOnlineSpreadSheetEditing/actions/runs/10571934380/job/29288830929",
                "log": """FAIL: testSPARQLQuery (tests.test_tableQuery.TestTableQuery)
    test SPARQL Query support
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "/home/runner/work/pyOnlineSpreadSheetEditing/pyOnlineSpreadSheetEditing/tests/test_tableQuery.py", line 206, in testSPARQLQuery
        self.assertTrue("Delhi" in citiesByLabel)
    AssertionError: False is not true

    ----------------------------------------------------------------------
    Ran 10 tests in 4.462s

    FAILED (failures=1)""",
                "expectations": {
                    "build_status": "failed",
                    "num_failed_tests": 1,
                    "failed_test_name": "testSPARQLQuery (tests.test_tableQuery.TestTableQuery)",
                    "total_tests": 10,
                    "time_taken": 4.462,
                    "num_failures": 1,
                },
            },
        ]

        gwa = GitHubWorkflowAnalyzer()
        for test_case in logs:
            with self.subTest(url=test_case["url"]):
                analysis = gwa.extract_log_info(test_case["log"])
                print(f"\nAnalysis for {test_case['url']}:")
                analysis.show()

                # Verify the analysis against expectations
                exp = test_case["expectations"]
                self.assertEqual(analysis.build_status, exp["build_status"])
                self.assertEqual(len(analysis.failed_tests), exp["num_failed_tests"])

                if exp["build_status"] == "failed":
                    self.assertEqual(
                        analysis.failed_tests[0].name, exp["failed_test_name"]
                    )
                    if "error_message" in exp:
                        self.assertEqual(
                            analysis.failed_tests[0].error, exp["error_message"]
                        )

                if "total_tests" in exp:
                    self.assertEqual(
                        analysis.test_summary.total_tests, exp["total_tests"]
                    )
                if "time_taken" in exp:
                    self.assertAlmostEqual(
                        analysis.test_summary.time_taken, exp["time_taken"], places=3
                    )
                if "num_failures" in exp:
                    self.assertEqual(
                        analysis.test_summary.num_failures, exp["num_failures"]
                    )

    def testWorkflowRunAnalysis(self):
        """
        Test the workflow run analysis functionality with multiple cases.
        """
        test_cases = [
            (
                "single_failure",
                "https://github.com/WolfgangFahl/pyOnlineSpreadSheetEditing/actions/runs/10571934380/job/29288830929",
                "failed",
                1,
            ),
            (
                "success",
                "https://github.com/WolfgangFahl/py-sidif/actions/runs/10228791653/job/28301694479",
                "succeeded",
                0,
            ),
            (
                "multiple_failures",
                "https://github.com/WolfgangFahl/scan2wiki/actions/runs/10557241724/job/29244366904",
                "failed",
                3,  # Adjust this number based on actual failures
            ),
            (
                "authorization",
                "https://github.com/WolfgangFahl/pyOpenSourceProjects/actions/runs/10573294825/job/29292512092",
                "failed",
                6,  # Expecting 6 failures
            ),
        ]

        gwa = GitHubWorkflowAnalyzer()

        for case_name, url, expected_status, expected_failures in test_cases:
            with self.subTest(case=case_name):
                analysis = gwa.analyze_workflow_run(url, save_log=True)

                self.assertIsInstance(analysis, WorkflowRunAnalysis)
                self.assertEqual(analysis.build_status, expected_status)
                self.assertIsInstance(analysis.failed_tests, list)
                self.assertEqual(len(analysis.failed_tests), expected_failures)
                self.assertIsInstance(analysis.test_summary, TestSummary)
                self.assertEqual(analysis.test_summary.num_failures, expected_failures)

                print(f"\nAnalysis for {case_name}:")
                analysis.show()

                if self.debug:
                    print("\nDetailed Analysis:")
                    print(f"Number of failed tests: {len(analysis.failed_tests)}")
                    for test in analysis.failed_tests:
                        print(
                            f"Test: {test.name}, File: {test.file}, Line: {test.line}"
                        )
