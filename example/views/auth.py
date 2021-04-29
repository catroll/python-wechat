from datetime import datetime, timedelta

from flask import Blueprint, current_app, redirect, request, url_for

app = Blueprint('auth', __name__)


@app.route('/login')
def login():
    openid = request.cookies.get('openid')
    next = request.args.get('next') or request.referrer or '/',
    if openid:
        return redirect(next)

    callback = url_for('authorized', next=next, _external=True)
    url = current_app.wechat.auth.authorize(callback, 'snsapi_base')
    return redirect(url)


@app.route('/authorized')
def authorized():
    code = request.args.get('code')
    if not code:
        return 'ERR_INVALID_CODE', 400
    next = request.args.get('next', '/')
    data = current_app.wechat.auth.access_token(code)
    openid = data.openid
    resp = redirect(next)
    expires = datetime.now() + timedelta(days=1)
    resp.set_cookie('openid', openid, expires=expires, secure=True, httponly=True, samesite='Lax')
    return resp
