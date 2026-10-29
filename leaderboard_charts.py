"""使用标准库生成适合 GitHub README 的轻量 SVG 和可核对的 CSV。"""

import csv
import io
import json
import math
from html import escape

from table30_v2 import CAPABILITIES, CHART_TOP_N, TASKS

THEMES = {
    "light": {"surface": "#fcfcfb", "ink": "#0b0b0b", "muted": "#52514e", "grid": "#e1e0d9", "accent": "#2a78d6", "missing": "#e1e0d9"},
    "dark": {"surface": "#1a1a19", "ink": "#f0efec", "muted": "#c3c2b7", "grid": "#383835", "accent": "#3987e5", "missing": "#383835"},
}
# 成功率使用单一蓝色的亮度渐变，不以颜色区分模型身份。
RAMP = ("#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b")


def validate_metadata(raw) -> dict:
    if not isinstance(raw, list):
        raise ValueError("V2 任务元数据必须为列表")
    benchmarks = [item for item in raw if isinstance(item, dict) and item.get("benchmark_id") == "table30v2"]
    if len(benchmarks) != 1 or not isinstance(benchmarks[0].get("tasks"), list):
        raise ValueError("未找到唯一的 Table30 V2 任务元数据")
    entries = benchmarks[0]["tasks"]
    if not all(isinstance(item, dict) and isinstance(item.get("task_name"), str) for item in entries):
        raise ValueError("V2 任务元数据记录格式无效")
    by_name = {item["task_name"]: item for item in entries}
    if len(entries) != len(TASKS) or len(by_name) != len(TASKS) or set(by_name) != {task.name for task in TASKS}:
        raise ValueError("官方 V2 任务集合发生变化，请核对任务 ID 映射")
    tags = {}
    for task in TASKS:
        values = by_name[task.name].get("task_tag")
        if not isinstance(values, list) or not values or not all(isinstance(value, str) for value in values):
            raise ValueError(f"任务 {task.name} 缺少有效能力标签")
        tags[task.id] = values
    for tag, _, _ in CAPABILITIES:
        if sum(tag in values for values in tags.values()) < 3:
            raise ValueError(f"能力维度 {tag} 覆盖不足三个任务，请重新核对")
    return tags


def model_tasks(row: dict) -> dict:
    results = row.get("task_results")
    if not isinstance(results, list) or not results:
        raise ValueError(f"模型 {row['display_name']} 缺少任务成绩")
    known = {task.id for task in TASKS}
    by_id = {}
    for result in results:
        if not isinstance(result, dict) or result.get("task_id") not in known:
            raise ValueError("任务成绩包含未知 V2 任务 ID")
        task_id = result["task_id"]
        if task_id in by_id:
            raise ValueError(f"模型任务成绩重复: {task_id}")
        value = result.get("success_ratio")
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError(f"任务 {task_id} 成功率不是有效的 0–1 数值")
        by_id[task_id] = value * 100
    return by_id


def capability_values(results: dict, tags: dict) -> list:
    return [
        sum(results.get(task.id, 0) for task in TASKS if tag in tags[task.id])
        / sum(tag in values for values in tags.values())
        for tag, _, _ in CAPABILITIES
    ]


def text(x, y, value, *, size=14, anchor="start", css="", weight=400) -> str:
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" text-anchor="{anchor}" '
            f'font-weight="{weight}" class="{css}">{escape(str(value))}</text>')


def svg_start(width: int, height: int, title: str, description: str, theme: dict) -> list:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>',
        '<style>text{font-family:system-ui,-apple-system,"Segoe UI","Noto Sans CJK SC",sans-serif;'
        f'fill:{theme["ink"]}' + '} .muted{fill:' + theme["muted"] + '} .inverse{fill:#fcfcfb}</style>',
        f'<rect width="100%" height="100%" rx="12" fill="{theme["surface"]}"/>',
    ]


def point(cx, cy, radius, index, count=6):
    angle = -math.pi / 2 + index * 2 * math.pi / count
    return cx + radius * math.cos(angle), cy + radius * math.sin(angle)


def polygon_points(points):
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in points)


