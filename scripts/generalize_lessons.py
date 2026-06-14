#!/usr/bin/env python3
"""泛化 lessons/reference — 移除项目特定前缀、标签、硬编码路径.

用法: cd MisakaNet && python3 scripts/generalize_lessons.py

操作:
  1. 清理 frontmatter tags: 移除 project:* / node:* / severity:*
  2. 重命名带项目前缀的 .md 文件
  3. 替换内容中硬编码路径 / 用户名
  4. 更新 lessons/index.md 索引
  5. 更新 reference/ 引用
"""

import os
import re
import json
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent

LESSONS = REPO / "lessons"
CONTRIB = LESSONS / "contrib"
CORE   = LESSONS / "core"
REF    = REPO / "reference"
INDEX  = LESSONS / "index.md"

# ─── 文件重命名映射: (旧名 → 新名) ────────────────────────────────

RENAME_MAP = {
    # --- cc-connect ---
    "cc-connect-feishu-display-optimization.md":
        "feishu-agent-display-settings.md",
    "cc-connect-feishu-setup-complete.md":
        "feishu-bot-setup-complete.md",

    # --- ccswitch / hermes-switch ---
    "ccswitch-hermes-switch.md":
        "model-switch-script-pattern.md",

    # --- codewhale ---
    "codewhale-git-push-yolo-task.md":
        "git-push-without-shell-agent.md",

    # --- deepseek-tui ---
    "deepseek-tui-agent-模式下-write-file-写入不落地-worktree-git-链接路径断裂.md":
        "agent-write-file-sandbox-worktree-path-breakage.md",
    "deepseek-tui-write-file-sandbox-worktree-git-path.md":
        "write-file-sandbox-worktree-git-path.md",

    # --- hermes ---
    "hermes-agent-手动更新步骤-update-超时.md":
        "agent-manual-update-timeout.md",
    "hermes-state-database-lock-issues-cleanup-protocol.md":
        "agent-state-database-lock-cleanup.md",

    # --- node_* (纯节点注册记录, 直接删除) ---
    "node_zsxh1990.md": None,        # 标记删除
    "node_10049.md": None,           # 标记删除
    "node_104.md": None,             # 标记删除
    "node_148.md": None,             # 标记删除
    "node2-配置完成-git-credentials-和-node-id-设置.md":
        "git-credentials-and-node-id-setup.md",

    # --- st2 (特定游戏) ---
    "st2-danielstarman-mcp-选rare-relic会卡死.md":
        "game-mcp-rare-relic-freeze.md",
    "st2-mcp-end-turn返回409但游戏正常推进.md":
        "game-mcp-end-turn-conflict-409.md",
    "st2-mcp从game-over重开必须走特定流程.md":
        "game-mcp-game-over-restart-flow.md",
}

# ─── 需要清理 tags 的 frontmatter 模式 ────────────────────────────

TAG_CLEAN_RE = re.compile(
    r'(?:["\']?(?:project|node):[^"\',\]]+|'
    r'["\']?severity:(?:critical|high|medium|low)["\']?)'
)

# ─── 内容中硬编码替换 ─────────────────────────────────────────────

CONTENT_REPLACE = [
    # 用户路径
    (r'/mnt/c/Users/hp/', '<your-project-path>/'),
    # 特定用户名出现在内容中
    (r'\bzsxh1990\b', '<user>'),
    (r'\bcc_haha\b', '<agent>'),
    (r'\bdanielstarman\b', '<user>'),
    # 特定项目名（非文件名引用）
    (r'\bAgent-Medici\b', '<project-name>'),
    (r'\bself-grow-wiki\b', '<project-name>'),
    (r'\bHermes-Agent\b', '<agent-framework>'),
]

# ─── 文件中的旧内容替换（每个文件的特定替换） ─────────────────────

FILE_CONTENT_FIXES = {
    # cc-connect 内容 → 泛化
    "cc-connect-feishu-display-optimization.md": [
        (r'cc-connect', '<your-agent>'),
        (r'~/.cc-connect/config\.toml', '<config-file>'),
        (r'cc-connect stop --force && cc-connect', '<agent-restart-command>'),
        (r'cc-connect logs --force', '<agent-logs-command>'),
    ],
    # ccswitch 内容
    "ccswitch-hermes-switch.md": [
        (r'ccswitch|hermes-switch', '<model-switch-script>'),
        (r'~/.claude/settings\.json', '<agent-config-file>'),
        (r'~/ccswitch', '<script-path>'),
        (r'ccswitch list', '<script> list'),
        (r'ccswitch status', '<script> status'),
        (r'ccswitch ds-flash', '<script> set-model'),
    ],
}


