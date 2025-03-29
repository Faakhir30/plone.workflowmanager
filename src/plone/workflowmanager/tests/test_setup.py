# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.workflowmanager.testing import (  # noqa: E501
    PLONE_WORKFLOWMANAGER_INTEGRATION_TESTING,
)

import unittest


try:
    from Products.CMFPlone.utils import get_installer
except ImportError:
    get_installer = None


class TestSetup(unittest.TestCase):
    """Test that plone.workflowmanager is properly installed."""

    layer = PLONE_WORKFLOWMANAGER_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        if get_installer:
            self.installer = get_installer(self.portal, self.layer["request"])
        else:
            self.installer = api.portal.get_tool("portal_quickinstaller")

    def test_product_installed(self):
        """Test if plone.workflowmanager is installed."""
        self.assertTrue(self.installer.is_product_installed("plone.workflowmanager"))

    def test_browserlayer(self):
        """Test that IPloneWorkflowmanagerLayer is registered."""
        from plone.browserlayer import utils
        from plone.workflowmanager.interfaces import IPloneWorkflowmanagerLayer

        self.assertIn(IPloneWorkflowmanagerLayer, utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = PLONE_WORKFLOWMANAGER_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        if get_installer:
            self.installer = get_installer(self.portal, self.layer["request"])
        else:
            self.installer = api.portal.get_tool("portal_quickinstaller")
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.installer.uninstall_product("plone.workflowmanager")
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if plone.workflowmanager is cleanly uninstalled."""
        self.assertFalse(self.installer.is_product_installed("plone.workflowmanager"))

    def test_browserlayer_removed(self):
        """Test that IPloneWorkflowmanagerLayer is removed."""
        from plone.browserlayer import utils
        from plone.workflowmanager.interfaces import IPloneWorkflowmanagerLayer

        self.assertNotIn(IPloneWorkflowmanagerLayer, utils.registered_layers())
