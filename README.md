# anime1-cover

从 [Anime1.me](https://anime1.me) 获取番剧封面的小工具。

## 功能

- 自动获取 Anime1.me 第一页番剧列表
- 从 Bangumi 搜索匹配番剧封面
- 生成带封面的 Markdown 文件

## 使用方法

```bash
# 运行脚本
python3 fetch_anime1_covers.py

# 查看生成的封面列表
cat anime1-covers.md
```

## 输出文件

| 文件 | 说明 |
|------|------|
| `anime1-covers.md` | 带封面的番剧列表 (Markdown) |
| `anime1_data.json` | 详细数据 (JSON) |

## 示例

```
| # | 番剧名 | 封面 | Anime1 | 集数 |
|---|--------|------|--------|------|
| 1 | Princession Orchestra | <img src="..." width="150"> | [链接](...) | 37 |
```

## 依赖

- Python 3.7+
- beautifulsoup4
- deep-translator

## 安装依赖

```bash
pip install beautifulsoup4 deep-translator
```

## License

MIT
