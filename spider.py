#coding:utf-8
'''
    爬取CSDN各个板块的爬虫
'''
import requests
import re
import json
import os

# url1：从首页点进去的文章列表
url1 = "https://blog.csdn.net/nav/python"
# url2：请求滚动后加载的文章列表
url2 = "https://blog.csdn.net/api/articles"

NUM = 100

def update_diglist(data_ids, cookies_dict):
    update_url = 'https://blog.csdn.net/api/ArticleDigg/isDiggList'
    header = {\
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36',
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", 'Connection': 'close'}

    data_ids = list(map(lambda x: 'article_id[]='+x, data_ids))
    payload = '&'.join(data_ids)
    payload = payload.encode('utf-8')
    res = requests.post(update_url, data=payload, headers=header, cookies=cookies_dict)

    cookies = requests.utils.dict_from_cookiejar(res.cookies)
    for key,value in cookies.items():
        cookies_dict[key] = value

    return cookies_dict

def get_articles(url, cookies_dict):
    '''
        1. 初始页面返回21篇文章
        2. 向服务器更新文章列表
    '''
    header = {
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'
        
    }
    res = requests.get(url,headers=header, cookies=cookies_dict) # 刷新一下页面和文章
    html = res.text
    offset_p = re.compile(r'shown-offset="\d+"')
    offset = offset_p.findall(html)[0]
    offset = offset[14:-1]

    artciles_p = re.compile(r'<div class="title">[\w\W]*?</h2>')
    articles_html = artciles_p.findall(html)

    title_p = re.compile(r' >[\w\W]*?</a>')
    url_p = re.compile(r'<a href="[\S]*?"')
    article_id_p = re.compile(r'\d+$')
    articles = []
    for art_html in articles_html:
        title = title_p.findall(art_html)[0]
        title = title[2:-4].strip()
        url = url_p.findall(art_html)
        url = url[0][9:-1]
        data_id = article_id_p.findall(url)[0]
        articles.append({'title': title, 'url':url, 'data_id':data_id})

    cookies = requests.utils.dict_from_cookiejar(res.cookies)
    for key,value in cookies.items():
        cookies_dict[key] = value

    data_ids = [i['data_id'] for i in articles]
    cookies_dict = update_diglist(data_ids, cookies_dict)
    return offset, articles, cookies_dict

def get_more(url, cookies_dict):
    '''
        1. 像鼠标滚动一样，多请求10片文章
        2. 向服务器更新文章列表
    '''
    header = {
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36',
    }
    params = 'type=more&category=python&shown_offset=0'
    res = requests.get(url,headers=header,params=params, cookies=cookies_dict)
    res.encoding = 'unicode'

    # content = res.content.decode('unicode-escape')
    r_json = res.json()
    articles = r_json['articles']

    article_id_p = re.compile(r'\d+$')

    for i in range(len(articles)):
        url = articles[i]['url']
        title = articles[i]['title'].strip()
        data_id = article_id_p.findall(url)[0]
        articles[i] = {'title': title, 'data_id':data_id, 'url':url}

    cookies = requests.utils.dict_from_cookiejar(res.cookies)
    for key,value in cookies.items():
        cookies_dict[key] = value

    data_ids = [i['data_id'] for i in articles]
    cookies_dict = update_diglist(data_ids, cookies_dict)
    return articles, cookies_dict

def read_cookies():
    cookies_dict = dict()
    if os.path.exists("cookies.txt"):
        with open("cookies.txt", "r") as fp:
            cookies = json.load(fp)
            for key,value in cookies.items():
                cookies_dict[key] = value
    return cookies_dict

def write_cookies(cookies_dict):
    with open("cookies.txt", "w") as fp:
        json.dump(cookies_dict, fp)

if __name__ == '__main__':
    cookies_dict = read_cookies()

    articles = []
    offset, res_articles, cookies_dict = get_articles(url1, cookies_dict)
    articles += res_articles
    while len(articles) < NUM:
        res_articles, cookies_dict = get_more(url2, cookies_dict)
        articles += res_articles
    articles = articles[:NUM]
    assert(len(articles) ==NUM)

    count = 0
    for a in articles:
        print(str(count)+'. '+a['title'], a['url'])
        count += 1
    write_cookies(cookies_dict)

    