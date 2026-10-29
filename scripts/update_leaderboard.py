"""每天北京时间 15:00 同步 Table30 V2 榜单、前五名图表及中英文 README。"""

import json
import math
import ssl
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from leaderboard_charts import generate_assets, validate_task_tags
from table30_v2 import CHART_TOP_N

BASE_DIR = Path(__file__).resolve().parent.parent
README_TARGETS = [
    {"path": "README.zh-CN.md", "lang": "zh"},
    {"path": "README.md", "lang": "en"},
]

UTC_PLUS_8 = timezone(timedelta(hours=8))
SECTION_START = "<!-- LEADERBOARD_START -->"
SECTION_END = "<!-- LEADERBOARD_END -->"
LEADERBOARD_URL = "https://robochallenge.cn/api/v2/leaderboard/leaderboard_table30_v2.json"
TOP_N = 10
MEDAL = {1: "🥇", 2: "🥈", 3: "🥉"}


def fetch_json(url: str):
    """保留证书校验；兼容官方 CDN 在部分 CI 节点的 TLS 握手差异。"""
    errors = []
    # CDN 的 www 节点曾返回数周前的缓存；主备地址使用同一个唯一查询参数。
    fresh_url = f"{url}{'&' if '?' in url else '?'}_refresh={time.time_ns()}"
    for candidate in (fresh_url, fresh_url.replace("https://robochallenge.cn/", "https://www.robochallenge.cn/")):
        req = Request(candidate, headers={"User-Agent": "RoboChallengeLeaderboardBot/1.0", "Cache-Control": "no-cache"})
        for tls12 in (False, True):
            context = ssl.create_default_context()
            if tls12:
                context.minimum_version = ssl.TLSVersion.TLSv1_2
                context.maximum_version = ssl.TLSVersion.TLSv1_2
            try:
                with urlopen(req, timeout=20, context=context) as resp:
                    return json.loads(resp.read())
            except (URLError, OSError) as exc:
                errors.append(str(exc))
        try:
            # 系统 curl 使用独立的 TLS 实现；不使用 -k 或关闭证书验证。
            result = subprocess.run(
                ["curl", "--fail", "--silent", "--show-error", "--location", "--retry", "2",
                 "--connect-timeout", "10", "--max-time", "30", "--header", "Cache-Control: no-cache",
                 "--user-agent", "RoboChallengeLeaderboardBot/1.0", candidate],
                check=True, capture_output=True, timeout=100,
            )
            return json.loads(result.stdout)
        except (OSError, subprocess.SubprocessError) as exc:
            errors.append(str(exc))
    raise OSError("官方接口 HTTPS 请求失败: " + "; ".join(errors))


def extract_rows(raw) -> list:
    """兼容列表和 leaderboard_all 包装；异常或空数据不覆盖已有榜单。"""
    rows = raw.get("leaderboard_all") if isinstance(raw, dict) else raw
    if not isinstance(rows, list) or not rows:
        raise ValueError("Table30 V2 接口未返回有效的榜单列表")
    for row in rows:
        if not isinstance(row, dict) or not {"display_name", "user_name", "score", "success_ratio"} <= row.keys():
            raise ValueError("Table30 V2 榜单记录缺少必要字段")
        for key in ("score", "success_ratio"):
            value = row[key]
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError(f"Table30 V2 榜单字段 {key} 不是有效数值")
        if not 0 <= row["success_ratio"] <= 1:
            raise ValueError("Table30 V2 榜单成功率超出 0–1 范围")
    return rows


def markdown_cell(value) -> str:
    text = str(value if value is not None else "-")
    return " ".join(text.splitlines()).replace("|", "\\|")


def build_table(rows: list, lang: str, top_n: int = TOP_N) -> str:
    """沿用官方接口的排名顺序，仅展示前 top_n 名。"""
    if lang == "zh":
        lines = [
            "| 排名 | 模型 | 用户 | 分数 | 成功率 (%) |",
            "|:----:|------|------|-----:|-----------:|",
        ]
    else:
        lines = [
            "| Rank | Model | User | Score | SR (%) |",
            "|:----:|-------|------|------:|-------:|",
        ]

    for i, row in enumerate(rows[:top_n], 1):
        rank = row.get("rank") or i
        medal = MEDAL.get(rank, str(rank))
        model = markdown_cell(row["display_name"])
        user = markdown_cell(row["user_name"])
        score = f"{row['score']:.2f}"
        sr_pct = f"{row['success_ratio'] * 100:.2f}"
        lines.append(f"| {medal} | {model} | {user} | {score} | {sr_pct} |")

    return "\n".join(lines)


def build_full_section(rows: list, updated_at: str, lang: str) -> str:
    table = build_table(rows, lang)
    if lang == "zh":
        timestamp = f"> 榜单数据更新时间: **{updated_at}**"
        more_hint = f"_仅展示前 {TOP_N} 名，[查看完整榜单](https://robochallenge.cn/leaderboard)。_"
    else:
        timestamp = f"> Leaderboard data updated: **{updated_at}**"
        more_hint = f"_Showing the top {TOP_N} only. [View the full leaderboard](https://robochallenge.cn/leaderboard)._"
    return f"{timestamp}\n\n### RoboChallenge Table30 V2\n\n{table}\n\n{more_hint}\n"


def update_readme(section_body: str, readme_path: str) -> None:
    path = BASE_DIR / readme_path
    content = path.read_text(encoding="utf-8")
    start_idx = content.find(SECTION_START)
    end_idx = content.find(SECTION_END)
    if content.count(SECTION_START) != 1 or content.count(SECTION_END) != 1 or end_idx < start_idx:
        raise RuntimeError(f"{readme_path} 缺少唯一且有序的榜单区域标记")

    current_body = content[start_idx + len(SECTION_START):end_idx].strip()
    # 仅更新时间变化时保留原内容，避免定时任务产生无数据变化的提交。
    if current_body.partition("\n")[2] == section_body.strip().partition("\n")[2]:
        print(f"⏭️ {readme_path} 榜单无变化")
        return

    new_block = f"{SECTION_START}\n{section_body}\n{SECTION_END}"
    updated = content[:start_idx] + new_block + content[end_idx + len(SECTION_END):]
    path.write_text(updated, encoding="utf-8")
    print(f"✅ {readme_path} 已更新")


def main():
    tags = validate_task_tags(json.loads((BASE_DIR / "data/table30-v2-task-tags.json").read_text(encoding="utf-8")))
    print("📡 拉取 Table30 V2 榜单，使用本地固定任务标签 …", flush=True)
    rows = extract_rows(fetch_json(LEADERBOARD_URL))
    # 先完成验证和全部渲染，失败时保留已有榜单及图片。
    assets = generate_assets(rows, tags)
    print(f"共 {len(rows)} 条，榜单展示前 {TOP_N} 名；图表展示前 {CHART_TOP_N} 名")
    updated_at = datetime.now(UTC_PLUS_8).strftime("%Y-%m-%d %H:%M UTC+8")
    for target in README_TARGETS:
        section = build_full_section(rows, updated_at, target["lang"])
        update_readme(section, target["path"])
    for relative, content in assets.items():
        path = BASE_DIR / relative
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            print(f"✅ {relative} 已更新")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"❌ 榜单更新失败: {exc}", file=sys.stderr)
        sys.exit(1)
