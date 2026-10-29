import json
import statistics
from collections import defaultdict
import pandas as pd
from openpyxl.styles import Font, Border, Side, Alignment, PatternFill
import matplotlib.pyplot as plt
from math import pi

# --- 绘图字体配置 ---
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'PingFang SC', 'Arial Unicode MS', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# --- 任务元数据字典 ---
task_map = {
    "2343": {
        "task_name": "pour_fries_into_plate",
        "task_tag": ["bimanual", "two-arm", "ALOHA", "precise3d"]
    },
    "2345": {
        "task_name": "stack_bowls",
        "task_tag": ["bimanual", "two-arm", "ALOHA", "repeated", "classification"]
    },
    "233z": {
        "task_name": "make_vegetarian_sandwich",
        "task_tag": ["bimanual", "two-arm", "ALOHA", "precise3d"]
    },
    "233y": {
        "task_name": "clean_dining_table",
        "task_tag": ["repeated", "two-arm", "ALOHA", "classification"]
    },
    "22xr": {
        "task_name": "place_shoes_on_rack",
        "task_tag": ["simple-pick", "single-arm", "ARX5"]
    },
    "238j": {
        "task_name": "put_pen_into_pencil_case",
        "task_tag": ["manipulation", "two-arm", "ALOHA", "bimanual"]
    },
    "238r": {
        "task_name": "stick_tape_to_box",
        "task_tag": ["bimanual", "two-arm", "ALOHA", "manipulation", "multiview"]
    },
    "2396": {
        "task_name": "scan_QR_code",
        "task_tag": ["bimanual", "two-arm", "ALOHA", "temporal"]
    },
    "233i": {
        "task_name": "arrange_paper_cups",
        "task_tag": ["repeated", "single-arm", "ARX5", "precise3d"]
    },
    "238w": {
        "task_name": "open_the_drawer",
        "task_tag": ["precise3d", "single-arm", "ARX5", "manipulation"]
    },
    "238s": {
        "task_name": "put_cup_on_coaster",
        "task_tag": ["simple-pick", "single-arm", "ARX5"]
    },
    "22v9": {
        "task_name": "arrange_flowers",
        "task_tag": ["repeated", "single-arm", "ARX5", "precise3d"]
    },
    "22xh": {
        "task_name": "fold_dishcloth",
        "task_tag": ["softbody", "single-arm", "ARX5"]
    },
    "22wy": {
        "task_name": "water_potted_plant",
        "task_tag": ["temporal", "single-arm", "ARX5"]
    },
    "22ru": {
        "task_name": "sort_electronic_products",
        "task_tag": ["repeated", "single-arm", "ARX5", "classification"]
    },
    "238i": {
        "task_name": "sweep_the_rubbish",
        "task_tag": ["bimanual", "two-arm", "ALOHA", "multiview"]
    },
    "227f": {
        "task_name": "arrange_fruits_in_basket",
        "task_tag": ["simple-pick", "repeated", "single-arm", "UR5"]
    },
    "22q7": {
        "task_name": "shred_scrap_paper",
        "task_tag": ["precise3d", "single-arm", "UR5", "softbody", "multiview"]
    },
    "2368": {
        "task_name": "put_opener_in_drawer",
        "task_tag": ["precise3d", "two-arm", "ALOHA", "manipulation"]
    },
    "23a9": {
        "task_name": "search_green_boxes",
        "task_tag": ["multiview", "single-arm", "ARX5"]
    },
    "2336": {
        "task_name": "wipe_the_table",
        "task_tag": ["softbody", "single-arm", "ARX5"]
    },
    "23aa": {
        "task_name": "set_the_plates",
        "task_tag": ["repeated", "single-arm", "UR5"]
    },
    "239v": {
        "task_name": "stack_color_blocks",
        "task_tag": ["simple-pick", "single-arm", "UR5", "classification"]
    },
    "238h": {
        "task_name": "hang_toothbrush_cup",
        "task_tag": ["multiview", "single-arm", "UR5", "precise3d"]
    },
    "23a4": {
        "task_name": "turn_on_light_switch",
        "task_tag": ["precise3d", "single-arm", "ARX5", "manipulation"]
    },
    "22wr": {
        "task_name": "sort_books",
        "task_tag": ["precise3d", "single-arm", "UR5", "repeated", "classification"]
    },
    "23a8": {
        "task_name": "turn_on_faucet",
        "task_tag": ["precise3d", "two-arm", "ALOHA", "manipulation"]
    },
    "23cp": {
        "task_name": "press_three_buttons",
        "task_tag": ["temporal", "single-arm", "Franka", "repeated"]
    },
    "23cn": {
        "task_name": "plug_in_network_cable",
        "task_tag": ["bimanual", "two-arm", "ALOHA", "precise3d"]
    },
    "23cm": {
        "task_name": "move_objects_into_box",
        "task_tag": ["repeated", "single-arm", "Franka"]
    }
}

# 榜单模型列表：(user_name, display_name) 精准定位，避免不同用户同名模型混淆
# rank_models = [
#     ('Robotera',    'Era0'),
#     ('Dexmal',      'DM0'),
#     ('lyf',         'GigaBrain-0.1'),
#     ('Spirit AI',   'Spirit-v1.5'),
#     ('rc_baseline', 'pi0.5'),
#     ('Pushi Zhang', 'wall-oss-v0.1'),
#     ('rc_baseline', 'pi0'),
#     ('Chongyang Xu', 'X-VLA')
# ]
rank_models = [
    ('Atlas', 'Lira_generalist'),
    ('Atlas', 'Atlas_generalist'),
    ('Dexmal', 'DM0_generalist'),
    ('Sicheng Xie', 'VLO'),
    ('wyf', 'pi05_generalist'),
    ('Sicheng Xie', 'GR00T-MULTI'),
    ('wyf', 'pi0_generalist'),
    ('Xiangyue Wu', 'VLA_test_0204'),
]

