#!/usr/bin/env python3
"""
每日 AI 资讯 Markdown 报告生成脚本
- 读取 data/latest-24h.json
- 生成前 50 条新闻的 MD 报告
- 保存到 reports/ 目录，按日期命名
- 自动 git commit 并 push
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

# 配置
BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "data" / "latest-24h.json"
REPORTS_DIR = BASE_DIR / "reports"
TOP_N = 50

def load_data():
    """加载最新 24 小时数据"""
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_markdown(data, date_str):
    """生成 Markdown 报告"""
    items = data.get('items', [])[:TOP_N]
    generated_at = data.get('generated_at', '')
    total_items = data.get('total_items', 0)
    
    # 解析生成时间
    try:
        gen_dt = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
        gen_time_cn = gen_dt.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    except:
        gen_time_cn = generated_at
    
    md_lines = [
        f"# AI 资讯日报 - {date_str}",
        "",
        f"> 生成时间：{gen_time_cn} | 数据窗口：24 小时 | 总条目：{total_items}",
        "",
        "---",
        "",
    ]
    
    for i, item in enumerate(items, 1):
        title = item.get('title_zh') or item.get('title') or '无标题'
        url = item.get('url', '#')
        site = item.get('site_name', '未知来源')
        published = item.get('published_at', '')[:10] if item.get('published_at') else ''
        
        md_lines.append(f"## {i}. {title}")
        md_lines.append("")
        md_lines.append(f"- 📰 来源：{site}")
        md_lines.append(f"- 📅 发布：{published}")
        md_lines.append(f"- 🔗 链接：[{url}]({url})")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")
    
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")
    md_lines.append("*本报告由 AI News Radar 自动生成*")
    md_lines.append("")
    
    return '\n'.join(md_lines)

def save_report(content, date_str):
    """保存报告文件"""
    REPORTS_DIR.mkdir(exist_ok=True)
    filename = f"{date_str}.md"
    filepath = REPORTS_DIR / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath

def ensure_git_identity():
    """确保 Git 用户信息已配置，优先使用环境变量，否则设置为默认机器人身份"""
    import subprocess

    name = (
        os.environ.get("GIT_AUTHOR_NAME")
        or os.environ.get("GIT_COMMITTER_NAME")
    )
    email = (
        os.environ.get("GIT_AUTHOR_EMAIL")
        or os.environ.get("GIT_COMMITTER_EMAIL")
    )

    def get_config(key):
        result = subprocess.run(
            ["git", "config", "--get", key],
            cwd=BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        return result.stdout.strip()

    name = name or get_config("user.name")
    email = email or get_config("user.email")

    if name and email:
        return

    if os.environ.get("GITHUB_ACTIONS") == "true":
        name = name or "github-actions[bot]"
        email = email or "41898282+github-actions[bot]@users.noreply.github.com"
    else:
        name = name or "ai-news-radar-bot"
        email = email or "ai-news-radar-bot@example.com"

    subprocess.run(["git", "config", "user.name", name], cwd=BASE_DIR, check=True)
    subprocess.run(["git", "config", "user.email", email], cwd=BASE_DIR, check=True)

def git_commit_push(date_str):
    """Git commit 并 push"""
    import subprocess

    ensure_git_identity()
    
    # 检查是否有变化
    result = subprocess.run(
        ['git', 'status', '--porcelain', 'reports/'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, cwd=BASE_DIR
    )
    
    if not result.stdout.strip():
        print("没有新的更改需要提交")
        return False
    
    # Add
    subprocess.run(['git', 'add', 'reports/'], cwd=BASE_DIR, check=True)
    
    # Commit
    subprocess.run(
        ['git', 'commit', '-m', f'chore: 添加 AI 资讯日报 {date_str}'],
        cwd=BASE_DIR, check=True
    )
    
    # Pull first (rebase to keep history clean)
    subprocess.run(
        ['git', 'pull', '--rebase', 'origin', 'master'],
        cwd=BASE_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
    )
    
    # Push
    subprocess.run(['git', 'push', 'origin', 'master'], cwd=BASE_DIR, check=True)
    
    print(f"✅ 已提交并推送：{date_str}.md")
    return True

def main():
    # 使用当前日期（Asia/Shanghai）
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    print(f"📰 生成 AI 资讯日报：{date_str}")
    
    # 加载数据
    data = load_data()
    print(f"✅ 加载数据完成，共 {data.get('total_items', 0)} 条")
    
    # 生成报告
    content = generate_markdown(data, date_str)
    
    # 保存文件
    filepath = save_report(content, date_str)
    print(f"✅ 报告已保存：{filepath}")
    
    # Git commit & push
    git_commit_push(date_str)
    
    print("🎉 完成！")

if __name__ == '__main__':
    main()
