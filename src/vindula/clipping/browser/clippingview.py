# -*- coding: utf-8 -*-

from five import grok

from Products.CMFCore.utils import getToolByName

from vindula.clipping.interfaces import IVindulaClipping

from vindula.content.browser.views import quote_chars

grok.templatedir("templates")


class ClippingView(grok.View):
    grok.name('view')
    grok.require("zope2.View")
    grok.context(IVindulaClipping)

    def QueryFilter(self):
        """ metodo para retornar os objetos a serem listados
        """
        catalog_tool = getToolByName(self, 'portal_catalog')
        form = self.request.form
        submitted = form.get('submitted', False)
        form_cookies = {}

        if not submitted and self.request.cookies.get('find-news', None):
            form_cookies = self.getCookies(self.request.cookies.get('find-news', None))

        if submitted or form_cookies:
            D = {}
            invert = form.get('invert', form_cookies.get('invert', False))
            sort_on = form.get('sorted',form_cookies.get('sorted', ''))

            if sort_on == 'effective':
                invert = not invert

            if invert:
                D['sort_order'] = 'reverse'
            else:
                D['sort_order'] = ''

            text = form.get('keyword',form_cookies.get('keyword', ''))
            if text:
                text = text.strip()
                if '*' not in text:
                    text += '*'
                D['SearchableText'] = quote_chars(text)

            D['sort_on'] = sort_on
            D['path'] = {'query':'/'.join(self.context.getPhysicalPath())}
            result = catalog_tool(**D)
        else:
            result = catalog_tool({'portal_type': ('ATNewsItem','VindulaNews',), 'sort_on': 'effective', 'sort_order':'reverse'})
        return result

    def getCookies(self, cookies=None):
        form_cookies = {}
        if not cookies:
            cookies = self.request.cookies.get('find-news', None)

        if cookies:
            all_cookies = self.request.cookies.get('find-news', None).split('|')
            for cookie in all_cookies:
                if cookie:
                    cookie = cookie.split('=')
                    form_cookies[cookie[0]] = cookie[1]

        return form_cookies
