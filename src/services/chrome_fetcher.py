"""使用 Chrome headless 获取无法用 SSL 访问的页面"""
import os
import subprocess
import sys
import tempfile

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def fetch_with_chrome(url: str, timeout: int = 30) -> str:
    """
    使用 Chrome headless 模式获取页面内容
    适用于其他工具 SSL 不兼容但 Chrome 可以访问的网站
    """
    if not os.path.exists(CHROME_PATH):
        raise RuntimeError(f"Chrome not found at {CHROME_PATH}")

    run_kwargs = {
        'capture_output': True,
        'text': True,
        'timeout': timeout + 5,
    }
    # On Windows, use CREATE_NO_WINDOW to avoid terminal flash
    if sys.platform == "win32":
        run_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

    result = subprocess.run(
        [
            CHROME_PATH,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--dump-dom",
            "--virtual-time-budget=5000",
            url,
        ],
        **run_kwargs
    )

    # Chrome 会输出 SSL 错误到 stderr，HTML 在 stdout
    # 过滤掉错误行，保留 HTML
    html_lines = []
    for line in result.stdout.splitlines():
        if line.startswith("<"):
            html_lines.append(line)

    html = "\n".join(html_lines)
    if not html:
        # 如果没找到 HTML 标签，返回整个 stdout
        html = result.stdout

    return html


if __name__ == "__main__":
    # 测试
    html = fetch_with_chrome("https://anime1.pw/")
    print(f"获取到 {len(html)} 字节")
    print(html[:500])
