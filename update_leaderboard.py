"""每天北京时间 15:00 拉取 Table30 V2 前 10 名，更新中英文 README。"""

import json
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen

BASE_DIR = Path(__file__).resolve().parent
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
    req = Request(url, headers={"User-Agent": "RoboChallengeLeaderboardBot/1.0"})
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


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
        sr_pct = f"{row['success_ratio'] * 100:.1f}"
        lines.append(f"| {medal} | {model} | {user} | {score} | {sr_pct} |")

    return "\n".join(lines)


def build_full_section(rows: list, updated_at: str, lang: str) -> str:
    table = build_table(rows, lang)
    if lang == "zh":
        timestamp = f"> 榜单数据更新时间: **{updated_at}**"
        more_hint = f"_仅展示前 {TOP_N} 名，[查看完整榜单](https://robochallenge.cn/home)。_"
    else:
        timestamp = f"> Leaderboard data updated: **{updated_at}**"
        more_hint = f"_Showing the top {TOP_N} only. [View the full leaderboard](https://robochallenge.cn/home)._"
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
    print("📡 拉取 Table30 V2 榜单 …", flush=True)
    rows = extract_rows(fetch_json(LEADERBOARD_URL))
    print(f"共 {len(rows)} 条，展示前 {TOP_N} 名")
    updated_at = datetime.now(UTC_PLUS_8).strftime("%Y-%m-%d %H:%M UTC+8")
    for target in README_TARGETS:
        section = build_full_section(rows, updated_at, target["lang"])
        update_readme(section, target["path"])


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"❌ 榜单更新失败: {exc}", file=sys.stderr)
        sys.exit(1)
