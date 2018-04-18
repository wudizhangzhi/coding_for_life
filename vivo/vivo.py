import requests
from user_agent import generate_user_agent

# 登录
url = 'https://usrsys.inner.bbk.com/v2/login'

# data = {
#     "account": "18505231132",
#     "pwd": "13961000804",
#     "verCode": 2,
#     "from": "com.vivo.game_game",
#     "imei": "862561035110764",
#     "cs": "0",
#     "locale": "zh_CN",
#     "model": "ONEPLUS A3010",
# }
#
# r = requests.post(url, data=data, verify=False)
# print(r.text)


"""
{
	"stat": "200",
	"msg": "处理成功",
	"id": 266837041,
	"openid": "70b424a0e7c21fa6",
	"sk": "4270796f459e93c11fa1ef3e36117adb",
	"visitor": "0",
	"isRemindUpgrade": "0",
	"isForceUpgrade": "0",
	"authtoken": "NmFkZmJlZTExN2MxYmMxYjE1ZWQuMjY2ODM3MDQxLjE1MjQwNjUzNjQxODk",
	"pcstoken": "",
	"cs": "-1",
	"tokenUpTime": "",
	"hasPwdPro": "0",
	"upemail": "0",
	"uppwd": "true",
	"uuid": "0f0a40e1-410a-4fb1-b5c9-91b63f48235c",
	"name": "",
	"email": "",
	"phonenum": "18505231132",
	"needAuth": false
}

appVersion: $.cookie("app_version")||$.cookie("vvc_app_version"),
elapsedtime: $.cookie("elapsedtime")||$.cookie("vvc_elapsedtime"),
imei: $.cookie("imei")||$.cookie("vvc_imei"),
logged: ($.cookie("status")||$.cookie("vvc_status")) === '1',
model: $.cookie("model")||$.cookie("vvc_model"),
openid: $.cookie("n")||$.cookie("vvc_openid"),
sign: $.cookie('vvs_vivos_sign'),
token: $.cookie("r")||$.cookie("vvc_r"),
username: $.cookie("p")||$.cookie("vvc_p"),
uuid: $.cookie("q")||$.cookie("vvc_q"),
cs: $.cookie("cs")||$.cookie("vvc_cs"),
av: $.cookie("av")||$.cookie("vvc_av"),
version: '1.0.0'



appVersion	161
elapsedtime	258854199  # elapsedRealTime()返回的是系统从启动到现在的时间
imei	862561035110764
logged	true
model	ONEPLUS+A3010
openid	70b424a0e7c21fa6
token	NmFkZmJlZTExN2MxYmMxYjE1ZWQuMjY2ODM3MDQxLjE1MjQwNjUzNjQxODk
username	185****1132
uuid	185****1132
cs	0
av	25
version	1.0.0

sign	2|2505605079
"""


def get_balance():
    url = 'https://pay.vivo.com.cn/vcoin/game/blance'
    data = {
        "appVersion": "40",
        "elapsedtime": "3544069",
        "imei": "865407010000009",
        "logged": "",
        "model": "vivo+Xplay3S",
        "openid": "880461d865bd98c5",
        "sign": "2|2505605079",
        "token": "NzU5M2U0OTE1NGI4ZmZhNTE3M2UuNTI1OTI3NS4xNDQ3OTAwODg2NDEy",
        "username": "test",
        "uuid": "test",
        "cs": "0",
        "av": "19",
        "version": "1.0.0",
    }

    headers = {}

    r = requests.post(url, data=data, headers=headers, verify=False)
    print(r.text)


if __name__ == '__main__':
    get_balance()
