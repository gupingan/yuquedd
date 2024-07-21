import click
import lakedoc
from lakedoc import string
from . import const, service


@click.command()
@click.argument('url', default='')
@click.option('--path', 'path', '-p', default='./', help='指定 md 文档保存的路径')
@click.option('--cookies', 'cookies', '-c', default='', help='携带 cookies 访问')
@click.option('--proxies', 'proxies', '-p', default='', help='指定代理："http=proxy1,https=proxy2"')
@click.option('--encoding', 'encoding', '-e', default='utf-8', help='指定保存文件的编码')
def execute(url, path, cookies, proxies, encoding):
    if not url or not const.url_pattern.match(url):
        print(string.color_string('Error：语雀文档地址不正确，参考：https://www.yuque.com/.../.../...', 'red'))
        return None

    service.set_options(cookies, proxies)

    book = service.create_book(url)
    if not book:
        print(string.color_string('Error：获取知识库文档对象失败，可能文档已被移动、删除或不被支持', 'red'))
        return None
    print(str(book))

    content = service.get_content(book)
    save_path = service.get_save_path(path, book)
    lakedoc.convert(content, save_path, encoding=encoding, is_file=False, builder='lxml', title=f'# {book.title}')
    print(string.color_string(f'> 文档已保存，路径为：{str(save_path.absolute().resolve())}\n', 'green'))
