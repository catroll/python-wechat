import logging
import time

from .base import WechatBase, WechatError, sha1, xml2dict

__all__ = 'WechatMsgError', 'WechatMsg'
LOG = logging.getLogger(__name__)


class WechatMsgError(WechatError):
    pass


class WechatMsg(WechatBase):
    def __init__(self, token, sender=None, expires_in=0, debug=False):
        self.token = token
        self.sender = sender
        self.expires_in = expires_in
        self.debug = debug
        self._registry = dict()

    def validate(self, signature, timestamp, nonce):
        if not self.token:
            raise WechatMsgError('wechat token is missing')

        if self.expires_in:
            try:
                timestamp = int(timestamp)
            except (TypeError, ValueError):
                return False
            delta = time.time() - timestamp
            if delta < 0 or delta > self.expires_in:
                return False

        values = [self.token, str(timestamp), str(nonce)]
        return signature == sha1(''.join(sorted(values)))

    def parse(self, content):
        """
        解析微信公众平台推送过来的消息
        参考文档: https://developers.weixin.qq.com/doc/offiaccount/Message_Management/Receiving_standard_messages.html
        """
        raw = xml2dict(content)
        formatted = self._data_format(raw)
        msg_parser = getattr(self, '_parse_{0}'.format(formatted['type']), None)
        parsed = msg_parser(raw) if callable(msg_parser) else self._parse_invalid_type(raw)
        formatted.update(parsed)
        return formatted

    # =====================================================

    def _data_format(self, kwargs):
        timestamp = int(kwargs['CreateTime'])
        return {
            'id': kwargs.get('MsgId'),
            'timestamp': timestamp,
            'receiver': kwargs['ToUserName'],
            'sender': kwargs['FromUserName'],
            'type': kwargs['MsgType'],
            'time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp)),
        }

    def _parse_text(self, raw):
        return {'content': raw['Content']}

    def _parse_image(self, raw):
        return {'picurl': raw['PicUrl']}

    def _parse_location(self, raw):
        return {
            'location_x': raw['Location_X'],
            'location_y': raw['Location_Y'],
            'scale': int(raw.get('Scale', 0)),
            'label': raw['Label'],
        }

    def _parse_link(self, raw):
        return {
            'title': raw['Title'],
            'description': raw['Description'],
            'url': raw['url'],
        }

    def _parse_voice(self, raw):
        return {
            'media_id': raw['MediaId'],
            'format': raw['Format'],
            'recognition': raw['Recognition'],
        }

    def _parse_video(self, raw):
        return {
            'media_id': raw['MediaId'],
            'thumb_media_id': raw['ThumbMediaId'],
        }

    def _parse_shortvideo(self, raw):
        return {
            'media_id': raw['MediaId'],
            'thumb_media_id': raw['ThumbMediaId'],
        }

    def _parse_event(self, raw):
        return {
            'event': raw.get('Event'),
            'event_key': raw.get('EventKey'),
            'ticket': raw.get('Ticket'),
            'latitude': raw.get('Latitude'),
            'longitude': raw.get('Longitude'),
            'precision': raw.get('Precision'),
            'status': raw.get('status')
        }

    def _parse_invalid_type(self, raw):
        LOG.warning('Invalid Type: %s', raw['MsgType'])
        return {}

    # =====================================================

    def reply(self, username=None, type='text', sender=None, **kwargs):
        if not username:
            raise RuntimeError('username is missing')
        sender = sender or self.sender
        if not sender:
            raise RuntimeError('WXN_SENDER or sender argument is missing')

        if type == 'text':
            content = kwargs.get('content', '')
            return text_reply(username, sender, content)

        if type == 'music':
            values = {k: kwargs[k] for k in ('title', 'description', 'music_url', 'hq_music_url')}
            return music_reply(username, sender, **values)

        if type == 'news':
            items = kwargs['articles']
            return news_reply(username, sender, *items)

        if type == 'customer_service':
            service_account = kwargs['service_account']
            return transfer_customer_service_reply(username, sender, service_account)

        if type == 'image':
            media_id = kwargs.get('media_id')
            return image_reply(username, sender, media_id)

        if type == 'voice':
            media_id = kwargs.get('media_id')
            return voice_reply(username, sender, media_id)

        if type == 'video':
            values = {k: kwargs[k] for k in ('media_id', 'title', 'description')}
            return video_reply(username, sender, **values)

    # =====================================================

    def register(self, msg_type, key=None, func=None):
        if func:
            self._registry.setdefault(msg_type, dict())[key or '*'] = func
            return func
        return self.__call__(msg_type, key)

    def __call__(self, type, key):
        def wrapper(func):
            self.register(type, key, func)
            return func
        return wrapper

    def command(self, key='*'):
        return self.register('text', key)

    def __getattr__(self, key):
        key = key.lower()
        if key == 'all':
            return self.register('*')
        if key in ['image', 'video', 'voice', 'shortvideo', 'location', 'link', 'event', 'text']:
            return self.register(key)
        if key in ['subscribe', 'unsubscribe', 'location', 'click', 'view', 'scan',
                   'scancode_push', 'scancode_waitmsg', 'pic_sysphoto',
                   'pic_photo_or_album', 'pic_weixin', 'location_select',
                   'qualification_verify_success', 'qualification_verify_fail', 'naming_verify_success',
                   'naming_verify_fail', 'annual_renew', 'verify_expired',
                   'card_pass_check', 'user_get_card', 'user_del_card', 'user_consume_card',
                   'user_pay_from_pay_cell', 'user_view_card', 'user_enter_session_from_card',
                   'card_sku_remind']:
            return self.register('event', key)
        raise AttributeError('invalid attribute "%s"' % key)

    def handle(self, content):
        try:
            data = self.parse(content)
        except ValueError:
            raise WechatMsgError('parse error', content)

        func = None
        # LOG.info(self._registry.keys())
        type_registry = self._registry.get(data['type'], dict())
        # LOG.info(type_registry)

        if data['type'] == 'text':
            if data['content'] in type_registry:
                func = type_registry[data['content']]
        elif data['type'] == 'event':
            if data['event'].lower() in type_registry:
                func = type_registry[data['event'].lower()]

        if func is None and '*' in type_registry:
            func = type_registry['*']

        if func is None and '*' in self._registry:
            func = self._registry.get('*', dict()).get('*')

        if func is None:
            raise WechatMsgError('no func registered!')

        if not callable(func):
            raise WechatMsgError('func is invalid!')

        return data, func(**data)


