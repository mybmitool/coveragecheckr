#!/usr/bin/env python3
"""
站群批量修复脚本 V1.0
功能：
1. 检查所有站点的 auto-update.yml 是否包含 site_archive.json 提交
2. 检查 build.py 是否生成/更新 site_archive.json
3. 检查工具 slug 语义化（-calculator 后缀）
4. 自动修复可修复项，报告需手动处理项

使用方法：
  将本脚本放在站群根目录（与所有站点文件夹同级），运行：
  python site_batch_fixer.py
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime

SKIP_DIRS = {'.git', '.github', '__pycache__', 'node_modules', 'venv', '.site_builder'}

def find_site_dirs(root='.'):
    sites = []
    for entry in Path(root).iterdir():
        if entry.is_dir() and entry.name not in SKIP_DIRS:
            if (entry / 'index.html').exists() or (entry / 'site_archive.json').exists():
                sites.append(entry)
    return sorted(sites)

def fix_auto_update_yml(site_dir):
    yml_path = site_dir / '.github' / 'workflows' / 'auto-update.yml'
    if not yml_path.exists():
        return 'MISSING', 'auto-update.yml 不存在'

    content = yml_path.read_text(encoding='utf-8')

    if 'site_archive.json' in content:
        return 'OK', '已包含 site_archive.json'

    original = content
    # 匹配 git add 行
    if 'git add sitemap.xml sitemap.html llms.txt' in content:
        content = content.replace(
            'git add sitemap.xml sitemap.html llms.txt',
            'git add sitemap.xml sitemap.html llms.txt site_archive.json'
        )
    elif 'git add -A' in content or 'git add .' in content:
        return 'OK', '已使用 git add -A 或 git add .'
    else:
        # 在 git diff 前插入
        content = content.replace(
            'git diff --cached --quiet',
            'git add site_archive.json\n          git diff --cached --quiet'
        )

    if content != original:
        yml_path.write_text(content, encoding='utf-8')
        return 'FIXED', '已加入 site_archive.json 到提交列表'

    return 'OK', '无需修复'

def check_build_py(site_dir):
    build_path = site_dir / 'build.py'
    if not build_path.exists():
        return 'MISSING', 'build.py 不存在'

    content = build_path.read_text(encoding='utf-8')

    if 'site_archive.json' in content:
        return 'OK', 'build.py 已包含 site_archive.json 处理逻辑'

    has_sitemap = 'sitemap.xml' in content or 'sitemap.html' in content
    has_llms = 'llms.txt' in content

    if has_sitemap and has_llms:
        return 'WARN', 'build.py 生成 sitemap/llms 但不生成 site_archive.json（建议：在 main() 中加入 site_archive.json 更新）'

    return 'WARN', 'build.py 内容异常，请人工检查'

def check_tool_slugs(site_dir):
    archive_path = site_dir / 'site_archive.json'
    if not archive_path.exists():
        return 'MISSING', 'site_archive.json 不存在'

    try:
        with open(archive_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        return 'ERROR', 'site_archive.json 解析失败'

    tools = data.get('tools', [])
    bad_slugs = []
    good_suffixes = ['-calculator', '-tool', '-tracker', '-guide', '-planner', 
                     '-checker', '-estimator', '-evaluator', '-optimizer', 
                     '-comparator', '-converter', '-analyzer', '-score', '-log', 
                     '-chart', '-timeline', '-budget', '-splitter', '-matcher', 
                     '-index', '-ratio', '-window', '-predictor', '-assessment', 
                     '-generator', '-schedule', '-refi', '-calc']

    for tool in tools:
        slug = tool.get('slug', '')
        if slug and not any(suffix in slug for suffix in good_suffixes):
            bad_slugs.append(slug)

    if bad_slugs:
        return 'WARN', f'以下工具 slug 可能缺少语义化后缀: {bad_slugs}'
    return 'OK', f'所有 {len(tools)} 个工具 slug 已语义化'

def main():
    print("=" * 60)
    print("站群批量检查修复工具 V1.0")
    print("=" * 60)

    site_dirs = find_site_dirs()
    print(f"\n发现 {len(site_dirs)} 个站点目录")
    print("-" * 60)

    report = []
    for site_dir in site_dirs:
        site_name = site_dir.name
        print(f"\n📁 {site_name}")

        status, msg = fix_auto_update_yml(site_dir)
        print(f"   auto-update.yml: [{status}] {msg}")
        report.append({'site': site_name, 'file': 'auto-update.yml', 'status': status, 'msg': msg})

        status, msg = check_build_py(site_dir)
        print(f"   build.py:        [{status}] {msg}")
        report.append({'site': site_name, 'file': 'build.py', 'status': status, 'msg': msg})

        status, msg = check_tool_slugs(site_dir)
        print(f"   tool slugs:      [{status}] {msg}")
        report.append({'site': site_name, 'file': 'tool-slugs', 'status': status, 'msg': msg})

    print("\n" + "=" * 60)
    print("汇总报告")
    print("=" * 60)

    issues = [r for r in report if r['status'] in ('WARN', 'MISSING', 'ERROR')]
    if issues:
        print(f"\n⚠️ 发现 {len(issues)} 个问题需处理：")
        for r in issues:
            print(f"   {r['site']}/{r['file']}: [{r['status']}] {r['msg']}")
    else:
        print("\n✅ 所有站点检查通过，无问题！")

    report_path = Path('site_batch_fix_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n📄 详细报告已保存: {report_path}")

if __name__ == '__main__':
    main()
