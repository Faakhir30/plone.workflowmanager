# -*- coding: utf-8 -*-
from plone.app.testing import ROBOT_TEST_LEVEL
from plone.testing import layered
from plone.workflowmanager.testing import (  # noqa: E501
    PLONE_WORKFLOWMANAGER_ACCEPTANCE_TESTING,
)

import os
import robotsuite
import unittest


def test_suite():
    suite = unittest.TestSuite()
    current_dir = os.path.abspath(os.path.dirname(__file__))
    robot_dir = os.path.join(current_dir, "robot")
    robot_tests = [
        os.path.join("robot", doc)
        for doc in os.listdir(robot_dir)
        if doc.endswith(".robot") and doc.startswith("test_")
    ]
    for robot_test in robot_tests:
        robottestsuite = robotsuite.RobotTestSuite(robot_test)
        robottestsuite.level = ROBOT_TEST_LEVEL
        suite.addTests(
            [
                layered(
                    robottestsuite,
                    layer=PLONE_WORKFLOWMANAGER_ACCEPTANCE_TESTING,
                ),
            ]
        )
    return suite
