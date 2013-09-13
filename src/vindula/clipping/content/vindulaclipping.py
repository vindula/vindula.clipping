# -*- coding: utf-8 -*-

from zope.interface import implements

from Products.Archetypes import atapi
from Products.ATContentTypes.content import schemata

from plone.app.folder.folder import ATFolder, ATFolderSchema

from vindula.clipping.interfaces import IVindulaClipping
from vindula.clipping.config import PROJECTNAME
from vindula.clipping import MessageFactory as _

#TODO: criar validator para as URLs inseridas

VindulaClippingSchema = ATFolderSchema.copy() + atapi.Schema((

    atapi.LinesField(
        name='feeds',
        widget=atapi.LinesWidget(
            label=_(u"Feeds"),
            description=_(u"Informe os enderecos dos Feeds, um por linha.")
        )
    ),
))

schemata.finalizeATCTSchema(VindulaClippingSchema, folderish=True, moveDiscussion=False)


class VindulaClipping(ATFolder):
    """
    """

    implements(IVindulaClipping)

    meta_type = "VindulaClipping"
    schema = VindulaClippingSchema

    _at_rename_after_creation = True

atapi.registerType(VindulaClipping, PROJECTNAME)
