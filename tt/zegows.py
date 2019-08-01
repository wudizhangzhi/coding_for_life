import websocket
import json
import requests
from base64 import b64decode
from user_agent import generate_user_agent

try:
    import thread
except ImportError:
    import _thread as thread
import time


class ZegoWSBase(object):
    host = 'wsliveroom1082937486-api.zego.im:8282'
    app_id = None
    id_name = None
    session_id = None
    user_id = None
    room_id = None
    token_base64 = None

    cmd_func_map = {
        'login': '_on_msg_login',
        'user_list': '_on_msg_user_list',
        'push_userlist_update': '_on_msg_push_userlist_update',
        'hb': '_on_msg_hb',
    }

    def __init__(self, app_id, id_name, room_id):
        self.room_id = room_id
        self.token_base64 = self.get_token(app_id, id_name)
        token = b64decode(self.token_base64).decode('utf8')
        print('获取token: %s' % token)

    def get_token(self, app_id=None, id_name=None):
        """
        获取token
        :param app_id:
        :param id_name:
        :return:
        {"ver":1,"hash":"4a52658fef2d227db7850b6c6ba3afda","nonce":"68b2cf8fbce2fd844e118b8d00eb989a","expired":1567219021}
        """
        if app_id:
            self.app_id = app_id
        if id_name:
            self.id_name = id_name
        headers = {
            'User-Agent': generate_user_agent()
        }
        params = {
            'app_id': self.app_id,
            'id_name': self.id_name,
        }
        url = 'https://%s/token' % self.host
        ret = requests.get(url, headers=headers, params=params)
        return ret.text

    def _on_message(self, ws, message):
        print('收到: %s' % message)
        print('-' * 30)
        try:
            message = json.loads(message)
        except:
            pass

        header = message['header']
        cmd = header['cmd']
        if cmd in self.cmd_func_map:
            func = getattr(self, self.cmd_func_map[cmd])
            func(ws, message)
        else:
            print('没有地方处理: %s' % message)

    def _on_open(self, ws):
        # 发送登录的指令
        self.begin_login(ws)

        # 启动heartbeat
        def heart_beat_forever(*args, **kwargs):
            while True:
                time.sleep(30)
                self.heart_beat(ws)

            ws.close()
            print("thread terminating...")

        thread.start_new_thread(heart_beat_forever, ())

    def _on_error(self, ws, error):
        pass

    def _on_close(self, ws):
        print('关闭')

    def _on_msg_login(self, ws, message):
        """
        {"body": {"err_code": 0, "err_message": "success", "user_id": "12256144455877684210",
          "session_id": "376495930586693632", "hearbeat_interval": 30000, "server_user_seq": 0, "stream_seq": 0,
          "stream_info": [], "config_info": {"log_level": 1, "log_url": "wss://wslogger-demo.zego.im:8282/log"},
          "online_count": 1, "ret_timestamp": "1564566512817", "bigim_time_window": 5000, "dati_time_window": 5000,
          "anchor_info": {"anchor_id": "0", "anchor_id_name": "", "anchor_nick_name": ""}, "cluster_name": ""},
         "header": {"protocol": "rsp", "cmd": "login", "appid": 1082937486, "seq": 1, "user_id": "", "session_id": "",
                    "room_id": "123"}}
        :param ws:
        :param message:
        :return:
        """
        body = message['body']
        self.session_id = body['session_id']
        self.user_id = body['user_id']

        # 获取用户列表
        msg_user_list = {"header": {"Protocol": "req", "cmd": "user_list", "appid": self.app_id, "seq": 3,
                                    "user_id": self.user_id, "session_id": self.session_id, "room_id": self.room_id},
                         "body": {"user_index": 0, "sort_type": 0}}
        print('发送获取用户列表: %s' % msg_user_list)
        ws.send(json.dumps(msg_user_list))

    def _on_msg_user_list(self, ws, message):
        """
        {"body":{"err_code":0,"err_message":"","server_user_index":1,"ret_user_index":1,"server_user_seq":1,"user_baseinfos":
        [{"id_name":"1564645676874","nick_name":"u-1564645676874","role":2}]},"header":{"protocol":"rsp","cmd":"user_list","appid":1082937486,
        "seq":3,"user_id":"7548156113329788324","session_id":"376827638804643840","room_id":"123"}}
        :param ws:
        :param message:
        :return:
        """
        body = message['body']
        user_baseinfos = body['user_baseinfos']
        print('在线列表: ')
        for user_info in user_baseinfos:
            print(user_info)

    def _on_msg_push_userlist_update(self, ws, message):
        """
        {"body":{"user_list_seq":5,"room_id":"123","user_actions":[{"Action":1,"IdName":"1564649324958","NickName":"u-1564649324958","Role":2,"LoginTime":"1564649249363"}]},
        "header":{"protocol":"push","cmd":"push_userlist_update","appid":1082937486,"user_id":"2135327535690938714",
        "session_id":"376842657575469056","room_id":"123","push_seq":1,"from_user_id":"","qos_flag":0}}
        """
        body = message['body']
        user_actions = body['body.user_actions']
        print('用户更新')
        for user_action in user_actions:
            print(user_action)

    def _on_msg_hb(self, ws, message):
        """
        {"header": {"Protocol": "req", "cmd": "hb", "appid": 1082937486, "seq": 2, "user_id": "12256144455877684210",
            "session_id": "376495930586693632", "room_id": "123"}, "body": {"reserve": 0}}

        {"body": {"err_code": 0, "err_message": "", "hearbeat_interval": 30000, "stream_seq": 0, "server_user_seq": 1,
                  "online_count": 1, "bigim_time_window": 5000, "dati_time_window": 5000, "trans_seqs": [],
                  "hearbeat_timeout": 100000, "user_trans_seqs": []},
         "header": {"protocol": "rsp", "cmd": "hb", "appid": 1082937486, "seq": 2, "user_id": "12256144455877684210",
                    "session_id": "376495930586693632", "room_id": "123"}}
        :param ws:
        :param message:
        :return:
        """
        body = message['body']
        err_code = body['err_code']
        if err_code != 0:
            print('心跳失败')

    def begin_login(self, ws):
        # 登录
        msg_login = {"header": {"Protocol": "req", "cmd": "login", "appid": self.app_id, "seq": 1, "session_id": "",
                                "room_id": self.room_id},
                     "body": {"id_name": self.id_name, "nick_name": "u-%s" % self.id_name, "role": 2,
                              "token": self.token_base64,
                              "version": "1.2.2", "room_name": self.room_id, "user_state_flag": 1,
                              "room_create_flag": 1, "client_type": 3, "third_token": ""}}
        # msg_login = {"header": {"Protocol": "req", "cmd": "login", "appid": 1082937486, "seq": 1, "session_id": "",
        #                         "room_id": "123"},
        #              "body": {"id_name": "1564627114113", "nick_name": "u-1564627114113", "role": 2,
        #                       "token": "eyJ2ZXIiOjEsImhhc2giOiI0YTUyNjU4ZmVmMmQyMjdkYjc4NTBiNmM2YmEzYWZkYSIsIm5vbmNlIjoiNjhiMmNmOGZiY2UyZmQ4NDRlMTE4YjhkMDBlYjk4OWEiLCJleHBpcmVkIjoxNTY3MjE5MDIxfQ==",
        #                       "version": "1.2.2", "room_name": "123", "user_state_flag": 1, "room_create_flag": 1,
        #                       "client_type": 3,
        #                       "third_token": ""}}
        print('发送登录: %s' % msg_login)
        ws.send(json.dumps(msg_login))

    def heart_beat(self, ws):
        print('心跳')
        msg_beat = {"header": {"Protocol": "req", "cmd": "hb", "appid": self.app_id, "seq": 2, "user_id": self.user_id,
                               "session_id": self.session_id, "room_id": self.room_id}, "body": {"reserve": 0}}
        ws.send(json.dumps(msg_beat))

    def run(self):
        websocket.enableTrace(True)
        ws = websocket.WebSocketApp("wss://%s/ws" % self.host,
                                    on_message=self._on_message,
                                    on_error=self._on_error,
                                    on_close=self._on_close)
        ws.on_open = self._on_open
        ws.run_forever()


if __name__ == "__main__":
    app_id = 1082937486
    id_name = '1564565801640'
    room_id = '123'
    zego = ZegoWSBase(app_id, id_name, room_id)
    zego.run()
