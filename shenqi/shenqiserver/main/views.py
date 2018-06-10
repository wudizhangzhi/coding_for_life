# coding=utf8
from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.
import time
import json
import requests
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def status(request):
    data = {
    	"userName": "1000000",
    	"overTime": "false",
    	"id": "1000000",
    	"time": int(time.time()) * 1000
    }
    return HttpResponse(json.dumps(data))

@csrf_exempt
def sysconf(request):
    data = {
    	"sellUrl": "http://api2.apk00888888.com/lishu008AppManager/AuToAddDays.action",
    	"status": "1",
    	"expiryTime": int(time.time()) * 1000,
    	"vip": "true",
    	"promoteUrl": "/DownLoadFileAction.action?id=1000000",
    	"msg": "未过期",
    	"id": "1000000"
    }
    return HttpResponse(json.dumps(data))

@csrf_exempt
def genid(request):
    data = {

    }
    print(request)
    return HttpResponse(json.dumps(data))
