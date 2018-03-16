#-*-coding:utf-8-*-
import requests
import chardet
import json
import re
import os
from multiprocessing import Pool
from hashlib import md5
from bs4 import BeautifulSoup
from requests import RequestException
from json import JSONDecodeError
from urllib.parse import urlencode
headers = {'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:58.0) Gecko/20100101 Firefox/58.0'}

#获取起始页的HTML,主要目的是提取每个图集的入口
def get_first_page(offset):
    data = {
    'autoload':'true',
    'count':20,
    'cur_tab':3,
    'format':'json',
    'from': 'gallery',
    'keyword':'街拍',
    'offset':offset
    }
    url = 'https://www.toutiao.com/search_content/?'+urlencode(data)
    try:
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            response.encoding = chardet.detect(response.content)['encoding']
            return response.text
        return None
    except RequestException:
        print('请求起始页失败',url)

#分析起始页的HTML，提取每个图集的URL
def parse_first_page(html):
    try:
        data = json.loads(html)
        if data and 'data' in data.keys():
            for item in data.get('data'):
                yield item['article_url']
    except JSONDecodeError:
        pass

#获取每一个图集的html
def get_page_detail(url):
    try:
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            response.encoding = chardet.detect(response.content)['encoding']
            return response.text
        return None
    except RequestException:
        print('请求详情页失败',url)

#分析每一个图集的URL，提取到图片的URL和title
def parse_page_detail(html,url):
    try:
        soup = BeautifulSoup(html,'lxml')
        title = soup.select('title')[0].get_text()
        pattern = re.compile('BASE_DATA.galleryInfo = (.*?)</script>',re.S)
        result = re.search(pattern,html)
        galleryinfo = result.group()
        if 'gallery' in galleryinfo:
            dataclean = galleryinfo.replace('BASE_DATA.galleryInfo = ','').replace('</script>','').replace('\\','')
            # print (dataclean)
            pattern = re.compile('    gallery: JSON.parse(.*)')
            data = re.search(pattern,dataclean).group()
            final_data = data.replace('    gallery: JSON.parse("','').replace('"),','')
            try:
                jsondata = json.loads(final_data)
                if jsondata and 'sub_images' in  jsondata.keys():
                    sub_images = jsondata.get('sub_images')
                    images_url = [item.get('url') for item in sub_images]
                    for img_url in images_url:
                        download_image(img_url)
                    return {
                        'title':title,
                        'url':url,
                        'images':images_url
                    }
                return None
            except JSONDecodeError:
                print('json数据解析失败')
    except Exception:
        print('请求详情页失败',url)

#下载图片
def download_image(url):
    print('正在下载图片',url)
    try:
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            if __name__ == '__main__':
                response.encoding = chardet.detect(response.content)['encoding']
                save_image_to_computer(response.content)
            return None
    except RequestException:
        print('加载图片失败')

#下载的图片保存到本地
def save_image_to_computer(content):
    print('正在保存图片到本地')
    try:
        filepath = '{0}\{1}.{2}'.format(os.getcwd(),md5(content).hexdigest(),'jpg')
        with open(filepath,'wb') as f:
            f.write(content)
    except Exception:
        print('保存图片失败')

#保存到txt文件中
def save_to_file(data):
    print('正在保存',data)
    try:
        data = json.dumps(data,ensure_ascii=False)
        with open('jiepai.txt','a+',encoding='utf-8') as f:
            f.write(data+'\n')
    except Exception:
        print('保存到文件失败')


def main(offset):
    html = get_first_page(offset)
    for url in parse_first_page(html):
        html = get_page_detail(url)
        if html:
            result = parse_page_detail(html,url)
            # print(result)
            save_to_file(result)




if __name__ == '__main__':
    pool = Pool()
    pool.map(main,[i*20 for i in range(0,3)])
