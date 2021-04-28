from django.http import (HttpResponse, HttpResponseForbidden,
                         HttpResponseNotAllowed)
from weixin.msg import WeixinMsg

msg = WeixinMsg('e10adc3949ba59abbe56e057f20f883e', None, 0)


def view_func(request):
    signature = request.GET.get('signature')
    timestamp = request.GET.get('timestamp')
    nonce = request.GET.get('nonce')

    if not msg.validate(signature, timestamp, nonce):
        return HttpResponseForbidden('signature failed')

    if request.method == 'GET':
        echostr = request.GET.get('echostr', '')
        return HttpResponse(echostr)

    if request.method != 'POST':
        return HttpResponseNotAllowed(['GET', 'POST'])

    try:
        ret = msg.parse(request.body)
    except ValueError:
        return HttpResponseForbidden('invalid')

    func = None
    _registry = msg._registry.get(ret['type'], dict())
    if ret['type'] == 'text':
        if ret['content'] in _registry:
            func = _registry[ret['content']]
    elif ret['type'] == 'event':
        if ret['event'].lower() in _registry:
            func = _registry[ret['event'].lower()]

    if func is None and '*' in _registry:
        func = _registry['*']
    if func is None and '*' in msg._registry:
        func = msg._registry.get('*', dict()).get('*')

    text = ''
    if func is None:
        text = 'failed'

    if callable(func):
        text = func(**ret)

    content = ''
    if isinstance(text, basestring):
        if text:
            content = msg.reply(
                username=ret['sender'],
                sender=ret['receiver'],
                content=text,
            )
    elif isinstance(text, dict):
        text.setdefault('username', ret['sender'])
        text.setdefault('sender', ret['receiver'])
        content = msg.reply(**text)

    return HttpResponse(content, content_type='text/xml; charset=utf-8')
