from wechat.base import md5, hmac_sha256

"""
采用 微信支付接口签名校验工具 验证：
https://pay.weixin.qq.com/wiki/doc/api/micropay.php?chapter=20_1
"""


def main():
    key = '192006250b4c09247ec02edce69f6a2d'
    a_string = ('appid=wxd930ea5d5a258f4f'
                '&body=test'
                '&device_info=1000'
                '&mch_id=10000100'
                '&nonce_str=ibuaiVcKdpRxkhJA')
    a_string += "&key=%s" % key

    a = md5(a_string)
    print(a)
    a_expected = '9A0A8659F005D6984697E2CA0A9CF3B7'
    print(a_expected)
    print(a == a_expected)

    b = hmac_sha256(key, a_string)
    print(b)
    b_expected = '6A9AE1657590FD6257D693A078E1C3E4BB6BA4DC30B23E0EE2496E54170DACD6'
    print(b_expected)
    print(b == b_expected)


if __name__ == "__main__":
    main()
