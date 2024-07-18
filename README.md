# 开发中

## 简述

`yuquedd` 是一个基于 `Python` 开发、可以将语雀的公共知识库 `html` 文档转为 `markdown` 文档格式的工具，尽管无法百分百还原，但是已经足够使用。

注意：本项目采用 MIT 许可证。请查看 [LICENSE](https://github.com/gupingan/yuequedd?tab=MIT-1-ov-file) 文件以了解更多信息。

> 本项目为开源项目，仅供学习研究使用，如若商用或者其他用途，请使用其他模块，使用本模块产生的任何纠纷与作者无关。
>
> 如该项目侵犯到贵司或组织的相关权益，请尽快联系我删除。

## 安装模块

### 1. 本地

如果您不想从源代码安装，您可以直接安装发布到 GitHub Releases 页面的打包版本。

首先，下载最新的发布包 `yuquedd-x.x.x.tar.gz` 从 [GitHub Releases](https://github.com/gupingan/yuquedd/releases) 页面。

接着，您可以使用 pip 等包管理工具来安装下载的 `.tar.gz` 文件：

```bash
pip install ./yuquedd-x.x.x.tar.gz
```

其中 `x.x.x` 为您下载 `.tar.gz` 文件确版本，并确保指定安装包文件路径是正确的。

### 2. 网络

```bash
pip install yuquedd
```

假如上述命令执行后发生了一些错误，可以选择使用`pip3`命令或者添加镜像源等等方式解决。

## 快速使用

安装完本模块后，您可以按照以下方式使用 `yuquedd`：

```bash
# 在任意终端位置，使用下述命令
yuquedd <url>  # 其中 url 形如：https://www.yuque.com/.../.../...
```

或者，新建一个 python 文件：

```python
import yuquedd

yuquedd.execute(('https://www.yuque.com/.../.../...',))
```

