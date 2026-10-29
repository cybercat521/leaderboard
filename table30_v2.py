"""Table30 V2 的固定任务 ID、名称及展示标签；能力标签从官方 V2 元数据读取。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Task:
    id: str
    name: str
    robot: str
    en: str
    zh: str
    emoji: str


# 顺序与中英文 README 的机型分组一致；ID / name 来自官方 V2 任务页。
TASKS = (
    Task("6dcb", "fold_the_clothes", "W1", "Fold clothes", "叠衣服", "👕"),
    Task("2b13", "hold_the_tray_with_both_hands", "W1", "Hold a tray", "双手端托盘", "🍽️"),
    Task("6ab4", "place_objects_into_desk_drawer", "W1", "Fill desk drawer", "将物品放入书桌抽屉", "🗄️"),
    Task("2945", "put_in_pen_container", "W1", "Fill pen holder", "放入笔筒", "✏️"),
    Task("0965", "put_the_shoes_back", "W1", "Put shoes back", "放回鞋子", "👟"),
    Task("8fc9", "stack_bowls", "W1", "Stack bowls", "叠碗", "🥣"),
    Task("b2e8", "sweep_the_trash", "W1", "Sweep trash", "清扫垃圾", "🧹"),
    Task("3232", "tidy_up_the_makeup_table", "W1", "Tidy makeup table", "整理化妆台", "💄"),
    Task("c6b3", "tie_a_knot", "W1", "Tie a knot", "打结", "🪢"),
    Task("1c7d", "untie_the_shoelaces", "W1", "Untie shoelaces", "解开鞋带", "👟"),
    Task("f31b", "lint_roller_remove_dirt", "ALOHA", "Use lint roller", "用粘毛滚筒除尘", "🧽"),
    Task("671c", "pack_the_items", "ALOHA", "Pack items", "打包物品", "📦"),
    Task("6ccd", "pack_the_toothbrush_holder", "ALOHA", "Pack toothbrush holder", "打包牙刷架", "🪥"),
    Task("4bca", "paint_jam", "ALOHA", "Spread jam", "涂抹果酱", "🍓"),
    Task("ae1f", "put_the_books_back", "ALOHA", "Put books back", "放回书本", "📚"),
    Task("fea0", "put_the_pencil_case_into_the_schoolbag", "ALOHA", "Pack pencil case", "将铅笔盒放入书包", "🎒"),
    Task("e358", "scoop_with_a_small_spoon", "ALOHA", "Scoop with spoon", "用小勺舀取", "🥄"),
    Task("3809", "stamp_positioning", "ALOHA", "Position a stamp", "印章定位", "📍"),
    Task("43ea", "wipe_the_blackboard", "ALOHA", "Wipe blackboard", "擦黑板", "🧽"),
    Task("abc7", "wrap_with_a_soft_cloth", "ALOHA", "Wrap with cloth", "用软布包裹", "🧣"),
    Task("9d9d", "arrange_flowers", "ARX5", "Arrange flowers", "整理花束", "💐"),
    Task("3624", "hang_the_cup", "ARX5", "Hang a cup", "挂杯子", "☕"),
    Task("2acf", "pick_out_the_green_blocks", "ARX5", "Pick green blocks", "挑出绿色积木", "🟩"),
    Task("bec8", "press_the_button", "ARX5", "Press buttons", "按下按钮", "🔘"),
    Task("d96c", "turn_on_the_light_switch", "ARX5", "Turn on light", "打开电灯开关", "💡"),
    Task("f5b4", "water_the_flowers", "ARX5", "Water flowers", "给花浇水", "🪴"),
    Task("90e1", "wipe_the_table", "ARX5", "Wipe table", "擦桌子", "🧽"),
    Task("bf87", "arrange_fruits", "UR5", "Arrange fruit", "摆放水果", "🍎"),
    Task("cb19", "item_classification", "UR5", "Sort objects", "物品分类", "🗂️"),
    Task("44df", "shred_paper", "UR5", "Shred paper", "碎纸", "📄"),
)

# 选择至少覆盖三个任务的官方能力标签；这六个展示名称并非官方能力定义。
CAPABILITIES = (
    ("bimanual", "Two-hand", "双手协作"),
    ("precise3d", "Precision", "空间精度"),
    ("manipulation", "Manipulation", "物体操作"),
    ("temporal", "Timing", "时序控制"),
    ("softbody", "Soft-body", "柔性物体"),
    ("repeated", "Repetition", "重复操作"),
)

CHART_TOP_N = 6
METADATA_URL = "https://robochallenge.cn/api/v2/benchmark/benchmark_list.json"