def text_reply(username, sender, content):
    shared = _shared_reply(username, sender, 'text')
    template = '<xml>%s<Content><![CDATA[%s]]></Content></xml>'
    return template % (shared, content)


def music_reply(username, sender, **kwargs):
    kwargs['shared'] = _shared_reply(username, sender, 'music')
    return ('<xml>'
            '%(shared)s'
            '<Music>'
            '<Title><![CDATA[%(title)s]]></Title>'
            '<Description><![CDATA[%(description)s]]></Description>'
            '<MusicUrl><![CDATA[%(music_url)s]]></MusicUrl>'
            '<HQMusicUrl><![CDATA[%(hq_music_url)s]]></HQMusicUrl>'
            '</Music>'
            '</xml>') % kwargs


def news_reply(username, sender, *items):
    item_template = ('<item>'
                     '<Title><![CDATA[%(title)s]]></Title>'
                     '<Description><![CDATA[%(description)s]]></Description>'
                     '<PicUrl><![CDATA[%(picurl)s]]></PicUrl>'
                     '<Url><![CDATA[%(url)s]]></Url>'
                     '</item>')
    articles = [item_template % o for o in items]
    kwargs = {
        'shared': _shared_reply(username, sender, 'news'),
        'count': len(items),
        'articles': ''.join(articles)
    }
    return ('<xml>'
            '%(shared)s'
            '<ArticleCount>%(count)d</ArticleCount>'
            '<Articles>%(articles)s</Articles>'
            '</xml>') % kwargs


def transfer_customer_service_reply(username, sender, service_account):
    template = '<xml>%(shared)s%(transfer_info)s</xml>'
    transfer_info = ('<TransInfo>'
                     '<KfAccount>![CDATA[%s]]</KfAccount>'
                     '</TransInfo>') % service_account if service_account else ''
    return template % {
        'shared': _shared_reply(username, sender, type='transfer_customer_service'),
        'transfer_info': transfer_info,
    }


def image_reply(username, sender, media_id):
    shared = _shared_reply(username, sender, 'image')
    template = '<xml>%s<Image><MediaId><![CDATA[%s]]></MediaId></Image></xml>'
    return template % (shared, media_id)


def voice_reply(username, sender, media_id):
    shared = _shared_reply(username, sender, 'voice')
    template = '<xml>%s<Voice><MediaId><![CDATA[%s]]></MediaId></Voice></xml>'
    return template % (shared, media_id)


def video_reply(username, sender, **kwargs):
    kwargs['shared'] = _shared_reply(username, sender, 'video')
    return ('<xml>'
            '%(shared)s'
            '<Video>'
            '<MediaId><![CDATA[%(media_id)s]]></MediaId>'
            '<Title><![CDATA[%(title)s]]></Title>'
            '<Description><![CDATA[%(description)s]]></Description>'
            '</Video>'
            '</xml>') % kwargs


def _shared_reply(username, sender, type):
    template = ('<ToUserName><![CDATA[%(username)s]]></ToUserName>'
                '<FromUserName><![CDATA[%(sender)s]]></FromUserName>'
                '<CreateTime>%(timestamp)d</CreateTime>'
                '<MsgType><![CDATA[%(type)s]]></MsgType>')
    kwargs = {
        'username': username,
        'sender': sender,
        'type': type,
        'timestamp': int(time.time()),
    }
    return template % kwargs
