# -*- coding: utf-8 -*-


__all__ = 'WechatError', 'dict2xml', 'xml2dict'

from lxml import etree


def dict2xml(raw):
    s = ''
    for k, v in raw.items():
        s += '<{0}>{1}</{0}>'.format(k, v)
    s = '<xml>{0}</xml>'.format(s)
    return s.encode('utf-8')


def xml2dict(content):
    root = etree.fromstring(content.encode('utf-8'),
                            parser=etree.XMLParser(resolve_entities=False))
    return {chind.tag: child.text for child in root}


class WechatError(Exception):
    def __init__(self, msg):
        super(WechatError, self).__init__(msg)
