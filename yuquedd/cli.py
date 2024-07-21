import click
from click.testing import CliRunner
import lakedoc
from lakedoc import string
from . import const, service


@click.command()
@click.argument('url', default='')
@click.option('--path', 'path', '-p', default='./', help='指定 md 文档保存的路径')
@click.option('--savesource', 'savesource', '-s', is_flag=True, help='是否保存源 HTML 内容')
@click.option('--cookies', 'cookies', '-c', default='', help='携带 cookies 访问')
@click.option('--proxies', 'proxies', '-p', default='', help='指定代理："http=proxy1,https=proxy2"')
@click.option('--encoding', 'encoding', '-e', default='utf-8', help='指定保存文件的编码')
def cli_execute(url, path, savesource, cookies, proxies, encoding):
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
    if savesource:
        with open(f'./{book.title}.html', 'w', encoding=encoding) as fw:
            fw.write(content)

    save_path = service.get_save_path(path, book)
    lakedoc.convert(content, save_path, encoding=encoding, is_file=False, builder='lxml', title=f'# {book.title}')
    print(string.color_string(f'> 文档已保存，路径为：{str(save_path.absolute().resolve())}\n', 'green'))


def execute(url: str, path='./', savesource=False, cookies='', proxies='', encoding='utf-8', nohint=False):
    """
    执行主要功能的 Python 方法

    :param url: 要访问的 URL
    :param path: 保存路径
    :param savesource: 是否保存源 HTML 内容
    :param cookies: 携带的 cookies
    :param proxies: 指定的代理
    :param encoding: 保存文件的编码
    :param nohint: 是否打印提示
    """
    args = [url]
    if path:
        args.extend(['--path', path])
    if savesource:
        args.append('--savesource')
    if cookies:
        args.extend(['--cookies', cookies])
    if proxies:
        args.extend(['--proxies', proxies])
    if encoding:
        args.extend(['--encoding', encoding])

    runner = CliRunner()
    result = runner.invoke(cli_execute, args)

    if not nohint:
        print(result.output)