# ═══════════════════════════════════════════════════════════════════
#  实现
# ═══════════════════════════════════════════════════════════════════

def read_file(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def write_file(p: Path, content: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def clean_tags(frontmatter: str) -> str:
    """清理 JSON frontmatter 中的 project:/node:/severity: 标签"""
    def _clean_line(m: re.Match) -> str:
        return ""

    result = TAG_CLEAN_RE.sub("", frontmatter)
    # 清理残留的空引号、空标签数组元素
    result = re.sub(r',\s*,\s*', ", ", result)
    result = re.sub(r'\{\s*\}', "{}", result)
    result = re.sub(r'"\s*"\s*,\s*', "", result)
    result = re.sub(r',\s*"\s*"', "", result)
    result = re.sub(r'\[\s*\]', "[]", result)
    return result


def fix_json_frontmatter(content: str) -> str:
    """解析 ---...--- 中的 JSON frontmatter 并清理 tags"""
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not m:
        return content

    raw = m.group(1)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # 尝试清理后重试
        cleaned = clean_tags(raw)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            return content

    changed = False
    for key in ("tags",):
        if key not in data:
            continue
        tags = data[key]
        if isinstance(tags, list):
            new_tags = [t for t in tags
                        if not re.match(r'project:|node:|severity:', t)]
            if len(new_tags) != len(tags):
                data[key] = new_tags
                changed = True
        elif isinstance(tags, str):
            parts = [t.strip().strip('"') for t in tags.split(",")]
            new_parts = [t for t in parts
                         if t and not re.match(r'project:|node:|severity:', t)]
            if len(new_parts) != len(parts):
                data[key] = ", ".join(new_parts)
                changed = True

    if not changed:
        return content

    new_raw = json.dumps(data, ensure_ascii=False)
    return content[:m.start(1)] + new_raw + content[m.end(1):]


def apply_content_replacements(content: str, old_name: str) -> str:
    """对内容做硬编码替换"""
    # 通用替换
    for pattern, replacement in CONTENT_REPLACE:
        content = re.sub(pattern, replacement, content)

    # 文件特定替换
    fixes = FILE_CONTENT_FIXES.get(old_name, [])
    for pattern, replacement in fixes:
        content = re.sub(pattern, replacement, content)

    return content


def process_file(old_path: Path, new_name: Optional[str] = None) -> None:
    """处理单个文件: 清理 tags, 替换内容, 可选重命名"""
    old_name_str = old_path.name
    content = read_file(old_path)

    # 1. 清理 frontmatter tags
    content = fix_json_frontmatter(content)

    # 2. 替换硬编码内容
    content = apply_content_replacements(content, old_name_str)

    # 3. 如果重命名 → 写新文件 (旧文件后续 git rm)
    if new_name and new_name != old_name_str:
        new_path = old_path.parent / new_name
        write_file(new_path, content)
        print(f"  🔄 {old_name_str} → {new_name}")
    else:
        write_file(old_path, content)
        print(f"  ✏️  {old_name_str} (内容已替换)")


def update_index() -> None:
    """更新 index.md 中的文件链接"""
    if not INDEX.exists():
        return

    content = read_file(INDEX)

    # 替换链接中的旧文件名
    for old_name, new_name in RENAME_MAP.items():
        if old_name == new_name:
            continue
        content = content.replace(old_name, new_name)

    # 清理 index 中的 project:/node:/severity: 标签
    content = TAG_CLEAN_RE.sub("", content)
    content = re.sub(r'\s*,\s*,', ',', content)
    content = re.sub(r',\s*\)', ')', content)

    write_file(INDEX, content)
    print("  📝 index.md 已更新")


def update_reference_refs() -> None:
    """更新 reference/ 中引用的旧 lesson 文件名"""
    for ref_file in REF.glob("*.md"):
        content = read_file(ref_file)
        orig = content
        for old_name, new_name in RENAME_MAP.items():
            content = content.replace(old_name, new_name)
        if content != orig:
            write_file(ref_file, content)
            print(f"  🔗 reference/{ref_file.name} 引用已更新")


def main():
    print("=" * 60)
    print("MisakaNet Lesson 泛化工具")
    print("=" * 60)

    # ─── Phase 1: 清理 frontmatter tags ───
    print("\n[阶段 1/4] 清理 frontmatter 标签...")
    tag_count = 0
    for f in sorted(CONTRIB.glob("*.md")):
        content = read_file(f)
        cleaned = fix_json_frontmatter(content)
        if cleaned != content:
            write_file(f, cleaned)
            tag_count += 1
    print(f"  已清理 {tag_count} 个文件的 tags")

    # ─── Phase 2: 重命名/删除文件 ───
    print("\n[阶段 2/4] 重命名/删除项目特定文件...")
    rename_count = 0
    delete_list = []
    for old_name, new_name in RENAME_MAP.items():
        old_path = CONTRIB / old_name
        if not old_path.exists():
            old_path = LESSONS / old_name
        if not old_path.exists():
            print(f"  ⚠️  未找到: {old_name}")
            continue

        # None = 标记删除
        if new_name is None:
            delete_list.append(old_path)
            print(f"  🗑️  {old_name} (标记删除)")
            continue

        # 读内容, 清理, 写新文件
        content = read_file(old_path)
        content = fix_json_frontmatter(content)
        content = apply_content_replacements(content, old_name)

        new_path: Optional[Path] = None
        if new_name.startswith("_archive/"):
            new_path = LESSONS / new_name
        else:
            new_path = CONTRIB / new_name
        new_path.parent.mkdir(parents=True, exist_ok=True)
        write_file(new_path, content)
        rename_count += 1
        # 旧文件保留, 提示用户 git rm
        print(f"  🔄 {old_name} → {new_path.relative_to(REPO)}")
        print(f"     (旧文件需手动: git rm {old_path.relative_to(REPO)})")
    print(f"  已重命名 {rename_count} 个文件")

    # ─── Phase 3: 替换内容中的硬编码 ───
    print("\n[阶段 3/4] 替换硬编码路径/用户名...")
    content_fix_count = 0
    for f in sorted(CONTRIB.glob("*.md")):
        content = read_file(f)
        orig = content
        content = apply_content_replacements(content, f.name)
        if content != orig:
            write_file(f, content)
            content_fix_count += 1
    print(f"  已替换 {content_fix_count} 个文件的内容")

    # ─── Phase 4: 更新 index 和 reference ───
    print("\n[阶段 4/4] 更新索引和引用...")
    update_index()
    update_reference_refs()

    # ─── 遗留操作提示 ───
    print("\n" + "=" * 60)
    print("泛化完成! 下一步:")
    print("=" * 60)
    print()
    print("1. 查看变更:")
    print("   git status")
    print()
    print("2. 删除旧文件 + 标记删除的文件:")
    # 重命名产生的旧文件
    for old_name, new_name in RENAME_MAP.items():
        if old_name == new_name or new_name is None:
            continue
        for d in (CONTRIB, LESSONS):
            p = d / old_name
            if p.exists():
                print(f"   git rm {p.relative_to(REPO)}")
    # None = 直接删除
    for old_name, new_name in RENAME_MAP.items():
        if new_name is not None:
            continue
        for d in (CONTRIB, LESSONS):
            p = d / old_name
            if p.exists():
                print(f"   git rm {p.relative_to(REPO)}  # 节点注册记录，直接删除")
    print()
    print("3. 提交 + 推送:")
    print("   git add -A")
    print('   git commit -m "refactor: generalize lessons - remove project-specific naming, paths, and tags"')
    print("   git push")
    print()

    # 统计
    contrib_count = len(list(CONTRIB.glob("*.md")))
    archive_count = len(list((LESSONS / "_archive").glob("*.md")))
    ref_count = len(list(REF.glob("*.md")))
    print(f"  当前统计: contrib/ {contrib_count} 篇, _archive/ {archive_count} 篇, reference/ {ref_count} 篇")


if __name__ == "__main__":
    main()
