# -*- coding: utf-8 -*-

import itertools
import time
import feedparser

from five import grok

from Products.CMFCore.utils import getToolByName

from vindula.clipping.interfaces import IVindulaClipping

grok.templatedir("templates")


class VindulaClippingView(grok.View):
    grok.name('view')
    grok.permissions("Zope2.View")
    grok.context(IVindulaClipping)

    def update(self):
        self.catalog = getToolByName(self.context, 'portal_catalog')
        self.portal = getToolByName(self.context, "portal_url").getPortalObject()

    def get_feeds(self):
        return self.context.feeds

    def cleanFeed(self, feed):
        """Sanitize the feed.
        """
        for entry in feed.entries:
            entry["feed"]=feed.feed
            if not "published_parsed" in entry:
                entry["published_parsed"]=entry["updated_parsed"]
                entry["published"]=entry["updated"]

    def get_feed(self, url):
        """ Pega um feed.
        """
        feed = feedparser.parse(url)
        self.cleanFeed(feed)
        return feed
