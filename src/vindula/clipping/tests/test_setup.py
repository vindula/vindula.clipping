# -*- coding: utf-8 -*-
"""Setup/installation tests for this package."""

import unittest2 as unittest

from Products.CMFCore.utils import getToolByName

from vindula.clipping.config import PROJECTNAME
from vindula.clipping.testing import INTEGRATION_TESTING
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID


class TestInstall(unittest.TestCase):
    """Test installation of vindula.clipping into Plone."""

    layer = INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.app = self.layer['app']
        self.portal = self.layer['portal']
        self.qi = getToolByName(self.portal, 'portal_quickinstaller')
        self.ttool = getToolByName(self.portal, 'portal_types')

    def test_installed(self):
        self.assertTrue(self.qi.isProductInstalled(PROJECTNAME))

    def test_installedAllTypes(self):
        # test that all types are installed well
        types = self.ttool.listContentTypes()
        ids = ('VindulaClipping',)
        for i in ids:
            self.assertTrue(i in types)


class UninstallTestCase(unittest.TestCase):

    layer = INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.qi = self.portal['portal_quickinstaller']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.qi.uninstallProducts(products=[PROJECTNAME])

    def test_uninstalled(self):
        self.assertFalse(self.qi.isProductInstalled(PROJECTNAME))
