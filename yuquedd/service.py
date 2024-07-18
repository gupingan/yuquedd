import json
import re
import typing as t
import requests
from urllib.parse import unquote
from lxml import etree
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


class Node:
    def __init__(self):
        """markdown 节点"""
        self.text = []
        self.tags = []

    def __repr__(self):
        return f'<Node: {self.tags} {self.text}>'

    def to_string(self):
        """当前节点对应的 markdown 语法文本"""
        data = ''
        for tag, text in zip(self.tags, self.text):
            if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                data += f'{"#" * int(tag[1])} {text}\n'
            elif tag == 'p':
                data += f'{text}'
            elif tag == 'strong':
                data += f'**{text}**'
            elif tag == 'span':
                data += text.strip()
            elif tag.startswith('code_'):
                code_mode = tag.split('_')[-1]
                data += f'\n```{code_mode}\n{text}\n```\n'
            elif tag == 'img':
                data += f'![图片未加载]({text})\n'
            elif tag.startswith('ul_li_'):
                indent = int(tag.split('_')[-1])
                data += '\t' * indent
                data += f'- {text}\n'
            elif tag.startswith('ol_li_'):
                index = tag.split('_')[-2]
                indent = int(tag.split('_')[-1])
                data += '\t' * indent
                data += f'{index}. {text}\n'
        return data


class Converter:
    def __init__(self, html_content: t.Union[str, bytes], encoding: t.Union[str] = 'utf-8'):
        if isinstance(html_content, str):
            self.html_content = html_content
        elif isinstance(html_content, bytes):
            self.html_content = html_content.decode(encoding)
        else:
            self.html_content = ''

        self.tree = etree.HTML(self.html_content)
        self.result = []
        self.nodes = []

    def execute(self):
        # 从表层标签出发
        root = self.tree.xpath('//body/*')
        for elem in root:
            node = Node()
            self.nodes.append(node)
            # 递归捕获标签特征与标签文本，完善节点信息
            self._create_node(node, elem)

        for node in self.nodes:
            self.result.append(node.to_string())

    def _create_node(self, node: t.Union[Node], elem):
        """根据当前标签与子标签对应处理"""
        if elem.tag:
            if elem.tag in ['ul', 'ol']:
                self._parse_list(node, elem)
            elif elem.tag == 'card':
                name = elem.get('name', '')
                encoded_value = elem.get('value', '')[5:]
                decoded_value = unquote(encoded_value)
                json_data = json.loads(decoded_value)
                if name == 'codeblock':
                    code_block = json_data.get('code', '')
                    mode = json_data.get('mode', 'text')
                    node.tags.append(f'code_{mode}')
                    node.text.append(code_block)
                elif name == 'image':
                    img_src = json_data.get('src', '')
                    node.tags.append('img')
                    node.text.append(img_src)
            else:
                children = elem.getchildren()
                if elem.text:
                    node.text.append(elem.text)
                    ptag = elem.getparent().tag
                    if ptag == 'body' or ptag == 'html':
                        ptag = 'span'
                    node.tags.append(ptag)

                for child in children:
                    self._create_node(node, child)

    @staticmethod
    def _parse_list(node: t.Union[Node], elem):
        """解析列表，完善对应 Node 信息"""
        list_type = 'ul' if elem.tag == 'ul' else 'ol'
        children = elem.getchildren()
        indent = elem.get('data-lake-indent', '0')
        for index, child in enumerate(children):
            if child.tag == 'li':
                new_text = child.text or ''
                new_tag = f'{list_type}_li_0'
                if list_type == 'ol':
                    new_tag = f'{new_tag}_{index + 1}'
                new_tag = f'{new_tag}_{indent}'
                li_children = child.getchildren()
                for li_child in li_children:
                    if li_child.tag == 'strong':
                        li_strong_children = li_child.getchildren()
                        for li_strong_child in li_strong_children:
                            if li_strong_child.tag == 'span':
                                if li_strong_child.text:
                                    new_text += f'**{li_strong_child.text}**'
                    elif li_child.tag == 'span':
                        if li_child.text:
                            new_text += li_child.text

                node.tags.append(new_tag)
                node.text.append(new_text)


def html2markdown(content: t.Union[str, bytes], encoding: t.Union[str] = 'utf-8'):
    """
    将 html 内容转为 markdown 语法文本列表
    :param content: html 内容
    :param encoding: 转换时，如果传入字节串，根据编码解析，默认为 utf-8
    :return: markdown 内容的列表 ['# Python 入门', '## 变量', ...]
    """
    converter = Converter(content, encoding)
    converter.execute()
    return converter.result
