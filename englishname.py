import requests
from user_agent import generate_user_agent


class Game(object):
    def __init__(self):
        self.session = requests.Session()
        headers = {
            "User-Agent": generate_user_agent(os=['linux', 'mac'])
        }
        self.session.headers = headers

    def login(self, name, department=None):
        url = 'http://172.16.250.216:6080/appadmin/private/user/login.do?token=&platform=3&version=1.3.9'
        data = {
            'name': name,
            'serviceLine': 4,
            'token': '',
            'platform': '3',
            'version': '1.3.9',
        }
        ret = self.session.post(url, data=data)
        print(ret.text)
        self.gameSign = ret.json()['data']['gameSign']
        self.loginId = ret.json()['data']['id']

    def update_score(self, score):
        url = 'http://172.16.250.216:6080/appadmin/private/user/updateScore.do?token=&platform=3&version=1.3.9'
        data = {
            'loginId': self.loginId,
            'gameSign': self.gameSign,
            'nowScore': score,
            'token': '',
            'platform': 3,
            'version': '1.3.9',
        }
        ret = self.session.post(url, data=data)
        print(ret.text)

    def run(self):
        self.login('moon')
        self.update_score(20)

"""
postScore: function() {
                    for (var t = this, e = "", n = 0; n < 5; n++)
                        e += Math.floor(10 * Math.random());
                    var i = {
                        loginId: t.loginData.id,
                        gameSign: t.gameSign,
                        nowScore: t.principalFraction,
                        sign: e
                    }
                      , r = a.enc.Utf8.parse("2a40b3df13b551a2")
                      , o = a.DES.encrypt((0,
                    s.default)(i), r, {
                        mode: a.mode.ECB,
                        padding: a.pad.Pkcs7
                    });
                    this.$http.post("//172.16.250.216:6080/appadmin/private/user/updateScore.do", {
                        request: o.toString()
                    }).then(function(t) {}).catch(function(e) {
                        t.setToast(e.data.msg)
                    })
                },
"""
if __name__ == '__main__':
    g = Game()
    g.run()