class RobotDataAnalyzer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = self._load_data()
        # 数据展平，用于整体排名的核心聚合逻辑
        self.flat_rollouts = self._flatten_rollouts()
        # 榜单标准 runs：按 rank_models 过滤 + 去重，一次构建，全局复用
        self.rank_model_names = [m for _, m in rank_models]
        self.canonical_runs = self.build_canonical_runs(rank_models)

    def _load_data(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            return []

    def _get_display_name(self, run_entry):
        """统一获取 Display Name 的逻辑"""
        raw_display_name = run_entry.get('display_name')
        raw_model_name = run_entry.get('model_name', 'Unknown')
        return raw_display_name if raw_display_name else raw_model_name

    def _flatten_rollouts(self):
        """
        按照 display_name 进行整体聚合 (用于总榜)
        """
        flat_data = []
        for run in self.data:
            group_key = self._get_display_name(run)
            rollouts = run.get('rollouts', [])

            for r in rollouts:
                flat_data.append({
                    "group_name": group_key,
                    "score": r.get('score', 0),
                    "completion": r.get('completion', False)
                })
        return flat_data

    def build_canonical_runs(self, target_models: list) -> list:
        """
        按榜单规则生成去重后的标准 runs 列表，供所有下游分析和绘图使用。

        两步去重：
        - Step 1: 按 (user_name, model_name, task_id) 去重 → 同一具体模型同一任务取最新提交（time 最大）。
        - Step 2: 按 (user_name, display_name, task_id) 聚合 → 从各变体中取最高 SR，SR 相同取最高 Score。

        返回：原始 run dict 的列表，每个 (user, display_name, task_id) 恰好一条。
        """
        target_set = {(u, m) for u, m in target_models}

        # Step 1: 按 (user, model_name, task_id) 去重，取最新时间
        step1: dict = {}
        for run in self.data:
            user = run.get('user_name', '')
            model = self._get_display_name(run)
            if (user, model) not in target_set:
                continue
            mn = run.get('model_name', '')
            task_id = run.get('task_id', '')
            key = (user, mn, task_id)
            if key not in step1 or run.get('time', 0) > step1[key].get('time', 0):
                step1[key] = run

        # Step 2: 按 (user, display_name, task_id) 取最高 SR → 最高 Score
        step2: dict = {}
        for run in step1.values():
            user = run.get('user_name', '')
            model = self._get_display_name(run)
            task_id = run.get('task_id', '')
            key = (user, model, task_id)
            sr = run.get('success_rate', 0.0)
            score = run.get('score', 0.0)
            if key not in step2:
                step2[key] = run
            else:
                prev = step2[key]
                if sr > prev.get('success_rate', 0.0) or (
                        sr == prev.get('success_rate', 0.0) and score > prev.get('score', 0.0)):
                    step2[key] = run

        canonical = list(step2.values())
        print(f"✅ canonical runs 构建完成：{len(canonical)} 条"
              f"（{len(target_models)} 个模型 × 各任务去重后）")
        return canonical

    def plot_specific_models_dashboard(self):
        """
        绘制榜单模型在所有任务上的成功率热力图，使用 self.canonical_runs。
        """
        import numpy as np

        # 直接从 canonical_runs 构建 task_data
        task_data = {}
        for run in self.canonical_runs:
            t_id = run.get('task_id', 'Unknown')
            m_name = self._get_display_name(run)
            t_real_name = task_map.get(str(t_id), {}).get("task_name", str(t_id))

            if t_id not in task_data:
                task_data[t_id] = {'name': t_real_name, 'rates': {}}

            # 直接用顶层 success_rate（与榜单一致）
            task_data[t_id]['rates'][m_name] = run.get('success_rate', 0.0)

        sorted_task_ids = sorted(task_data.keys())

        # X轴标签：任务名
        x_labels = []
        for tid in sorted_task_ids:
            name = task_data[tid]['name']
            # 截断过长的任务名
            short_name = (name[:15] + '..') if len(name) > 15 else name
            x_labels.append(f"{short_name}")

        # 准备数据矩阵：matrix[model_idx][task_idx]
        matrix = np.zeros((len(self.rank_model_names), len(sorted_task_ids)))

        for i, model in enumerate(self.rank_model_names):
            for j, tid in enumerate(sorted_task_ids):
                rate = task_data[tid]['rates'].get(model, 0.0)
                matrix[i, j] = rate

        print("\n" + "=" * 40)
        print(f"📊 Model Average SR (across {len(sorted_task_ids)} tasks):")
        for i, model in enumerate(self.rank_model_names):
            avg_sr = np.mean(matrix[i, :])
            print(f"  • {model:<20}: {avg_sr * 100:.2f}%")
        print("=" * 40 + "\n")

        fig, ax = plt.subplots(figsize=(20, 8))  # 宽画布

        im = ax.imshow(matrix, cmap='YlGnBu', aspect='auto', vmin=0, vmax=1)

        ax.set_xticks(range(len(x_labels)))
        ax.set_xticklabels(x_labels, rotation=45, ha="right", fontsize=9)

        ax.set_yticks(range(len(self.rank_model_names)))
        ax.set_yticklabels(self.rank_model_names, fontsize=11, fontweight='bold')

        for i in range(len(self.rank_model_names)):
            for j in range(len(x_labels)):
                val = matrix[i, j]
                text_color = "white" if val > 0.5 else "black"
                label = f"{int(val * 100)}"
                ax.text(j, i, label, ha="center", va="center", color=text_color, fontsize=8)

        cbar = ax.figure.colorbar(im, ax=ax)
        cbar.ax.set_ylabel("Success Rate", rotation=-90, va="bottom")

        plt.title(f"Top {len(self.rank_model_names)} Models across {len(sorted_task_ids)} Tasks",
                  fontsize=16)
        plt.tight_layout()
        plt.show()

    def generate_model_task_table(self, out_excel: str = None, highlight: bool = True):
        """
        生成指定模型在任务级别的表格，直接使用 self.canonical_runs（已去重）。
        SR 和 Score 直接读顶层字段，与榜单口径一致。
        """

        # ============================
        # 1. 数据准备：从 canonical_runs 构建 (model_name, task_id) -> run
        # ============================
        global task_map
        current_task_map = task_map if 'task_map' in globals() else getattr(self, "task_map", {})

        # 直接从 canonical_runs 建查找表，无需再做去重
        best_runs_map = {}
        for run in self.canonical_runs:
            m_name = self._get_display_name(run)
            t_id = str(run.get('task_id', ''))
            if m_name and t_id:
                best_runs_map[(m_name, t_id)] = run

        # 收集所有任务 ID（来自 canonical_runs）
        tids = {str(run.get('task_id', '')) for run in self.canonical_runs if run.get('task_id')}

        rows = []
        for t_id in tids:
            raw_name = str(t_id)
            if current_task_map and t_id in current_task_map:
                raw_name = current_task_map[t_id].get("task_name", str(t_id))
            display_name = raw_name.replace("_", " ")

            row_data = {}
            for m in self.rank_model_names:
                target_run = best_runs_map.get((m, t_id))
                if target_run:
                    sr = round(target_run.get('success_rate', 0.0) * 100.0, 1)
                    score = round(target_run.get('score', 0.0), 1)
                else:
                    sr, score = 0.0, 0.0
                row_data[(m, "SR")] = sr
                row_data[(m, "Score")] = score

            rows.append({"name": display_name, "data": row_data})

        # ============================
        # 2. DataFrame 构建
        # ============================
        rows.sort(key=lambda x: x["name"])

        sorted_data = [r["data"] for r in rows]
        index_names = [r["name"] for r in rows]

        if sorted_data:
            df = pd.DataFrame(sorted_data, index=pd.Index(index_names, name="Task"))
            df.columns = pd.MultiIndex.from_tuples(df.columns)
        else:
            cols = pd.MultiIndex.from_product([self.rank_model_names, ["SR", "Score"]])
            df = pd.DataFrame(columns=cols)

        # 强制列顺序
        ordered_cols = []
        for m in self.rank_model_names:
            ordered_cols.append((m, "SR"))
            ordered_cols.append((m, "Score"))
        df = df.reindex(columns=pd.MultiIndex.from_tuples(ordered_cols))

        # 计算 Average 行
        if not df.empty:
            avg_series = df.mean(axis=0).round(2)
            df_avg = pd.DataFrame([avg_series], index=["average"])
            df_final = pd.concat([df_avg, df], axis=0)
        else:
            df_final = df

        # 控制台预览
        print("-" * 30)
        print(df_final.head().to_string())
        print("-" * 30)

        # ============================
        # 3. 导出 Excel
        # ============================
        if out_excel:
            with pd.ExcelWriter(out_excel, engine="openpyxl") as writer:
                df_final.to_excel(writer, sheet_name="Result")

            if highlight:
                from openpyxl import load_workbook
                from openpyxl.styles import PatternFill, Font, Alignment, Border, Side

                wb = load_workbook(out_excel)
                ws = wb["Result"]

                # --- 定义样式 ---
                FONT_NAME = "Times New Roman"
                BORDER_THIN = Side(style='thin', color="000000")
                HIGHLIGHT_FILL = PatternFill(start_color="BCDBED", end_color="BCDBED", fill_type="solid")

                max_row = ws.max_row
                max_col = ws.max_column

                header_sub_row = 2
                average_row = 3

                # (A) 通用格式
                for row in ws.iter_rows(min_row=1, max_row=max_row, min_col=1, max_col=max_col):
                    for cell in row:
                        cell.font = Font(name=FONT_NAME, size=11)
                        cell.alignment = Alignment(horizontal='center', vertical='center')

                for r in range(3, max_row + 1):
                    ws.cell(row=r, column=1).alignment = Alignment(horizontal='left', vertical='center')

                # 边框绘制
                for c in range(1, max_col + 1):
                    ws.cell(row=header_sub_row, column=c).border = Border(bottom=BORDER_THIN)
                for c in range(1, max_col + 1):
                    cur = ws.cell(row=average_row, column=c).border
                    ws.cell(row=average_row, column=c).border = Border(
                        bottom=BORDER_THIN, top=cur.top, left=cur.left, right=cur.right
                    )
                for c in range(3, max_col, 2):
                    for r in range(1, max_row + 1):
                        cell = ws.cell(row=r, column=c)
                        cur = cell.border
                        cell.border = Border(
                            right=BORDER_THIN, bottom=cur.bottom, top=cur.top, left=cur.left
                        )

                # 高亮逻辑
                for r in range(average_row, max_row + 1):
                    # SR 高亮
                    sr_values = []
                    sr_cols_idx = range(2, max_col + 1, 2)
                    for c in sr_cols_idx:
                        val = ws.cell(row=r, column=c).value
                        sr_values.append(val if isinstance(val, (int, float)) else -1)

                    if sr_values:
                        max_sr = max(sr_values)
                        for idx, c in enumerate(sr_cols_idx):
                            if sr_values[idx] == max_sr and max_sr > 0:
                                ws.cell(row=r, column=c).fill = HIGHLIGHT_FILL

                    # Score 高亮
                    score_values = []
                    score_cols_idx = range(3, max_col + 1, 2)
                    for c in score_cols_idx:
                        val = ws.cell(row=r, column=c).value
                        score_values.append(val if isinstance(val, (int, float)) else -float('inf'))

                    if score_values:
                        max_score = max(score_values)
                        for idx, c in enumerate(score_cols_idx):
                            if score_values[idx] == max_score and max_score > 0:
                                ws.cell(row=r, column=c).fill = HIGHLIGHT_FILL

                ws.column_dimensions['A'].width = 25
                wb.save(out_excel)
                print(f"✅ Excel 已生成: {out_excel}")

        return df_final

    def generate_tag_stats(self, target_models: list = None):
        """
        按任务标签（Tag）维度统计数据，使用 self.canonical_runs 作为数据源（已去重）。

        target_models: 模型 display_name 的列表（字符串）。None 时使用 self.rank_model_names。
        """
        import pandas as pd
        import statistics

        global task_map
        current_task_map = task_map if 'task_map' in globals() else getattr(self, "task_map", {})

        # 统一归一化：无论传入字符串列表还是 (user, model) 元组列表，都提取 display_name
        if not target_models:
            model_names = self.rank_model_names
        elif isinstance(target_models[0], tuple):
            model_names = [m for _, m in target_models]
        else:
            model_names = list(target_models)

        # 使用 canonical_runs 作为数据源，按 display_name 过滤
        target_set = set(model_names)
        source_runs = [r for r in self.canonical_runs if self._get_display_name(r) in target_set]

        # =====================================================
        # 统计：按 Tag 聚合（canonical_runs 已去重，无需再做去重）
        # =====================================================
        stats = {}

        for run in source_runs:
            t_id = str(run.get('task_id', ''))
            model_name = self._get_display_name(run)

            tags = []
            if current_task_map and t_id in current_task_map:
                tags = current_task_map[t_id].get("task_tag", [])
            if not tags:
                tags = ["Uncategorized"]

            # 直接使用顶层字段，与榜单口径一致
            sr = run.get('success_rate', 0.0)  # 0.0 - 1.0
            score = run.get('score', 0.0)
            rollouts = run.get('rollouts', [])
            n_total = len(rollouts)
            n_success = round(sr * n_total) if n_total > 0 else 0

            for tag in tags:
                if tag not in stats:
                    stats[tag] = {
                        'unique_tasks': set(),
                        'model_names': set(),
                        'total_episodes': 0,
                        'total_success': 0,
                        'run_scores': [],
                        'by_model': {}
                    }

                stats[tag]['unique_tasks'].add(t_id)
                stats[tag]['model_names'].add(model_name)
                stats[tag]['total_episodes'] += n_total
                stats[tag]['total_success'] += n_success
                stats[tag]['run_scores'].append(score)

                if model_name not in stats[tag]['by_model']:
                    stats[tag]['by_model'][model_name] = {'success': 0, 'total': 0}
                stats[tag]['by_model'][model_name]['success'] += n_success
                stats[tag]['by_model'][model_name]['total'] += n_total

        # =====================================================
        # 生成结果 DataFrame
        # =====================================================
        result_data = []
        all_tags = sorted(list(stats.keys()))

        for tag in all_tags:
            row = {"Tag": tag}
            row["Tasks"] = len(stats[tag]['unique_tasks'])
            has_data = False
            for m in model_names:
                m_data = stats[tag]['by_model'].get(m, {'success': 0, 'total': 0})
                if m_data['total'] > 0:
                    row[m] = round((m_data['success'] / m_data['total']) * 100.0, 1)
                    has_data = True
                else:
                    row[m] = 0.0
            if has_data:
                result_data.append(row)

        cols = ["Tasks"] + model_names

        if result_data:
            df = pd.DataFrame(result_data)
            df.set_index("Tag", inplace=True)
            df = df.reindex(columns=cols)
        else:
            df = pd.DataFrame(columns=cols)

        print("\n" + "=" * 10 + " Tag Stats (canonical runs) " + "=" * 10)
        print(df.to_string())

        return df

    def generate_rank_stats_overview(self, target_models: list = None,
                                     out_json: str = "canonical_runs.json"):
        """
        统计指定模型列表的全局概览，直接使用 self.canonical_runs（init 时已构建）。
        运行完成后将 canonical_runs 存为 JSON，供后续所有分析脚本使用。

        Score：各任务最佳 score 的均值。
        SR：各任务最佳 success_rate 的均值（×100 转为百分比）。
        out_json: 输出 canonical runs 的 JSON 路径（None 则不存盘）。
        """
        if target_models is None:
            target_models = rank_models
        canonical = self.canonical_runs

        agg = {(u, m): {'sr_sum': 0.0, 'score_sum': 0.0, 'tasks': 0} for u, m in target_models}
        for run in canonical:
            user = run.get('user_name', '')
            model = self._get_display_name(run)
            agg[(user, model)]['sr_sum'] += run.get('success_rate', 0.0)
            agg[(user, model)]['score_sum'] += run.get('score', 0.0)
            agg[(user, model)]['tasks'] += 1

        result_list = []
        for u, m in target_models:
            d = agg[(u, m)]
            n = d['tasks']
            result_list.append({
                "Model": m,
                "User": u,
                "Tasks": n,
                "Success Rate (%)": round((d['sr_sum'] / n) * 100.0 if n > 0 else 0.0, 2),
                "Avg Score": round(d['score_sum'] / n if n > 0 else 0.0, 2),
            })

        df = pd.DataFrame(result_list)
        df.sort_values(by="Avg Score", ascending=False, inplace=True)

        print(f"\n{'=' * 30} 🏆 模型总榜概览 {'=' * 30}")
        print(df.to_string(index=False))
        print(f"{'=' * 76}")

        # 将 canonical_runs 持久化，后续所有分析直接读这个文件
        if out_json:
            with open(out_json, 'w', encoding='utf-8') as f:
                json.dump(canonical, f, ensure_ascii=False, indent=2)
            print(f"✅ canonical_runs 已保存 → {out_json}  ({len(canonical)} 条)")

        return df

    def generate_task_champions_table(self, top_k: int = 3, out_excel: str = None):
        """
        生成每个 Task 中榜单模型的 Top K 排名表格，使用 self.canonical_runs（已去重）。
        SR 和 Score 直接读顶层字段，与榜单口径一致。
        """
        global task_map
        current_task_map = task_map if 'task_map' in globals() else getattr(self, "task_map", {})

        # canonical_runs 每个 (model, task) 已恰好一条，按 task 分组即可
        task_results = defaultdict(list)
        for run in self.canonical_runs:
            t_id = str(run.get('task_id', '') or 'Unknown_ID')
            task_results[t_id].append({
                'model': self._get_display_name(run),
                'sr': run.get('success_rate', 0.0) * 100.0,
                'score': run.get('score', 0.0),
            })

        table_rows = []
        for t_id, runs in task_results.items():
            meta = current_task_map.get(t_id, {})
            t_name = meta.get("task_name", t_id)
            t_tags = meta.get("task_tag", [])
            t_tags_str = ", ".join(t_tags) if isinstance(t_tags, list) else str(t_tags)

            runs.sort(key=lambda x: (x['sr'], x['score']), reverse=True)

            row_data = {
                "Task ID": t_id,
                "Task Name": t_name,
                "Tags": t_tags_str,
                "Model Count": len(runs)
            }
            for i in range(top_k):
                p = f"Rank {i + 1}"
                if i < len(runs):
                    row_data[f"{p} Model"] = runs[i]['model']
                    row_data[f"{p} SR(%)"] = round(runs[i]['sr'], 1)
                    row_data[f"{p} Score"] = round(runs[i]['score'], 1)
                else:
                    row_data[f"{p} Model"] = "-"
                    row_data[f"{p} SR(%)"] = "-"
                    row_data[f"{p} Score"] = "-"
            table_rows.append(row_data)

        df = pd.DataFrame(table_rows)
        if not df.empty:
            df.sort_values(by="Task Name", inplace=True)
            base_cols = ["Task ID", "Task Name", "Tags", "Model Count"]
            rank_cols = []
            for i in range(top_k):
                p = f"Rank {i + 1}"
                rank_cols.extend([f"{p} Model", f"{p} SR(%)", f"{p} Score"])
            df = df[[c for c in base_cols + rank_cols if c in df.columns]]

        print(f"\n{'=' * 20} Task Champions Table (Preview) {'=' * 20}")
        print(df.head().to_string(index=False))

        if out_excel and not df.empty:
            try:
                with pd.ExcelWriter(out_excel, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Champions', index=False)
                    ws = writer.sheets['Champions']
                    for column in ws.columns:
                        max_len = max((len(str(cell.value or '')) for cell in column), default=10)
                        ws.column_dimensions[column[0].column_letter].width = min((max_len + 2) * 1.1, 40)
                print(f"✅ 榜单表格已生成: {out_excel}")
            except Exception as e:
                print(f"❌ 导出 Excel 失败: {e}")

        return df

    def generate_task_champions_table_max(self, top_k: int = 3, out_excel: str = None):
        """generate_task_champions_table 的别名（逻辑已合并，canonical_runs 已是最优去重结果）。"""
        return self.generate_task_champions_table(top_k=top_k, out_excel=out_excel)


    def plot_models_radar_grid(self, target_models: list, out_file: str = "models_radar_grid.png"):
        """
        生成“多子图”雷达图（多边形风格）。
        """
        # 1. 获取数据
        df = self.generate_tag_stats(target_models=target_models)

        if df.empty:
            print("⚠️ 数据为空")
            return

        # 2. 剔除不需要的标签
        exclude_tags = ["ALOHA", "ARX5", "Franka", "UR5", "two-arm", "single-arm"]
        df_plot = df.drop(index=exclude_tags, errors='ignore')
        df_plot = df_plot.drop(columns=['Tasks'], errors='ignore')
        # 检查维度
        categories = df_plot.index.tolist()
        N = len(categories)
        if N < 3:
            print(f"⚠️ 有效标签少于3个 ({categories})，无法绘制雷达图。")
            return

        # 3. 计算网格布局
        models = df_plot.columns.tolist()
        num_models = len(models)

        cols = 4 if num_models >= 4 else num_models
        rows = (num_models + cols - 1) // cols

        # 4. 初始化大图
        fig, axes = plt.subplots(rows, cols, figsize=(4 * cols, 4 * rows),
                                 subplot_kw=dict(polar=True))

        if num_models == 1:
            axes = [axes]
        else:
            axes = axes.flatten()

        # 准备角度 (闭合)
        angles = [n / float(N) * 2 * pi for n in range(N)]
        angles += angles[:1]

        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']

        # 定义网格刻度 (用于画多边形背景)
        grid_levels = [20, 50, 80, 100]

        # 5. 循环绘制每个模型
        for i, model_name in enumerate(models):
            ax = axes[i]
            color = colors[i % len(colors)]

            # 获取数据并闭合
            values = df_plot[model_name].values.flatten().tolist()
            values += values[:1]

            # --- 核心修改：绘制多边形网格背景 ---
            # A. 关掉默认的圆形 Y 轴网格 和 外部圆圈脊柱
            ax.yaxis.grid(False)
            ax.spines['polar'].set_visible(False)

            # B. 保持 X 轴（放射线）网格，并设置样式
            ax.xaxis.grid(True, color='grey', linestyle='--', linewidth=0.5, alpha=0.5)

            # C. 手动画多边形等高线 (20, 50, 80, 100)
            # zorder=0 确保网格在数据下方
            for level in grid_levels:
                ax.plot(angles, [level] * len(angles),
                        color='grey', linestyle='--', linewidth=0.5, alpha=0.5, zorder=0)

            # -----------------------------------

            # 绘图 (数据层)
            ax.plot(angles, values, linewidth=2, linestyle='solid', color=color, zorder=10)
            ax.fill(angles, values, color=color, alpha=0.25, zorder=10)

            # --- 子图标签设置 ---
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories, size=9)

            # 设置 Y 轴标签 (只显示数值，不显示网格线)
            ax.set_rlabel_position(0)
            ax.set_yticks(grid_levels[:-1])  # 不显示 100 的数字，避免跟标题打架
            ax.set_yticklabels([str(x) for x in grid_levels[:-1]], color="grey", size=7)
            ax.set_ylim(0, 100)

            # 设置标题
            ax.set_title(model_name, size=14, weight='bold', position=(0.5, 1.1))

        # 6. 隐藏多余子图
        for j in range(num_models, len(axes)):
            fig.delaxes(axes[j])

        # 7. 全局布局
        plt.tight_layout()
        plt.subplots_adjust(top=0.85, hspace=0.4, wspace=0.3)

        fig.suptitle("Model Capabilities (SR%)", fontsize=20, weight='bold')

        plt.savefig(out_file, bbox_inches='tight')
        plt.close()
        print(f"✅ 多边形雷达图已生成: {out_file}")

    def calculate_overall_best_success_rate(self, verbose: bool = True):
        """
        计算整体的最佳平均成功率 (Oracle Success Rate)。

        逻辑：
        1. 遍历所有数据，按 Task -> Model 分组统计 Success 和 Total Rollouts。
        2. 对于每个 Task，找出所有模型中最高的那个 SR (Max SR)。
        3. 对所有 Task 的 Max SR 求平均值。

        Args:
            verbose: 是否打印详细的每个任务的最佳 SR 概览。
        """

        # ============================
        # 1. 数据聚合 (与原函数逻辑保持一致)
        # ============================
        # temp_data[task_id][model_name] = {'success': 0, 'total': 0}
        temp_data = defaultdict(lambda: defaultdict(lambda: {'success': 0, 'total': 0}))

        for run in self.data:
            # 获取 Task ID
            t_id = str(run.get('task_id') or run.get('env_id') or run.get('task') or "Unknown_ID")
            # 获取模型名称
            model_name = self._get_display_name(run)

            rollouts = run.get('rollouts', [])
            if not rollouts:
                continue

            # 统计当前 Run 的数据
            run_success = sum(1 for r in rollouts if r.get('completion', False))
            run_total = len(rollouts)

            # 累加到聚合字典中
            temp_data[t_id][model_name]['success'] += run_success
            temp_data[t_id][model_name]['total'] += run_total

        # ============================
        # 2. 计算每个 Task 的最高 SR
        # ============================
        task_max_srs = []

        # 用于展示的详细列表
        detail_rows = []

        global task_map
        current_task_map = task_map if 'task_map' in globals() else getattr(self, "task_map", {})

        for t_id, models in temp_data.items():
            # 计算该任务下所有模型的 SR，并取最大值
            best_sr_for_this_task = 0.0
            best_model_name = "None"

            for m_name, stats in models.items():
                if stats['total'] > 0:
                    sr = (stats['success'] / stats['total']) * 100.0
                    if sr > best_sr_for_this_task:
                        best_sr_for_this_task = sr
                        best_model_name = m_name

            task_max_srs.append(best_sr_for_this_task)

            # 记录详细信息用于展示
            meta = current_task_map.get(t_id, {})
            t_name = meta.get("task_name", t_id)

            detail_rows.append({
                "Task ID": t_id,
                "Task Name": t_name,
                "Best Model": best_model_name,
                "Max SR(%)": best_sr_for_this_task
            })

        # ============================
        # 3. 计算整体平均值 (Macro Average of Max SRs)
        # ============================
        if not task_max_srs:
            print("⚠️ No valid task data found.")
            return 0.0

        overall_best_sr = statistics.mean(task_max_srs)

        # ============================
        # 4. 输出结果
        # ============================
        if verbose:
            print(f"\n{'=' * 20} Overall Best Success Rate Analysis {'=' * 20}")
            print(f"Total Tasks Analyzed: {len(task_max_srs)}")
            print(f"Overall Best SR (Avg of Max per Task): {overall_best_sr:.2f}%\n")

            # 打印 Top 5 和 Bottom 5 任务概览，或者全部
            df_details = pd.DataFrame(detail_rows)
            if not df_details.empty:
                df_details.sort_values(by="Max SR(%)", ascending=False, inplace=True)
                print("--- Details (Top 5 Tasks) ---")
                print(df_details.head(5).to_string(index=False))
                print("..." if len(df_details) > 10 else "")
                if len(df_details) > 5:
                    print("--- Details (Bottom 5 Tasks) ---")
                    print(df_details.tail(5).to_string(index=False))
            print("=" * 60)

        return overall_best_sr

    def generate_tag_aggregated_sr_all_runs(self, target_models: list = None):
        """
        【修改版】统计标签（Tag）维度下，所有模型的整体平均成功率。

        变更点：
        取消了 "Best Run" 筛选逻辑。
        现在会统计 self.data 中存在的所有 Run，无论同一个任务跑了多少次，全部累加。

        输出:
        DataFrame, 索引为 Tag
        """
        import pandas as pd

        global task_map
        current_task_map = task_map if 'task_map' in globals() else getattr(self, "task_map", {})

        # 用于聚合统计的字典
        # 结构: { tag_name: { 'tasks': set(), 'models': set(), 'success': int, 'total': int } }
        tag_stats = {}

        for run in self.data:
            # --- 1. 基础信息提取 ---
            m_name = self._get_display_name(run)
            t_id = str(run.get('task_id') or run.get('env_id') or run.get('task'))

            if not m_name or not t_id:
                continue

            # 筛选指定模型
            if target_models and m_name not in target_models:
                continue

            rollouts = run.get('rollouts', [])
            if not rollouts:
                continue

            # --- 2. 计算当前 Run 的数据 (不再与历史 Run 比较，直接使用) ---
            n_success = sum(1 for r in rollouts if r.get('completion', False))
            n_total = len(rollouts)

            # 如果这个 Run 没有有效测试数据，跳过
            if n_total == 0:
                continue

            # --- 3. 获取标签 ---
            tags = []
            if current_task_map and t_id in current_task_map:
                tags = current_task_map[t_id].get("task_tag", [])
            if not tags:
                tags = ["Uncategorized"]

            # --- 4. 累加数据到 Tag ---
            for tag in tags:
                if tag not in tag_stats:
                    tag_stats[tag] = {
                        'tasks': set(),  # 记录涉及了多少种 unique task
                        'models': set(),  # 记录涉及了多少个 unique model
                        'total_success': 0,  # 成功次数累加
                        'total_episodes': 0  # 总尝试次数累加
                    }

                tag_stats[tag]['tasks'].add(t_id)
                tag_stats[tag]['models'].add(m_name)
                tag_stats[tag]['total_success'] += n_success
                tag_stats[tag]['total_episodes'] += n_total

        # =====================================================
        # 5. 生成结果 DataFrame
        # =====================================================
        result_data = []
        sorted_tags = sorted(list(tag_stats.keys()))

        for tag in sorted_tags:
            d = tag_stats[tag]
            total = d['total_episodes']
            success = d['total_success']

            # 计算微平均 SR
            avg_sr = (success / total * 100.0) if total > 0 else 0.0

            result_data.append({
                "Tag": tag,
                "Unique Tasks": len(d['tasks']),  # 涉及的任务种类数
                "Models": len(d['models']),  # 参与的模型数量
                "Total Episodes": total,  # 此时这个数字会比之前大，因为它包含了重复跑的测试
                "Overall SR (%)": round(avg_sr, 2)
            })

        cols = ["Unique Tasks", "Models", "Total Episodes", "Overall SR (%)"]

        if result_data:
            df = pd.DataFrame(result_data)
            df.set_index("Tag", inplace=True)
            df = df.reindex(columns=cols)
        else:
            df = pd.DataFrame(columns=cols)

        print("\n" + "=" * 10 + " Tag Stats (All Runs Included) " + "=" * 10)
        print(df.to_string())

        return df

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side


def upsert_border(cell, top=None, bottom=None, left=None, right=None):
    """
    辅助函数：安全更新单元格边框。
    读取现有的边框设置，只修改传入的参数，避免覆盖原本存在的其他方向边框。
    """
    cur = cell.border

    # 如果传入了新样式则使用，否则保留原有样式
    new_top = top if top is not None else cur.top
    new_bottom = bottom if bottom is not None else cur.bottom
    new_left = left if left is not None else cur.left
    new_right = right if right is not None else cur.right

    cell.border = Border(top=new_top, bottom=new_bottom, left=new_left, right=new_right)


def save_styled_excel(df: pd.DataFrame, out_path: str, highlight: bool = True):
    # 1. 基础写入
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Result")

    # 2. 加载工作簿
    wb = load_workbook(out_path)
    ws = wb["Result"]

    # --- 样式定义 ---
    FONT_NAME = "Times New Roman"
    FONT_SIZE = 11

    # 边框线条风格
    BORDER_THIN = Side(style='thin', color="000000")  # 细线（用于内部）
    BORDER_THICK = Side(style='medium', color="000000")  # 粗线（用于顶部和底部，可选）

    # 高亮颜色
    HIGHLIGHT_FILL = PatternFill(start_color="BCDBED", end_color="BCDBED", fill_type="solid")

    max_row = ws.max_row
    max_col = ws.max_column

    # 定位关键行
    header_top_row = 1  # 表头第一行
    header_sub_row = 2  # 表头第二行 (SR/Score)
    data_start_row = 3  # 数据开始行

    # ============================
    # (A) 全局字体与对齐
    # ============================
    for row in ws.iter_rows(min_row=1, max_row=max_row, min_col=1, max_col=max_col):
        for cell in row:
            cell.font = Font(name=FONT_NAME, size=FONT_SIZE)
            cell.alignment = Alignment(horizontal='center', vertical='center')

    # 任务名列 (第一列) 左对齐，拉宽
    for r in range(data_start_row, max_row + 1):
        ws.cell(row=r, column=1).alignment = Alignment(horizontal='left', vertical='center')
    ws.column_dimensions['A'].width = 25

    # ============================
    # (B) 边框绘制 (使用 upsert_border 防止覆盖)
    # ============================

    # 1. 表格 顶部 横线 (Row 1 上方) - 使用粗线更有质感
    for c in range(1, max_col + 1):
        upsert_border(ws.cell(row=header_top_row, column=c), top=BORDER_THIN)

    # 2. 表头 底部 横线 (Row 2 下方) - 分隔表头和数据
    for c in range(1, max_col + 1):
        upsert_border(ws.cell(row=header_sub_row, column=c), bottom=BORDER_THIN)

    # 3. Average 行 底部 横线 (Row 3 下方)
    # 只有当数据行数足够时才画
    if max_row >= data_start_row:
        for c in range(1, max_col + 1):
            upsert_border(ws.cell(row=data_start_row, column=c), bottom=BORDER_THIN)

    # 4. 表格 底部 横线 (最后一行 下方)
    for c in range(1, max_col + 1):
        upsert_border(ws.cell(row=max_row, column=c), bottom=BORDER_THIN)

    # 5. 竖向分隔线 (区分不同模型)
    # 逻辑：从第3列开始，每隔2列 (对应 Score 列) 画一条右边框
    # 这样会把 (SR, Score) 作为一个块包起来
    for c in range(3, max_col, 2):
        # 从第1行画到最后一行，贯穿表头
        for r in range(1, max_row + 1):
            upsert_border(ws.cell(row=r, column=c), right=BORDER_THIN)

    # ============================
    # (C) 高亮逻辑 (SR/Score 独立比对)
    # ============================
    if highlight and max_row >= data_start_row:
        for r in range(data_start_row, max_row + 1):

            # 1. SR 列 (偶数列 2, 4, 6...)
            sr_cols = list(range(2, max_col + 1, 2))
            sr_vals = [ws.cell(row=r, column=c).value for c in sr_cols]
            # 过滤非数字
            clean_sr = [v if isinstance(v, (int, float)) else -1 for v in sr_vals]

            if clean_sr:
                max_v = max(clean_sr)
                if max_v > 0:
                    for i, val in enumerate(clean_sr):
                        if val == max_v:
                            ws.cell(row=r, column=sr_cols[i]).fill = HIGHLIGHT_FILL

            # 2. Score 列 (奇数列 3, 5, 7...)
            score_cols = list(range(3, max_col + 1, 2))
            score_vals = [ws.cell(row=r, column=c).value for c in score_cols]
            clean_score = [v if isinstance(v, (int, float)) else -float('inf') for v in score_vals]

            if clean_score:
                max_v = max(clean_score)
                if max_v > 0:
                    for i, val in enumerate(clean_score):
                        if val == max_v:
                            ws.cell(row=r, column=score_cols[i]).fill = HIGHLIGHT_FILL

    wb.save(out_path)
    print(f"✅ Excel 已生成 (边框已修复): {out_path}")



if __name__ == "__main__":
    analyzer = RobotDataAnalyzer("/Users/sunxue/PyCharmMiscProject/RC/data_2026_5_26.json")
    analyzer.generate_rank_stats_overview(rank_models)

    if analyzer.data:
        # 1. 按标签分析
        df_tags_specific = analyzer.generate_tag_stats(rank_models)
        df_tags_specific.to_excel("tag_analysis.xlsx")
        # 2. 按照模型能力（标签）绘制雷达图
        analyzer.plot_models_radar_grid(target_models=rank_models, out_file="tag_radar.png")
        # 3. 上榜的 8 个模型在不同任务下的成功率（热力图）
        analyzer.plot_specific_models_dashboard()
        # 4. 上榜的 8 个模型在不同任务下的 SR 和 score
        analyzer.generate_model_task_table('task_rank_table.xlsx')
        # 5. 各任务的最佳 Top 3 模型 (带详细任务信息)
        analyzer.generate_task_champions_table_max(top_k=3, out_excel="champions.xlsx")
        # 5. 理想状态下的最高成功率
        # analyzer.calculate_overall_best_success_rate()
        # df_result = analyzer.generate_tag_aggregated_sr_all_runs()
