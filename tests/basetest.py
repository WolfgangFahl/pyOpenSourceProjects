"""Created on 2021-08-19.

@author: wf
"""

import getpass
import io
import os
import time
import unittest
from contextlib import redirect_stdout
from typing import Callable, Type
from unittest import TestCase


class BaseTest(TestCase):
    """Base test case."""

    def setUp(self, debug=False, profile=True):
        """SetUp test environment."""
        TestCase.setUp(self)
        self.debug = debug
        self.profile = profile
        msg = f"test {self._testMethodName}, debug={self.debug}"
        self.profiler = Profiler(msg, profile=self.profile)

    def tearDown(self):
        TestCase.tearDown(self)
        self.profiler.time()

    @staticmethod
    def inPublicCI():
        """Are we running in a public Continuous Integration Environment?"""
        publicCI = getpass.getuser() in ["travis", "runner"]
        jenkins = "JENKINS_HOME" in os.environ
        return publicCI or jenkins

    @staticmethod
    def getSampleDictById(entityClass: Type, keyAttr: str, keyValue) -> dict:
        """

        Args:

        """
        if hasattr(entityClass, "getSamples") and callable(entityClass.getSamples):
            samples = entityClass.getSamples()
            if isinstance(samples, list):
                for record in samples:
                    if keyAttr in record and record.get(keyAttr) == keyValue:
                        return record

    @staticmethod
    def getSampleById(entityClass: Type, keyAttr: str, keyValue):
        """

        Args:

        """
        record = BaseTest.getSampleDictById(entityClass, keyAttr, keyValue)
        entity = entityClass()
        for k, v in record.items():
            setattr(entity, k, v)
        return entity

    @staticmethod
    def captureOutput(fn: Callable, *args, **kwargs) -> str:
        """Captures stdout put of the given function.

        Args:
            fn(callable): function to call
        Returns:
            str
        """
        f = io.StringIO()
        with redirect_stdout(f):
            fn(*args, **kwargs)
        f.seek(0)
        output = f.read()
        return output


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()


class Profiler:
    """Simple profiler."""

    def __init__(self, msg, profile=True):
        """Construct me with the given msg and profile active flag.

        Args:
            msg(str): the message to show if profiling is active
            profile(bool): True if messages should be shown
        """
        self.msg = msg
        self.profile = profile
        self.starttime = time.time()
        if profile:
            print(f"Starting {msg} ...")

    def time(self, extraMsg=""):
        """Time the action and print if profile is active."""
        elapsed = time.time() - self.starttime
        if self.profile:
            print(f"{self.msg}{extraMsg} took {elapsed:5.1f} s")
        return elapsed
