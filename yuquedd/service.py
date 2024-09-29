import json
import re
import requests
from urllib.parse import unquote
from pathlib import Path
from . import const


class Book(object):
    def __init__(self, id_, title, author, book_type, doc_type, slug, desc):
        self.id = id_
        self.title = title
        self.author = author
        self.book_type = book_type
        self.doc_type = doc_type
        self.slug = slug
        self.desc = desc

    def __str__(self):
        return f"""{'BEGIN'.center(66, '-')}
标题：{self.title}({self.id})
作者：{self.author}  文档类型：{self.doc_type}  slug：{self.slug}
描述：{self.desc}
{'END'.center(66, '-')}
"""


def set_options(cookie, proxies):
    if cookie:
        const.headers['Cookie'] = cookie

    if proxies:
        try:
            proxy_list = proxies.split(',')
            proxy_dict = {scheme: proxy for scheme, proxy in (p.split('=') for p in proxy_list)}
        except ValueError:
            print('代理参数格式不正确，参考："http=proxy1,https=proxy2"')
            return None
        const.proxies.update(proxy_dict)


def get_save_path(raw_path: str, book: Book):
    raw_path = Path(raw_path)
    if raw_path.is_dir():
        if not raw_path.exists():
            print(f'警告：保存的路径不存在（{str(raw_path.absolute().resolve())}），默认保存在当前文件夹')
            raw_path = Path('./')
        save_path = raw_path / f'{book.title}.md'
    else:
        save_folder = raw_path.parent.resolve()
        save_filename = raw_path.name
        if not save_folder.exists():
            print(f'警告：保存的路径不存在（{str(save_folder.absolute().resolve())}），默认保存在当前文件夹')
            save_path = Path('./') / save_filename
        else:
            save_path = raw_path
    return save_path


def create_book(url):
    page_html_resp = requests.request('GET', url, headers=const.headers, proxies=const.proxies)
    page_html = page_html_resp.text
    match_result = re.findall(r'decodeURIComponent\("(.*)"\)', page_html)
    raw_data = match_result[0] if match_result else None
    if raw_data:
        try:
            page_data = json.loads(unquote(raw_data))
            book = page_data['book']
            group = page_data['group']
            doc = page_data['doc']

            book_id = book['id']
            book_type = book['type']
            doc_title = doc['title']
            doc_type = doc['type']
            doc_desc = doc['description']
            doc_slug = doc['slug']
            book_author = group['name']

            return Book(book_id, doc_title, book_author, book_type, doc_type, doc_slug, doc_desc)
        except KeyError:
            return None


def get_content(book):
    api = f'https://www.yuque.com/api/docs/{book.slug}'
    if book.id:
        const.content_params['book_id'] = book.id
    response = requests.request('GET', api, params=const.content_params, proxies=const.proxies, headers=const.headers)
    result = response.json()
    try:
        content = result['data']['content']
        return content
    except KeyError:
        return None
