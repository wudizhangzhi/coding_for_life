/*
  sample:
    modify response data of http://httpbin.org/user-agent
  test:
    curl 'http://httpbin.org/user-agent' --proxy http://127.0.0.1:8001
  expected response:
    { "user-agent": "curl/7.43.0" } -- AnyProxy Hacked! --
*/

module.exports = {
  *beforeSendResponse(requestDetail, responseDetail) {
    if (requestDetail.url.indexOf('http://api.008shenqi.com/api/xtools/x008/status') === 0) {
      data = {
    	"userName": "1000000",
    	"overTime": "false",
    	"id": "1000000",
    	"time": Date.now()
      }
      const newResponse = responseDetail.response;
      newResponse.body = JSON.stringify(data);
      newResponse.statusCode = 200;
      return {
        response: newResponse
      };
    }else if(requestDetail.url.indexOf('http://api.008shenqi.com/api/xtools/x008/sysconf') === 0){
        data = {
            "sellUrl": "http://api2.apk00888888.com/lishu008AppManager/AuToAddDays.action",
            "status": "1",
            "expiryTime": Date.now(),
            "vip": "true",
            "promoteUrl": "/DownLoadFileAction.action?id=1000000",
            "msg": "未过期",
            "id": "1000000"
        }
        const newResponse = responseDetail.response;
        newResponse.body = JSON.stringify(data);
        newResponse.statusCode = 200;
        return {
           response: newResponse
        };
    }else if(requestDetail.url.indexOf('http://api.008shenqi.com/api/xtools/x008/genid') === 0){
        data = {}
        const newResponse = responseDetail.response;
        newResponse.body = JSON.stringify(data);
        newResponse.statusCode = 200;
        return {
            response: newResponse
        };
    }
  },
};