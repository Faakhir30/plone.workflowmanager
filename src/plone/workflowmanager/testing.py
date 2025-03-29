# -*- coding: utf-8 -*-
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2

import plone.workflowmanager


class PloneWorkflowmanagerLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        import plone.app.dexterity

        self.loadZCML(package=plone.app.dexterity)
        import plone.restapi

        self.loadZCML(package=plone.restapi)
        self.loadZCML(package=plone.workflowmanager)

    def setUpPloneSite(self, portal):
        applyProfile(portal, "plone.workflowmanager:default")


PLONE_WORKFLOWMANAGER_FIXTURE = PloneWorkflowmanagerLayer()


PLONE_WORKFLOWMANAGER_INTEGRATION_TESTING = IntegrationTesting(
    bases=(PLONE_WORKFLOWMANAGER_FIXTURE,),
    name="PloneWorkflowmanagerLayer:IntegrationTesting",
)


PLONE_WORKFLOWMANAGER_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(PLONE_WORKFLOWMANAGER_FIXTURE,),
    name="PloneWorkflowmanagerLayer:FunctionalTesting",
)


PLONE_WORKFLOWMANAGER_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        PLONE_WORKFLOWMANAGER_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE,
    ),
    name="PloneWorkflowmanagerLayer:AcceptanceTesting",
)
