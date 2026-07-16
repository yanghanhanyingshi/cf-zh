#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub IP 爬虫 - 自动生成 V2RayN 订阅
每 12 小时自动抓取并转换为 VLESS 协议
"""

import requests
import base64
import time
from datetime import datetime
from urllib.parse import quote

# 配置参数
GITHUB_URL = "https://raw.githubusercontent.com/yanghanhanyingshi/cf-linglu/refs/heads/main/vps789-100.txt"
WORKER_DOMAIN = "8888888888888888.88888888888888888888888888888888888.ccwu.cc"
UUID = "4c0b7280-76bb-495c-9c8b-f05712ebf805"
OUTPUT_FILE = "cf_subscription.txt"

# VLESS 参数模板
VLESS_PARAMS = {
    "encryption": "none",
    "security": "tls",
    "fp": "chrome",
    "insecure": "0",
    "allowInsecure": "0",
    "ech": "cloudflare-ech.com%2Bhttps%3A%2F%2Fdns.alidns.com%2Fdns-query",
    "type": "ws",
    "path": "%2F"  # URL 编码的 /
}


def fetch_ip_list():
    """从 GitHub 抓取 IP 列表"""
    print(f"[{datetime.now()}] 开始抓取 IP 列表...")
    try:
        response = requests.get(GITHUB_URL, timeout=30)
        response.raise_for_status()
        lines = response.text.strip().split('\n')
        print(f"成功抓取 {len(lines)} 个节点")
        return lines
    except Exception as e:
        print(f"抓取失败：{e}")
        return []


def parse_ip_line(line):
    """解析 IP 行，格式：domain:port#name"""
    try:
        line = line.strip()
        if not line:
            return None
        
        # 分离名称
        if '#' in line:
            ip_part, name = line.split('#', 1)
        else:
            ip_part = line
            name = "CF节点"
        
        # 分离域名和端口
        if ':' in ip_part:
            domain, port = ip_part.rsplit(':', 1)
        else:
            domain = ip_part
            port = "443"
        
        return {
            "domain": domain,
            "port": port,
            "name": name
        }
    except Exception as e:
        print(f"解析失败：{line} - {e}")
        return None


def generate_vless_link(node_info):
    """生成 VLESS 链接"""
    if not node_info:
        return None
    
    domain = node_info["domain"]
    port = node_info["port"]
    name = node_info["name"]
    
    # URL 编码名称
    encoded_name = quote(name, safe='')
    
    # 构建 VLESS 链接
    # address = 优选域名（连接入口），sni/host = Worker 域名（路由到后端）
    vless_link = (
        f"vless://{UUID}@{domain}:{port}?"
        f"encryption={VLESS_PARAMS['encryption']}&"
        f"security={VLESS_PARAMS['security']}&"
        f"sni={WORKER_DOMAIN}&"
        f"fp={VLESS_PARAMS['fp']}&"
        f"insecure={VLESS_PARAMS['insecure']}&"
        f"allowInsecure={VLESS_PARAMS['allowInsecure']}&"
        f"ech={VLESS_PARAMS['ech']}&"
        f"type={VLESS_PARAMS['type']}&"
        f"host={WORKER_DOMAIN}&"
        f"path={VLESS_PARAMS['path']}"
        f"#{encoded_name}"
    )
    
    return vless_link


def generate_subscription():
    """生成订阅文件"""
    # 抓取 IP 列表
    lines = fetch_ip_list()
    if not lines:
        print("没有获取到 IP 列表，跳过生成")
        return False
    
    # 生成 VLESS 链接
    vless_links = []
    for line in lines:
        node_info = parse_ip_line(line)
        if node_info:
            vless_link = generate_vless_link(node_info)
            if vless_link:
                vless_links.append(vless_link)
    
    if not vless_links:
        print("没有生成任何 VLESS 链接")
        return False
    
    # 合并所有链接并进行 base64 编码
    subscription_content = '\n'.join(vless_links)
    encoded_subscription = base64.b64encode(subscription_content.encode('utf-8')).decode('utf-8')
    
    # 保存到文件
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(encoded_subscription)
    
    print(f"[{datetime.now()}] 订阅文件已生成：{OUTPUT_FILE}")
    print(f"共生成 {len(vless_links)} 个节点")
    
    # 同时保存明文版本（方便调试）
    with open(f"{OUTPUT_FILE}.plain", 'w', encoding='utf-8') as f:
        f.write(subscription_content)
    
    return True


def job():
    """定时任务"""
    print("=" * 60)
    print(f"[{datetime.now()}] 开始执行定时任务")
    print("=" * 60)
    generate_subscription()
    print("=" * 60)
    print(f"[{datetime.now()}] 任务完成")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    
    print("CF 订阅生成器启动")
    print(f"数据源：{GITHUB_URL}")
    print(f"输出文件：{OUTPUT_FILE}")
    print("-" * 60)
    
    # 检查是否为单次运行模式（GitHub Actions）
    if "--once" in sys.argv:
        print("单次运行模式（GitHub Actions）")
        job()
    else:
        import schedule
        print("执行频率：每 12 小时一次")
        
        # 立即执行一次
        job()
        
        # 设置定时任务：每 12 小时执行一次
        schedule.every(12).hours.do(job)
        
        print("\n定时任务已启动，按 Ctrl+C 停止")
        print("等待下次执行...")
        
        # 保持运行
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            print("\n程序已停止")