def radar_svg(rows: list, tags: dict, lang: str, mode: str) -> str:
    theme = THEMES[mode]
    models = rows[:CHART_TOP_N]
    width, height = 240 * len(models), 355
    title = "Top models · capability success rate" if lang == "en" else "领先模型 · 能力成功率"
    desc = "Six selected official capability tags; task mean success rate; missing tasks count as zero; identical 0–100% axes."
    parts = svg_start(width, height, title, desc, theme)
    for index, row in enumerate(models):
        cx, cy, radius = index * 240 + 120, 178, 66
        name = str(row["display_name"])
        short_name = name if len(name) <= 22 else name[:21] + "…"
        parts.append(f'<g><title>{escape(name)} · {escape(str(row["user_name"]))}</title>')
        parts.append(text(cx, 30, f"#{row.get('rank', index + 1)}  {short_name}", size=18, anchor="middle", weight=650))
        user = str(row["user_name"])
        parts.append(text(cx, 52, user if len(user) <= 27 else user[:26] + "…", size=12, anchor="middle", css="muted"))
        for level in (25, 50, 75, 100):
            points = [point(cx, cy, radius * level / 100, i) for i in range(6)]
            parts.append(f'<polygon points="{polygon_points(points)}" fill="none" stroke="{theme["grid"]}" stroke-width="1"/>')
        for i, (tag, en, zh) in enumerate(CAPABILITIES):
            x, y = point(cx, cy, radius, i)
            parts.append(f'<path d="M {cx} {cy} L {x:.2f} {y:.2f}" stroke="{theme["grid"]}" fill="none"/>')
            x, y = point(cx, cy, radius + 25, i)
            # 标签居中放在每个面板内，避免相邻面板的长英文词重叠。
            if i not in (0, 3):
                x = cx + 78 * (1 if i < 3 else -1)
            parts.append(text(x, y + 5, en if lang == "en" else zh, size=11, anchor="middle", css="muted"))
        for level in (50, 100):
            parts.append(text(cx + 4, cy - radius * level / 100 + 4, level, size=9, css="muted"))
        results = model_tasks(row)
        values = capability_values(results, tags)
        points = [point(cx, cy, radius * value / 100, i) for i, value in enumerate(values)]
        parts.append(f'<polygon points="{polygon_points(points)}" fill="{theme["accent"]}" fill-opacity="0.10" stroke="{theme["accent"]}" stroke-width="2" stroke-linejoin="round"/>')
        for i, ((x, y), value) in enumerate(zip(points, values)):
            label = CAPABILITIES[i][1 if lang == "en" else 2]
            parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="{theme["accent"]}" stroke="{theme["surface"]}" stroke-width="2"><title>{escape(label)}: {value:.1f}%</title></circle>')
        overall = f"SR {row['success_ratio'] * 100:.1f}%"
        parts.append(text(cx, 300, overall, anchor="middle", size=15, weight=600))
        coverage = f"{len(results)}/30 tasks" if lang == "en" else f"已评测 {len(results)}/30 项"
        parts.append(text(cx, 321, coverage, anchor="middle", size=12, css="muted"))
        parts.append('</g>')
    footer = "Same axes · 0–100% · missing tasks = 0" if lang == "en" else "统一量程 0–100% · 未评测任务计 0"
    parts.append(text(width / 2, 345, footer, size=12, anchor="middle", css="muted"))
    return "\n".join(parts + ['</svg>']) + "\n"


def heat_color(value: float, mode: str) -> str:
    ramp = RAMP if mode == "light" else tuple(reversed(RAMP))
    position = value / 100 * (len(ramp) - 1)
    index = min(int(position), len(ramp) - 2)
    fraction = position - index
    a, b = ramp[index], ramp[index + 1]
    channels = [round(int(a[i:i + 2], 16) * (1 - fraction) + int(b[i:i + 2], 16) * fraction) for i in (1, 3, 5)]
    return "#" + "".join(f"{channel:02x}" for channel in channels)


