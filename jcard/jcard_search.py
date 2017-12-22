# coding =utf8


import requests
from lxml import etree
import json
from user_agent import generate_user_agent


def test():
    url = 'http://www.jcard.cn/Bill/TradeSearch.aspx'
    headers = {
        'User-Agent': generate_user_agent(os=('mac', 'linux')),
        'Host': 'www.jcard.cn',
        'Origin': 'http://www.jcard.cn',
    }
    data = {
        '__VIEWSTATE': '',
        '__VIEWSTATEGENERATOR': '',
        'ctl00$MainContent$txtCardNo': '1704280393550020',
        'ctl00$MainContent$txtUCardPassword': '5171101380166090',
        'ctl00$MainContent$txtCardNoExtCode:': '',
        'ctl00$Header$txtSearchKey:': '',
        'ctl00$MainContent$btnSearch:': '',
    }
    sess = requests.Session()
    sess.headers = headers
    r = sess.get(url, timeout=10)

    root = etree.HTML(r.text)
    inputs_hidden = root.xpath('//input[@type="hidden"]')
    for hidden in inputs_hidden:
        # print(hidden.attrib.get('name'), hidden.attrib.get('value'))
        data[hidden.attrib.get('name')] = hidden.attrib.get('value')

    print(json.dumps(data, indent=4))
    r = sess.post(url, data=data, timeout=10)
    # print(r.text)
    root = etree.HTML(r.text)
    success = root.xpath('//div[@id="ctl00_MainContent_panUCardTrade"]')
    if not success:
        print(r.text)


if __name__ == '__main__':
    test()
