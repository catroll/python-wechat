import hashlib
import hmac
import random
import string
import urllib.parse
import xml.etree.ElementTree as etree
from xml.sax.saxutils import escape as xml_escape

__all__ = 'random_string', 'md5', 'sha1', 'hmac_sha256', 'dict2xml', 'xml2dict', 'urlencode', 'WechatError'


def random_string(length=8):
    char = string.ascii_letters + string.digits
    return ''.join(random.choice(char) for _ in range(length))


def md5(content):
    return hashlib.md5(content.encode('utf-8')).hexdigest().upper()


def sha1(content):
    return hashlib.sha1(content.encode('utf-8')).hexdigest()


def hmac_sha256(key, content):
    return hmac.new(key.encode('utf-8'),
                    msg=content.encode('utf-8'),
                    digestmod=hashlib.sha256).hexdigest().upper()


def dict2xml(dct):
    return '<xml>%s</xml>' % (
        # ''.join(['<{0}><![CDATA[{1}]]></{0}>'.format(k, v)
        ''.join(['<{0}>{1}</{0}>'.format(k, xml_escape(str(v)))
                 for k, v in dct.items()]))


def xml2dict(xml_str):
    if isinstance(xml_str, str):
        xml_str = xml_str.encode('utf-8')
    # lxml: etree.XMLParser(resolve_entities=False)
    root = etree.fromstring(xml_str, parser=etree.XMLParser())
    return {child.tag: child.text for child in root}


def urlencode(url):
    return urllib.parse.quote_plus(url)


class WechatError(Exception):
    def __init__(self, msg):
        super(WechatError, self).__init__(msg)
