# -*- coding: utf-8 -*-
"""Base module for unittesting."""

from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.testing.z2 import installProduct
from plone.app.testing import applyProfile

from zope.configuration import xmlconfig


class Fixture(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        """Set up Zope."""
        # Load ZCML
        import vindula.clipping
        xmlconfig.file(
            'configure.zcml',
            vindula.clipping,
            context=configurationContext
        )

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'vindula.clipping:default')

FIXTURE = Fixture()
INTEGRATION_TESTING = IntegrationTesting(
    bases=(FIXTURE,),
    name="vindula.clipping:Integration",
)
FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(FIXTURE,),
    name="vindula.clipping:Functional",
)
