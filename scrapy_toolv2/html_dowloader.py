from requests.api import request
from urllib.parse import urljoin
import time,requests,json,os
from bs4 import BeautifulSoup

# Settings for htmldownloader
# 下载html过程中最大尝试次数
DEFAULT_MAX_ITER_TIME = 10000

# timeout
DEFAULT_MAX_CONNECT_TIME = 3
DEFAULT_MAX_READ_TIME = 30

# settings for proxypool
# 默认七夜代理获取地址
QIYE_URL = 'http://localhost:8000'

# 默认西刺代理地址
XICI_URL = 'http://www.xicidaili.com/wn/'

# 默认头文件
DEFAULT_HEADER = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'
        }

USER_AGENT = ['Mozilla/5.0(Macintosh;IntelMacOSX10.6;rv:2.0.1)Gecko/20100101Firefox/4.0.1', 'Mozilla/4.0(compatible;MSIE6.0;WindowsNT5.1)', 'Opera/9.80(WindowsNT6.1;U;en)Presto/2.8.131Version/11.11', 'Mozilla/5.0(Macintosh;IntelMacOSX10_7_0)AppleWebKit/535.11(KHTMLlikeGecko)Chrome/17.0.963.56Safari/535.11', 'Mozilla/4.0(compatible;MSIE7.0;WindowsNT5.1)', 'Mozilla/4.0(compatible;MSIE7.0;WindowsNT5.1;Trident/4.0;SE2.XMetaSr1.0;SE2.XMetaSr1.0;.NETCLR2.0.50727;SE2.XMetaSr1.0)', 'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko', 'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML like Gecko) Chrome/28.0.1500.95 Safari/537.36', 'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; rv:11.0) like Gecko)', 'Mozilla/5.0 (Windows; U; Windows NT 5.2) Gecko/2008070208 Firefox/3.0.1', 'Mozilla/5.0 (Windows; U; Windows NT 5.1) Gecko/20070309 Firefox/2.0.0.3', 'Mozilla/5.0 (Windows; U; Windows NT 5.1) Gecko/20070803 Firefox/1.5.0.12', 'Opera/9.27 (Windows NT 5.2; U; zh-cn)', 'Mozilla/5.0 (Macintosh; PPC Mac OS X; U; en) Opera 8.0', 'Opera/8.0 (Macintosh; PPC Mac OS X; U; en)', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.12) Gecko/20080219 Firefox/2.0.0.12 Navigator/9.0.0.6', 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Win64; x64; Trident/4.0)', 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0)', 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.2; .NET4.0C; .NET4.0E)', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML like Gecko) Maxthon/4.0.6.2000 Chrome/26.0.1410.43 Safari/537.1', 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.2; .NET4.0C; .NET4.0E; QQBrowser/7.3.9825.400)', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:21.0) Gecko/20100101 Firefox/21.0', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML like Gecko) Chrome/21.0.1180.92 Safari/537.1 LBBROWSER', 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0; BIDUBrowser 2.x)', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.11 (KHTML like Gecko) Chrome/20.0.1132.11 TaoBrowser/3.0 Safari/536.11']


