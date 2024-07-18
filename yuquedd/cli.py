import click
from pathlib import Path
from . import const
from .service import create_book, get_content, html2markdown


@click.command()
@click.argument('url', default='')
@click.option('--path', 'path', '-p', default='./', help='指定 md 文档保存的路径')
@click.option('--cookies', 'cookies', '-c', default='', help='携带 cookies 访问')
@click.option('--proxies', 'proxies', '-p', default='', help='指定代理："http=proxy1,https=proxy2"')
@click.option('--encoding', 'encoding', '-e', default='utf-8', help='指定保存文件的编码')
def execute(url, path, cookies, proxies, encoding):
    if not url or not const.url_pattern.match(url):
        print('语雀文档地址不正确，参考：https://www.yuque.com/.../.../...')
        return None

    raw_path = Path(path)

    if cookies:
        const.headers['Cookies'] = cookies

    if proxies:
        try:
            proxy_list = proxies.split(',')
            proxy_dict = {scheme: proxy for scheme, proxy in (p.split('=') for p in proxy_list)}
        except ValueError:
            print('代理参数格式不正确，参考："http=proxy1,https=proxy2"')
            return None
        const.proxies.update(proxy_dict)

    book = create_book(url)
    if not book:
        print('获取知识库文档对象失败，请检查方法 `create_book`')
        return None
    print('BEGIN'.center(66, '-'))
    print(f'标题：{book.title}({book.id})')
    print(f'作者：{book.author}    文档类型：{book.doc_type}    slug：{book.slug}')
    print(f'描述：{book.desc}')

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

    print(f'保存路径：{str(save_path.absolute().resolve())}')
    print('END'.center(66, '-'))
    print()

    content = get_content(book)
    markdown = html2markdown(content)

    with save_path.open('w', encoding=encoding) as fw:
        fw.write('\n'.join(markdown))
    print(f'> 文档已保存，路径为：{str(save_path.absolute().resolve())}\n')
