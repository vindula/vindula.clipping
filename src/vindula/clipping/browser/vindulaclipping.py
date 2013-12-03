# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from xml.dom import minidom
from hashlib import md5
import os
import re
import tempfile
import urllib2
from time import time

from plone.memoize import request

from Products.CMFCore.WorkflowCore import WorkflowException

from Products.ATContentTypes.lib import constraintypes
from zExceptions import BadRequest

import feedparser
from DateTime import DateTime
from zope import component
from zope import event
from zope import interface

from five import grok

from Products.CMFCore.utils import getToolByName

from Products.statusmessages.interfaces import IStatusMessage

from vindula.clipping.interfaces import IVindulaClipping

from BeautifulSoup import BeautifulSoup
from HTMLParser import HTMLParseError

grok.templatedir("templates")


def convert_summary(input):
    try:
        value = unicode(BeautifulSoup(
            input, convertEntities=BeautifulSoup.HTML_ENTITIES))
    except HTMLParseError:
        return input
    return value


def update_text(obj, text, mimetype=None):
    field = obj.getField('text')
    if mimetype in field.getAllowedContentTypes(obj):
        obj.setText(text, mimetype=mimetype)
        obj.reindexObject()
    else:
        # update does a reindexObject automatically
        obj.update(text=text)


def get_uid_from_entry(entry):
    """Get a unique id from the entry.
    """
    if hasattr(entry, 'id'):
        value = entry.id
    elif hasattr(entry, 'link'):
        value = entry.link
    else:
        return None
    sig = md5(value.encode('ascii', 'ignore'))
    return sig.hexdigest()


class VindulaClippingView(grok.View):
    grok.name('importar-rss')
    grok.require("zope2.View")
    grok.context(IVindulaClipping)

    def update(self):
        self.catalog = getToolByName(self.context, 'portal_catalog')
        self.portal = getToolByName(self.context, "portal_url").getPortalObject()
        self.pw = getToolByName(self.context, 'portal_workflow')
        self.portal_transforms = getToolByName(self.context, 'portal_transforms')

        titles = self.request.form.get('title', None)
        submitted = self.request.form.get('submit.clipping', None)

        if titles and submitted:
            self.import_feed_items(titles)

    def get_feeds(self):
        return self.context.feeds

    def get_font_title(self, url):
        feed = feedparser.parse(url)
        try:
            title = feed.feed['title']
        except KeyError:
            title = 'Feed desconhecido'

        return title

    def cleanFeed(self, feed):
        """Sanitize the feed.
        """
        for entry in feed.entries:
            entry["feed"]=feed.feed
            if not "published_parsed" in entry['feed']:
                entry["published_parsed"]=entry["updated_parsed"]
                entry["published"]=entry["updated"]

    @request.cache(get_key=lambda func,self:self.get_feeds,
                   get_request="self.request")
    def get_feed(self, url):
        """ Pega um feed.
        """
        feed = feedparser.parse(url)