class html_downloader():
    def __init__(self,china = True, world = False,
                 qiyeurl = QIYE_URL, xiciurl =XICI_URL):
        self.qiyeurl = qiyeurl
        self.xiciurl = xiciurl
        self.china = china
        self.world = world

        self.ip_pool = self.refresh_ip_pool()
        self.ip_buffer = set()
        self.ip_error = {}
        self.header_pool = self.refresh_header_pool()

        self.ip_pool_refresh_time = 0

    def refresh_ip_pool(self):
        if self.world:
            iplist = list(set(self.get_ip_list1() + self.get_ip_list2()))
        else:
            if self.china:
                iplist = list(set(self.get_ip_list1()+self.get_ip_list2()))
            else:
                iplist = self.get_ip_list1()
        pool = set(iplist)
        return pool

    # 使用qiye的IProxy程序获取ip池
    def get_ip_list1(self):
        if self.world:
            country = ''
        else:
            if self.china:
                country = '/?county=国内'
            else:
                country = '/?county=国外'
        try:
            r = requests.get(urljoin(self.qiyeurl, country))
            ip_list = ['{}:{}'.format(ipport[0], ipport[1]) for ipport in json.loads(r.text)]
        except:
            ip_list = []
        return ip_list

    #从西刺代理直接爬取获取ip池
    def get_ip_list2(self):
        try:
            web_data = requests.get(self.xiciurl, headers=DEFAULT_HEADER)
            soup = BeautifulSoup(web_data.text, 'html.parser')
            ips = soup.find_all('tr')
            ip_list = []
            for i in range(1, len(ips)):
                ip_info = ips[i]
                tds = ip_info.find_all('td')
                ip_list.append(tds[1].get_text() + ":" + tds[2].get_text())
        except:
            ip_list = []
        return ip_list

    def pick_ip(self):
        time_now = time.time()
        if len(self.ip_buffer) > 0:
            temp_ip = self.ip_buffer.pop()
        elif len(self.ip_pool - set(self.ip_error.keys())) == 0:
            # refresh error proxy 把一个小时前不能使用的ip过期
            self.ip_error = {k: v for k, v in self.ip_error.items() if v < time_now + 3600}
            #  防止进入无限循环
            try:
                self.ip_error.popitem()
            except:
                pass
            self.ip_pool = self.refresh_ip_pool()
            self.ip_pool_refresh_time +=1
            (time_now,temp_ip) = self.pick_ip()
        else:
            temp_ip= self.ip_pool.pop()
        return (time_now,temp_ip)
    def ip2proxies(self,ip):
        proxies = {'http': 'http://{}'.format(ip),'https': 'https://{}'.format(ip)}
        return proxies

    def refresh_header_pool(self):
        pool = [{'User-Agent':i} for i in USER_AGENT]
        return pool

    def pick_headers(self):
        if len(self.header_pool) == 0:
            self.header_pool = self.refresh_header_pool()
        tempheaders = self.header_pool.pop()
        return tempheaders

    def request_proxy(self,url,
                      method = 'get', timeout = (DEFAULT_MAX_CONNECT_TIME,DEFAULT_MAX_READ_TIME),
                      max_iter_time = DEFAULT_MAX_ITER_TIME,
                      data=None, cookies=None, files=None,
                    auth=None, allow_redirects=True,
                    hooks=None, stream=None, verify=None, cert=None, json=None):
        send_kwargs = {
            'url': url, 'method': method, 'data': data,
            'cookies': cookies, 'files': files, 'auth': auth, 'timeout': timeout,
            'allow_redirects': allow_redirects, 'hooks': hooks, 'stream': stream,
            'verify': verify, 'cert': cert, 'json': json}

        response = None
        iter_time = 0

        while iter_time < max_iter_time and self.ip_pool_refresh_time <2:
            (time_now, temp_ip) = self.pick_ip()
            send_kwargs['proxies'] = self.ip2proxies(temp_ip)
            send_kwargs['headers'] = self.pick_headers()
            try:
                response = request(**send_kwargs)
                if response.status_code == 200:
                    self.ip_buffer.add(temp_ip)
                    response.close()
                    break
                else:
                    self.ip_error.update({temp_ip:time_now})
            except:
                self.ip_error.update({temp_ip:time_now})
        self.ip_pool_refresh_time  = 0
        return response

if __name__ == "__main__":
    t0 = time.time()
    print(t0)
    hd = html_downloader(world =True)
    print(len(hd.ip_pool))
    t1 = time.time()
    print(t1)
    print(t1-t0)
    url = ['https://www.indiegogo.com/projects/zero-reinventing-the-translator-for-everyone/coll',
           'https://www.indiegogo.com/projects/tyrian-gazette/hmco',
           'https://www.indiegogo.com/projects/jawbreakers-god-k1ng-graphic-novel/hmco',
           'https://www.indiegogo.com/projects/camect-world-s-smartest-most-private-camera-hub/hmco',
           'https://www.indiegogo.com/campaign_collections/staff-picks']
    t = time.time()
    for i in url:
        print('*'*100)
        res = hd.request_proxy(i)
        print(res.status_code)
        print(res.text)
        t2 = time.time()
        print(t2)
        print('time:  {}'.format(t2-t))
        t = t2

