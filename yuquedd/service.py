import json
import re
import typing as t
import requests
from html.parser import HTMLParser
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
            elif tag in ['em', 'i']:
                data += f'*{text}*'
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
                tags = tag.split('_')
                index = tags[-2]
                indent = int(tags[-1])
                data += '\t' * indent
                data += f'{index}. {text}\n'
            elif tag == 'hr':
                data += f'\n---{text}'
            elif tag.startswith('table_'):
                data += text

        return data


class TableHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_td = False
        self.in_th = False
        self.current_row = []
        self.rows = []
        self.cell_data = ""

    def handle_starttag(self, tag, attrs):
        if tag in ('td', 'th'):
            self.in_td = tag == 'td'
            self.in_th = tag == 'th'
            self.cell_data = ""

    def handle_endtag(self, tag):
        if tag in ('td', 'th'):
            self.current_row.append(self.cell_data.strip())
            self.in_td = False
            self.in_th = False
        elif tag == 'tr':
            self.rows.append(self.current_row)
            self.current_row = []

    def handle_data(self, data):
        if self.in_td or self.in_th:
            self.cell_data += data

class Converter:
    def __init__(self, html_content: t.Union[str, bytes], encoding: t.Union[str] = 'utf-8'):
        if isinstance(html_content, str):
            self.html_content = html_content
        elif isinstance(html_content, bytes):
            self.html_content = html_content.decode(encoding)
        else:
            self.html_content = ''

        # with open('./test.html', 'w', encoding=encoding) as fw:
        #     fw.write(self.html_content)

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
            print(node)
            self.result.append(node.to_string())

    def _create_node(self, node: t.Union[Node], elem):
        """根据当前标签与子标签对应处理"""
        if elem.tag:
            if elem.tag in ['ul', 'ol']:
                self._parse_list(node, elem)
            elif elem.tag == 'card':
                name = elem.get('name', '')
                if name == 'codeblock':
                    encoded_value = elem.get('value', '')[5:]
                    decoded_value = unquote(encoded_value)
                    json_data = json.loads(decoded_value)
                    code_block = json_data.get('code', '')
                    mode = json_data.get('mode', 'text')
                    node.tags.append(f'code_{mode}')
                    node.text.append(code_block)
                elif name in ['image', 'flowchart2']:
                    encoded_value = elem.get('value', '')[5:]
                    decoded_value = unquote(encoded_value)
                    json_data = json.loads(decoded_value)
                    img_src = json_data.get('src', '')
                    node.tags.append('img')
                    node.text.append(img_src)
                elif name == 'hr':
                    node.tags.append('hr')
                    node.text.append('\n')
                elif name == 'table':
                    encoded_value = elem.get('value', '')[5:]
                    decoded_value = unquote(encoded_value)
                    json_data = json.loads(decoded_value)
                    rows = json_data.get('rows', '0')
                    cols = json_data.get('cols', '0')
                    html = json_data.get('html', '')

                    # Parse the HTML table
                    parser = TableHTMLParser()
                    parser.feed(html)
                    table_rows = parser.rows

                    # Convert to Markdown table
                    markdown_table = []
                    for row in table_rows:
                        markdown_table.append('| ' + ' | '.join(row) + ' |')
                    if len(markdown_table) > 1:
                        # Add header separator if there is a header
                        header_separator = '| ' + ' | '.join(['---'] * len(table_rows[0])) + ' |'
                        markdown_table.insert(1, header_separator)

                    node.tags.append(f'table_{rows}_{cols}')
                    node.text.append('\n'.join(markdown_table))
            else:
                children = elem.getchildren()
                if elem.text:
                    node.text.append(elem.text)
                    if elem.tag == 'span':
                        ptag = elem.getparent().tag
                        if ptag == 'body' or ptag == 'html':
                            ptag = elem.tag
                        node.tags.append(ptag)
                    else:
                        node.tags.append(elem.tag)

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
