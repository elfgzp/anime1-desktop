#!/usr/bin/env python3
"""
SSL 连接问题分析

问题: anime1.pw 服务器的 SSL 配置与 Python/OpenSSL 不兼容，
      但与 Apple Security 框架 (Safari/WebKit) 兼容

原因分析:
1. WebKit 使用 Apple Security.framework
2. Python requests 使用 OpenSSL/urllib3
3. 两者 SSL 堆栈实现不同，支持的 cipher suites 不同

可能的解决方案:
1. 使用 pyobjc 直接调用 Apple Security 框架 (复杂)
2. 使用 macOS 的 curl (已测试，失败)
3. 继续使用当前方案: 前端 webview 获取 HTML (最简单有效)
"""

import subprocess
import ssl
import socket

def test_ssl_tls_versions():
    """测试不同的 TLS 版本"""
    print("测试 TLS 版本支持...")

    # 使用 OpenSSL s_client 测试
    result = subprocess.run(
        ['openssl', 's_client', '-connect', 'anime1.pw:443', '-tls1_2'],
        input='', capture_output=True, text=True, timeout=10
    )
    print(f"TLS 1.2: {'✅ 支持' if 'CONNECTED' in result.stdout else '❌ 不支持'}")

    result = subprocess.run(
        ['openssl', 's_client', '-connect', 'anime1.pw:443', '-tls1_3'],
        input='', capture_output=True, text=True, timeout=10
    )
    print(f"TLS 1.3: {'✅ 支持' if 'CONNECTED' in result.stdout else '❌ 不支持'}")

def check_server_ssl_config():
    """检查服务器 SSL 配置"""
    print("\n检查服务器 SSL 配置...")

    # 获取证书信息
    result = subprocess.run(
        ['openssl', 's_client', '-connect', 'anime1.pw:443', '-servername', 'anime1.pw'],
        input='', capture_output=True, text=True, timeout=10
    )

    # 提取 cipher
    if 'Cipher is' in result.stdout:
        cipher = result.stdout.split('Cipher is')[1].split('\n')[0].strip()
        print(f"Cipher: {cipher}")

    # 检查证书链
    if 'Certificate chain' in result.stdout:
        print("证书链信息已获取")

def main():
    print("=" * 60)
    print("SSL 连接问题分析")
    print("=" * 60)

    test_ssl_tls_versions()
    check_server_ssl_config()

    print("\n" + "=" * 60)
    print("结论")
    print("=" * 60)
    print("anime1.pw 服务器的 SSL 配置可能:")
    print("1. 使用了只被 Apple Security 框架支持的 cipher suite")
    print("2. 或者有其他 macOS 特定的兼容性配置")
    print("\n推荐解决方案: 继续使用前端 webview 获取 HTML")
    print("=" * 60)

if __name__ == '__main__':
    main()
