# Copyright (c) 2009-2015 testtools developers. See LICENSE for details.

"""ContentType - a MIME Content Type."""


class ContentType(object):
    """A content type from http://www.iana.org/assignments/media-types/

    :ivar type: The primary type, e.g. "text" or "application"
    :ivar subtype: The subtype, e.g. "plain" or "octet-stream"
    :ivar parameters: A dict of additional parameters specific to the
        content type.
    """

    def __init__(self, primary_type, sub_type, parameters=None,
                 text_override=False):
        """Create a ContentType."""
        if None in (primary_type, sub_type):
            raise ValueError("None not permitted in %r, %r" % (
                primary_type, sub_type))
        self.type = primary_type
        self.subtype = sub_type
        self.parameters = parameters or {}
        self._text_override = text_override

    def __eq__(self, other):
        if type(other) != ContentType:
            return False
        return self.__dict__ == other.__dict__

    def __repr__(self):
        if self.parameters:
            params = '; '
            params += '; '.join(
                sorted('%s="%s"' % (k, v) for k, v in self.parameters.items()))
        else:
            params = ''
        return "%s/%s%s" % (self.type, self.subtype, params)

    def is_text(self):
        """True if this content type can be converted to text."""
        return self.type == 'text' or self._text_override


JSON = ContentType(
    'application', 'json', {'charset': 'utf8'}, text_override=True)

UTF8_TEXT = ContentType('text', 'plain', {'charset': 'utf8'})
