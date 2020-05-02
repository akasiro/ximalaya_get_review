import pandas as pd
import requests, re, os, time, sys
from bs4 import BeautifulSoup
from urllib.parse import urljoin
sys.path.append('scrapy_toolv2')
from html_dowloader import html_downloader

class ximalaya():
    def __init__(self, namelist = 'namelist.csv'):
        self.save_path = 'data'
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)
        self.webdomain = 'https://www.ximalaya.com/'
        self.hd = html_downloader(world=True)
        
        self.error = 'error.txt'
        if not os.path.exists(self.error):
            with open(self.error, 'a+') as f:
                f.write('||')
            self.usedlist = []
        else:
            with open(self.error, 'r') as f:
                self.usedlist = f.read().split('||')
        
        self.used = 'used.txt'
        if not os.path.exists(self.used):
            with open(self.used, 'a+') as f:
                f.write('||')
            self.usedlist = self.usedlist + []
        else:
            with open(self.used, 'r') as f:
                self.usedlist = self.usedlist + f.read().split('||')
        
        df = pd.read_csv(namelist)
        self.namelist = df['LessonName'].values.tolist()
    def get_web_page(self, project_name):
        url = 'https://www.ximalaya.com/search/{}'.format(project_name)
        r = self.hd.request_proxy(url)
        soup = BeautifulSoup(r.content)
        titles = soup.find_all('a', {'class':'xm-album-title'})
        authors = soup.find_all('p', {'class':'createBy'})
        
        if titles:
            href = titles[0].get('href')
        else:
            href = None
            
        if authors:
            author = authors[0].get('title')
        else:
            author = None
        
        return {'href':[href], 'name':[project_name], 'author':[author]}
    
    def get_review_num(self, results):
        url = results['href'][0]
        if url != None:
            url = urljoin(self.webdomain,url)
            r = self.hd.request_proxy(url)
            soup = BeautifulSoup(r.content)
            mainpart = soup.find('div', {'class':'head _Qp'})
            mainpart_spans = mainpart.find_all('span',{'class':'title'})
            voice = mainpart_spans[0].span.get_text().replace('（','').replace('）','')
            review = mainpart_spans[1].span.get_text().replace('（','').replace('）','')
            results['voice'] = [voice]
            results['review'] = [review]
            return results
        else:
            return None
        
    def get_by_namelist(self, namelist, max_chunk = 200):
        count = 1
        df = pd.DataFrame()
        for n in namelist:
            if count >= max_chunk:
                break
            if n in self.usedlist:
                continue
            try:
                r1 = self.get_web_page(n)
                r2 = self.get_review_num(r1)
            except:
                self.usedlist.append(n)
                with open(self.error,'a+') as f:
                    f.write('{}||'.format(n))
                continue
            if r2 == None:
                self.usedlist.append(n)
                with open(self.error, 'a+') as f:
                    f.write('{}||'.format(n))
                continue
            tmpdf = pd.DataFrame(r2)
            df = df.append(tmpdf)
            self.usedlist.append(n)
            with open(self.used, 'a+') as f:
                f.write('{}||'.format(n))
            count +=1
        df.to_csv(os.path.join(self.save_path,'{}.csv'.format(int(time.time()))), index =False, encoding = 'utf8')
        print('1 file success')
    def main(self):
        while len(self.usedlist) < len(self.namelist):
            self.get_by_namelist(self.namelist)
        print('mission compelete')
if __name__ == '__main__':
    test = ximalaya()
    test.main()