def readable_ink(background: str) -> str:
    channels = [int(background[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
    luminance = sum(weight * value for weight, value in zip((0.2126, 0.7152, 0.0722), linear))
    return "#000000" if luminance > 0.179 else "#ffffff"


def heatmap_svg(rows: list, lang: str, mode: str) -> str:
    theme = THEMES[mode]
    models = rows[:CHART_TOP_N]
    left, top, cell_w, cell_h = 270, 139, 108, 27
    width, height = left + len(models) * cell_w + 25, top + len(TASKS) * cell_h + 93
    title = "Task success rate" if lang == "en" else "任务成功率"
    parts = svg_start(width, height, title, "30 official V2 tasks by top-ranked models. Dash indicates no reported evaluation; zero is an evaluated task with no successes.", theme)
    parts.append(text(24, 35, title, size=23, weight=650))
    subtitle = "Official rank order · per-task SR (%)" if lang == "en" else "按官方榜单排名 · 单任务成功率 (%)"
    parts.append(text(24, 60, subtitle, size=13, css="muted"))
    for col, row in enumerate(models):
        x = left + (col + 0.5) * cell_w
        name = str(row['display_name'])
        parts.append(f'<g><title>{escape(name)} · {escape(str(row["user_name"]))}</title>')
        parts.append(text(x, 96, f"#{row.get('rank', col + 1)}", size=11, anchor="middle", css="muted"))
        parts.append(text(x, 118, name if len(name) <= 14 else name[:13] + "…", size=12, anchor="middle", weight=600))
        parts.append('</g>')
    task_maps = [model_tasks(row) for row in models]
    previous_robot = None
    for row_index, task in enumerate(TASKS):
        y = top + row_index * cell_h
        if task.robot != previous_robot:
            parts.append(f'<path d="M 24 {y - 2} H {width - 25}" stroke="{theme["grid"]}"/>')
            previous_robot = task.robot
        label = task.en if lang == "en" else task.zh
        parts.append(text(24, y + 18, f"{task.robot}  /  {label}", size=12))
        for col, results in enumerate(task_maps):
            x = left + col * cell_w
            value = results.get(task.id)
            color = theme["missing"] if value is None else heat_color(value, mode)
            parts.append(f'<g><title>{escape(task.name)} · {escape(str(models[col]["display_name"]))}: {"not evaluated" if value is None else f"{value:.1f}%"}</title>')
            parts.append(f'<rect x="{x + 1}" y="{y + 1}" width="{cell_w - 2}" height="{cell_h - 2}" rx="3" fill="{color}"/>')
            label = "—" if value is None else f"{value:.0f}"
            parts.append(f'<text x="{x + cell_w / 2}" y="{y + 18}" font-size="12" text-anchor="middle" style="fill:{readable_ink(color)}">{label}</text></g>')
    legend_y = top + len(TASKS) * cell_h + 25
    parts.append(text(24, legend_y + 12, "SR (%)", size=12, weight=600))
    for index in range(100):
        parts.append(f'<rect x="{100 + index * 2}" y="{legend_y}" width="2.1" height="12" fill="{heat_color(index * 100 / 99, mode)}"/>')
    parts.append(text(100, legend_y + 29, "0", size=10, css="muted"))
    parts.append(text(300, legend_y + 29, "100", size=10, anchor="end", css="muted"))
    missing = "— Not evaluated" if lang == "en" else "— 未评测"
    parts.append(text(345, legend_y + 12, missing, size=12, css="muted"))
    return "\n".join(parts + ['</svg>']) + "\n"


def csv_text(rows: list) -> str:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    # 防止来自官方模型名的内容被电子表格解释为公式。
    writer.writerows([["'" + str(value) if isinstance(value, str) and value.startswith(("=", "+", "-", "@")) else value for value in row] for row in rows])
    return stream.getvalue()


def generate_assets(rows: list, tags: dict) -> dict:
    models = rows[:CHART_TOP_N]
    for row in models:
        model_tasks(row)
    files = {}
    for lang in ("en", "zh"):
        for mode in ("light", "dark"):
            suffix = "" if mode == "light" else "-dark"
            files[f"assets/table30-v2-capabilities-{lang}{suffix}.svg"] = radar_svg(models, tags, lang, mode)
            files[f"assets/table30-v2-tasks-{lang}{suffix}.svg"] = heatmap_svg(models, lang, mode)
    capability_rows = [["rank", "model", "user", *[tag for tag, _, _ in CAPABILITIES]]]
    task_rows = [["rank", "model", "user", "task_id", "task_name", "robot", "success_rate_percent"]]
    for i, row in enumerate(models, 1):
        prefix = [row.get("rank", i), row["display_name"], row["user_name"]]
        results = model_tasks(row)
        capability_rows.append(prefix + [f"{value:.4f}" for value in capability_values(results, tags)])
        for task in TASKS:
            value = results.get(task.id)
            task_rows.append(prefix + [task.id, task.name, task.robot, "" if value is None else f"{value:.4f}"])
    files["data/table30-v2-capabilities.csv"] = csv_text(capability_rows)
    files["data/table30-v2-tasks.csv"] = csv_text(task_rows)
    files["data/table30-v2-task-tags.json"] = json.dumps(
        [{"task_id": task.id, "task_name": task.name, "robot": task.robot, "task_tag": tags[task.id]} for task in TASKS],
        ensure_ascii=False, indent=2,
    ) + "\n"
    return files