#        self.cleanFeed(feed)
        return feed.entries

    def folder_day(self):
        publica = self.pw.doActionFor
        ano = str(DateTime().year())
        mes = str(DateTime().month())
        dia = str(DateTime().day())
        folder = self.context

        if not hasattr(self.context, ano):
            try:
                folder.invokeFactory('VindulaFolder', id=ano, title=ano)
                folder = getattr(folder, ano)
                folder.setConstrainTypesMode(constraintypes.ENABLED)
                folder.setLocallyAllowedTypes(['VindulaFolder'])
                folder.setImmediatelyAddableTypes(['VindulaFolder'])
                try:
                    publica(folder,'publish_internally')
                except WorkflowException:
                    publica(folder, 'publish')
            except BadRequest:
                return False
                pass

        else:
            folder = getattr(folder, ano)

        if not hasattr(folder, mes):
            try:
                folder.invokeFactory('VindulaFolder', id=mes, title=mes)
                folder = getattr(folder, mes)
                folder.setConstrainTypesMode(constraintypes.ENABLED)
                folder.setLocallyAllowedTypes(['VindulaFolder'])
                folder.setImmediatelyAddableTypes(['VindulaFolder'])
                try:
                    publica(folder,'publish_internally')
                except WorkflowException:
                    publica(folder, 'publish')
            except BadRequest:
                return False
                pass

        else:
            folder = getattr(folder,mes)

        if not hasattr(folder, dia):
            try:
                folder.invokeFactory('VindulaFolder', id=dia, title=dia)
                folder = getattr(folder, dia)
                folder.setConstrainTypesMode(constraintypes.ENABLED)
                folder.setLocallyAllowedTypes(['VindulaNews'])
                folder.setImmediatelyAddableTypes(['VindulaNews'])
                try:
                    publica(folder,'publish_internally')
                except WorkflowException:
                    publica(folder, 'publish')
            except BadRequest:
                return False
                pass

        else:
            folder = getattr(folder, dia)

        return folder

    def import_feed_items(self, titles):
        entries = []
        urls = self.get_feeds()
        folder = self.folder_day()
        for url in urls:
            for entry in self.get_feed(url):
                entry_dic = {}
                entry_dic['font'] = self.get_font_title(url)
                entry_dic['entry'] = entry
                entries.append(entry_dic)

        for feed in entries:
            font = feed['font']
            entry = feed['entry']
            if entry['title'] in titles:
                id = get_uid_from_entry(entry)
                if not id:
                    continue
                updated = entry.get('updated')
                published = entry.get('published')

                if not updated:
                    # property may be blank if item has never
                    # been updated -- use published date
                    updated = published
                try:
                    folder.invokeFactory('VindulaNews', id=id, title=entry['title'])
                except BadRequest:
                    IStatusMessage(self.request).addStatusMessage('A notícia %s já foi importada anteriormente' % entry['title'], type='error')
                obj = getattr(folder, id)
                obj.setCreators(font,)
                try:
                    self.pw.doActionFor(obj,'publish_internally')
                except WorkflowException:
                    self.pw.doActionFor(obj,'publish')

               
                linkDict = getattr(entry, 'link', None)
                if linkDict:
                    # Hey, that's not a dict at all; at least not in my test.
                    #link = linkDict['href']
                    link = linkDict
                else:
                    linkDict = getattr(entry, 'links', [{'href': ''}])[0]
                    link = linkDict['href']

                if not updated:
                    updated = DateTime()
                if published is not None:
                    try:
                        published = DateTime(published)
                    except DateTime.SyntaxError:
                        continue
                    obj.setEffectiveDate(published)

                summary = getattr(entry, 'summary', '')
                summary = convert_summary(summary)
                obj.update(description=summary)
                feed_tags = [x.get('term') for x in entry.get('tags', [])]
                obj.feed_tags = feed_tags
                content = None
                if hasattr(entry, 'content'):
                    content = entry.content[0]
                    ctype = content.get('type')  # sometimes no type on linux prsr.
                elif hasattr(entry, 'summary_detail'):
                    # If it is a rss feed with a html description use that
                    # as content.
                    ctype = entry.summary_detail.get('type')
                    if ctype in ('text/xhtml', 'application/xhtml+xml',
                                 'text/html'):
                        content = entry.summary_detail
                if content:
                    if ctype in ('text/xhtml', 'application/xhtml+xml'):
                        # Archetypes doesn't make a difference between
                        # html and xhtml, so we set the type to text/html:
                        ctype = 'text/html'
                        # Warning: minidom.parseString needs a byte
                        # string, not a unicode one, so we need to
                        # encode it first, but only for this parsing.
                        # http://evanjones.ca/python-utf8.html
                        encoded_content = content['value'].encode('utf-8')
                        try:
                            doc = minidom.parseString(encoded_content)
                        except:
                            # Might be an ExpatError, but that is
                            # somewhere in a .so file, so we cannot
                            # specifically catch only that error.  One
                            # reason for an ExpatError, is that if there
                            # is no encapsulated tag, minidom parse fails,
                            # so we can try again in that case.
                            encoded_content = "<div>" + encoded_content + "</div>"
                            try:
                                doc = minidom.parseString(encoded_content)
                            except:
                                # Might be that ExpatError again.
                                continue
                        if len(doc.childNodes) > 0 and\
                           doc.firstChild.hasAttributes():
                            handler = None
                            top = doc.firstChild

                            if handler is None:
                                update_text(obj, content['value'], mimetype=ctype)
                            else:
                                handler.apply(top)
                                # Grab the first non-<dl> node and treat
                                # that as the content.
                                actualContent = None
                                for node in top.childNodes:
                                    if node.nodeName == 'div':
                                        actualContent = node.toxml()
                                        update_text(obj, actualContent,
                                            mimetype=ctype)
                                        break
                        else:
                            update_text(obj, content['value'], mimetype=ctype)
                    else:
                        update_text(obj, content['value'], mimetype=ctype)
                    if summary == convert_summary(content['value']):
                        # summary and content is the same so we can cut
                        # the summary.  The transform can stumble over
                        # unicode, so we convert to a utf-8 string.
                        summary = summary.encode('utf-8')
                        data = self.portal_transforms.convert('html_to_text', summary)
                        summary = data.getData()
                        words = summary.split()[:72]
                        summarywords = words[:45]
                        if len(words) > 70:
                            # use the first 50-70 words as a description
                            for word in words[45:]:
                                summarywords.append(word)
                                if word.endswith('.'):
                                    # if we encounter a fullstop that will be the
                                    # last word appended to the description
                                    break
                            summary = ' '.join(summarywords)
                            if not summary.endswith('.'):
                                summary = summary + ' ...'
                        obj.setDescription(summary)

                if hasattr(entry, 'links'):
                    enclosures = [x for x in entry.links if x.rel == 'enclosure']
                    real_enclosures = [x for x in enclosures if
                                       not self.isHTMLEnclosure(x)]

                    for link in real_enclosures:
                        enclosureSig = md5(link.href)
                        enclosureId = enclosureSig.hexdigest()
                        if enclosureId in obj.objectIds():
                            # Two enclosures with the same href in this
                            # entry...
                            continue
                        enclosure = obj.addEnclosure(enclosureId)
                        enclosure.update(title=enclosureId)
                        if enclosure.Title() != enclosure.getId():
                            self.tryRenamingEnclosure(enclosure, obj)
                            # At this moment in time, the
                        # rename-after-creation magic might have changed
                        # the ID of the file. So we recatalog the object.
                        obj.reindexObject()
        IStatusMessage(self.request).addStatusMessage('Importacao concluida com sucesso', type='info')

    def tryRenamingEnclosure(self, enclosure, feeditem):
        newId = enclosure.Title()
        for x in range(1, 10):
            if newId not in feeditem.objectIds():
                try:
                    feeditem.manage_renameObject(enclosure.getId(),
                        newId)
                    break
                except:
                    pass
            newId = '%i_%s' % (x, enclosure.Title())


    def isHTMLEnclosure(self, enclosure):
        if hasattr(enclosure, 'type'):
            return enclosure.type == u'text/html'
        return False
