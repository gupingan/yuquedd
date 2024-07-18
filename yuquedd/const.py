import re

url_pattern = re.compile(r'^https://www\.yuque\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)$')

proxies = {'http': None, 'https': None}
headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Host': 'www.yuque.com'
}

content_params = {
    'include_contributors': True,
    'include_like': True,
    'include_hits': True,
    'merge_dynamic_data': False,
}