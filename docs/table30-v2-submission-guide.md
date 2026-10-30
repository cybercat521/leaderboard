# RoboChallenge Table30 V2 提测手册

RoboChallenge 平台当前支持 **Table30 V2** 评测集；历史版本 **Table30 已下线**，不再作为推荐提测入口。相比 Table30，Table30 V2 在任务覆盖、机型组织、评测流程和结果展示上做了更新：任务集合更贴近日常操作场景，按 W1、ALOHA、ARX5、UR5 等机型组织提测要求，并在提交、预约、远程推理和榜单展示链路上提供更清晰的操作入口。

## 提测前准备

请前往 [RoboChallenge 官网](https://robochallenge.cn/evalyourpolicy)提交模型和申请评测，本仓库不受理提测。**平台评测免费，模型推理算力需自行准备。**

- 准备模型权重及运行推理所需的 GPU 等硬件。
- 部署官方 `table30_v2` 客户端，适配模型并完成本地 Mock 测试。
- 申请 RoboChallenge 账号和用户 Token，在官网创建评测提交并取得 `SubmissionId`。
- 联系官方运营团队预约真机，在确认的时间段内运行推理服务。

## 一、RoboChallenge 介绍

### 1.1 模型部署与评测介绍

RoboChallenge 平台不会直接运行用户的代码或权重文件，而是通过**远程 API** 的形式与选手已部署的模型进行实时交互。参测团队需负责自身模型推理服务的部署工作：

- **官方提供支持：** 提供**一键启动模型推理服务与 RC 交互的 Client 脚本**，帮助用户快速打通与评测平台的远程交互链路。

- **自备算力：** 平台仅进行远程接口调用，不提供模型运行机器，**用户必须自行准备模型推理所需的硬件算力。**

<p align="center">
  <img src="../assets/table30-v2-guide/01-overview.png" alt="RoboChallenge 模型部署与评测流程" width="720">
</p>

### 1.2 Table30 V2 任务和机型说明

**❗️重要说明：** 同一个机型下的任务，需要用同一个模型。

## 二、RoboChallenge 平台使用与真机提测

**📍【全局操作流程概览】**

为帮助用户快速理清端到端的提测链路，完整的评测流程可归纳为以下 5 个核心环节（本章及后续章节将逐一进行详细拆解）：

- **Step 1 | 账号注册：** 在 RC 平台注册账号并获取用户 Token。

- **Step 2 | 提交评测：** 在 RC 平台上发起评测请求，获取该次评测专属的有效 `SubmissionId`。

- **Step 3 | 真机预约：** 联系平台运营人员，预约真机评测。（下方有运营人员的微信）

- **Step 4 | 执行评测：** 在预约时段内，通过官方 Client 脚本在本地启动模型（在此之前完成本地 Mock 测试），连接平台完成真机操作。

- **Step 5 | 成绩查询：** 评测结束后，返回 RC 平台的「My Submissions」页面查看详细的成绩。

---

### 2.1 注册

如果已注册过 RoboChallenge 平台的账号，可以跳过这步。如果未注册请按照下面的邮件模板向 **join-robochallenge@robochallenge.ai** 发送邮件，才能申请 RoboChallenge 平台的账号：

```text
Subject: User Account Application Request

Dear RoboChallenge Team,
I would like to apply for a user account for RoboChallenge Platform. My details are as follows:

Full Name: [Your Name]
Nationality: [Your Nationality]
Institute/Organization: [Your Institute / Organization]
Department: [Your Department]
Position/Title: [Your Position]
Email Address: [Your Email]
Phone Number: [Your Phone Number]
Purpose of Application: [Briefly describe your purpose]

Best regards,
[Your Name]

Note: Please send your application email to join-robochallenge@robochallenge.ai
You may write your email in English or Chinese.
```

平台将审核通过后**通过邮件**下发 RC 评测所需 Token，如之前已申请获得 Token 的用户，无需重复注册。

### 2.2 登录

用户需要访问 [https://robochallenge.cn/home](https://robochallenge.cn/home) 点击页面右上角的「Log In」，输入邮箱和 Token 完成登录。

<p align="center">
  <img src="../assets/table30-v2-guide/02-login.png" alt="RoboChallenge 登录入口" width="720">
</p>

### 2.3 提交评测

<p align="center">
  <img src="../assets/table30-v2-guide/03-eval-entry.png" alt="进入 Eval Your Policy 页面" width="720">
</p>

点击「Eval Your Policy」进入提交评测页面。

- Base Model Name：模型名称（会显示在榜单），点击下拉框可以选择已经创建的 Model 信息，如果没有创建过可点击「Create New Model」（仅 Base Model Name 为必填项）。注意：已提测的模型名称不可修改。

<p align="center">
  <img src="../assets/table30-v2-guide/04-model-selection.png" alt="创建或选择模型" width="720">
</p>

<p align="center">
  <img src="../assets/table30-v2-guide/05-submission-config.png" alt="提交评测任务配置" width="720">
</p>

- Count this run in your final score：本次提测结果是否计算到上榜分数

- Select Task：选择提测的任务

    - 记分评测（Yes）：仅可选择单或多个机型下的全部任务，串行评测且提前不告知评测任务顺序。

    - 不记分评测（No）：可以选择某个机型的单个任务，但可以并行评测。

- **如何理解 Submission ID**：一次提交评测无论包含多少个任务，只会生成一个 Submission ID。可以尝试这么理解：要测同一个模型的多个任务，想在一次提测里完成，即得到一个 Submission ID；如果要测多个模型的多个任务，就需要按模型数量拆分成多次提交，而不是一股脑在一次提测中提交。

⚠️ **提交须知：**

- **唯一性：** 单次提交仅生成一个 Submission ID。

- **模型要求：** 若记分评测选择了多款机型，需以**单一模型**完成所选多个机型的全部任务。

### 2.4 真机预约

为了保障 Table30 V2 日常提测流程的高效顺畅，并最大化利用真机资源，目前我们统一采用在**微信群内提交预约申请**的形式进行排期。**运营助手微信**：添加时备注（Table30 V2 评测预约）

<p align="center">
  <img src="../assets/table30-v2-guide/06-wechat-booking.jpg" alt="Table30 V2 运营助手微信二维码" width="260">
</p>

请大家在提交提测需求前，仔细阅读以下预约流程与注意事项：

**预约格式**

请在预约时务必提供准确的信息，大家可以直接复制以下模板进行填写：

```text
RC 账户名称：[填写您 RC 账户名]
机型：[填写所需测试的机型]
任务名称：[填写具体任务名]
任务创建时间：[RC 上显示的任务创建时间]
任务类型：[计分/非计分]
Run id：[必填]
Submission id：[必填]
```

收到您的预约申请后，RC 平台运营人员会根据大家的预期测试需求进行统筹评估，并做出最合理的排期安排。

- **机器分配原则：** 运营人员会按照**最能够顺利测完**的策略进行机器台数的分配，以保障整体测试效率。

- **预约申请提交时间：** 测试前一天的 12:00 前在微信群内将预约申请提交给运营人员（注：周一的预约请在周五 12:00 前提交申请）

- **预约确认：** 运营人员会在排期结束后在群内与用户确认预约信息是否准确。

**⚠️ 请大家特别注意以下三点：**

1. **关于排期差异：** 当前真机测试资源较为紧张，最终释放给您的预约时间或资源配置可能与您提交的需求**有些许出入**，恳请大家的理解与配合。

2. **关于测试延期：** 若在规定的测试时段内，因**自身模型输出异常等个人/队伍原因**导致未能在规划时间内测完，未完成的测试将统一**顺延至 T+1 天**进行。（周六日不进行真机测试，周五未能测完的任务将顺延至周一）

3. **关于资源浪费：** 真机资源宝贵，若因自身原因**无故未完成测试**并造成真机资源空置与浪费，RC 运营方有权**取消该用户/队伍后续预约的所有其他测试**。

### 2.5 查看评测结果

用户在平台提交评测后，可在「My Submissions」中实时追踪测试进度与成绩。具体操作步骤与界面说明如下：

1. **进入控制台**：登录 RC 官网，将鼠标悬停在页面右上角的个人用户头像处，点击下拉菜单中的 「My Submissions」，即可进入您的评测管理主页。

<p align="center">
  <img src="../assets/table30-v2-guide/07-my-submissions-entry.png" alt="进入 My Submissions 页面" width="720">
</p>

<p align="center">
  <img src="../assets/table30-v2-guide/08-my-submissions-list.png" alt="My Submissions 提交记录列表" width="720">
</p>

2. **查看单次评测详情与 SubmissionId：**在页面的历史提交列表中，点击任意一条记录的 **「Detail」** 按钮，即可进入该次提测的详情页：

  - **执行情况：** 详细展示该任务在 **10 次真机执行（Rollout）** 中的具体表现，包括查看成功/失败状态与步骤分。
    - **点击每次执行对应的「rollout details」可查看真机执行回放**
    - 绿色方块中的数字是步骤分，满分 10 分，深绿色代表执行成功，成功与否取决于是否完成所有记分点步骤。
  - **⚠️ 获取核心凭证：** 页面中会明确显示该次提测的 **SubmissionId**。**（特别提醒：SubmissionId 是在本地执行真机推理脚本时的必传凭证）**

<p align="center">
  <img src="../assets/table30-v2-guide/09-submission-detail.png" alt="单次评测详情与 SubmissionId" width="720">
</p>

## 三、模型调试与评测执行指南

在你与平台运营人员成功预约了真机测试时段后，需要通过官方提供的 Client 脚本，在本地启动模型推理服务，并通过远程 API 与 RoboChallenge (RC) 平台进行交互，完成真机评测。

> 官方提供的 Client 脚本：[https://github.com/RoboChallenge/RoboChallengeInference/tree/table30_v2](https://github.com/RoboChallenge/RoboChallengeInference/tree/table30_v2)

⚠️ 注意：目前要用 `table30_v2` 分支

具体操作流程如下：

### 3.1 环境准备（本地 Client 部署）

请在预约的时间段前，提前拉取官方提供的 Inference 仓库，并完成本地运行环境的配置：

```bash
# 1. 克隆官方 Inference 仓库并进入目录
git clone https://github.com/RoboChallenge/RoboChallengeInference.git
cd RoboChallengeInference
git checkout table30_v2

# 2. (推荐) 创建并激活虚拟环境，避免污染全局 Python 环境
python -m venv venv
source venv/bin/activate  # Windows 环境请使用 venv\Scripts\activate

# 3. 安装所需依赖
pip install -r requirements.txt
```

### 3.2 推理逻辑适配

请参考仓库中的 `demo.py` 文件，**按需修改相关代码以适配您的自有模型**。重点完成以下关键操作：

- **自定义 Policy 类：** 继承 `DummyPolicy` 基类。在 `init` 方法中加载您的模型权重（通过 `checkpoint` 参数指定路径）；在 `run_policy` 方法中实现自定义的推理逻辑（如 GPU 加速的前向计算、特征数据处理等），特别提醒下处理 RC 返回时要考虑为空的情况，因为在部分情况下（紧急急停等）

**⚠️特别提醒：** 处理 RC 返回数据时，请务必增加**判空逻辑**。在紧急急停等特殊场景下，RC 可能会返回空值。

```python
class DummyPolicy:
    """
    Example policy class.
    Users should implement the __init__ and run_policy methods according to their own logic.
    """

    def __init__(self, checkpoint_path):
        """
        Initialize the policy.
        Args:
            checkpoint_path (str): Path to the model checkpoint file.
        """
        pass  # TODO: Load your model here using the checkpoint_path

    def run_policy(self, input_data, prompt=None):
        """
        Run inference using the policy/model.
        Args:
            input_data: Input data for inference.
            prompt (str, optional): Task prompt for the current run.
        Returns:
            list: Inference results.
        """
        # TODO: Implement your inference logic here (e.g., GPU model inference)
        return []
```

- **配置硬件匹配参数：** 根据目标测试机器人的硬件规范，严格调整以下参数：

  - `image_size`：对应机器人图像分辨率（默认 `[224, 224]`）。

  - `image_type`：对应所使用的摄像头类型（默认 `["high", "left_hand", "right_hand"]`）。

  - `action_type`：对应机器人的动作控制方式（如 `"joint"` 或 `"pos"`）。

  - `duration`：对应单次动作的执行时长（默认 `0.05` 秒）。

### 3.3 本地 Mock 测试（离线调试不记成绩）

在提交真机测试前，**强烈建议先通过本地 Mock 机器人服务验证推理逻辑的有效性与连通性。**

**步骤一：配置 Mock 参数** 编辑 `mock_server/mock_settings.py` 文件，设置与目标机型匹配的参数（注意：同一时间仅可激活一组配置）：

```python
# 示例：激活 Aloha 机器人配置（需从训练数据或赛事官网查询可用标签）
ROBOT_TAG = 'aloha'  # 可选值：aloha / arx5 / ur5 / w1
# 匹配机器人的本地测试数据路径（请确保路径与数据文件夹结构一致）
RECORD_DATA_DIR = '/path/to/your/recording/data/episode_000001'
```

**步骤二：启动 Mock 机器人服务** 新开一个终端窗口，启动本地数据服务：

```bash
# 启动本地 Mock 机器人服务（默认占用 9098 端口）
python3 mock_robot_server.py
```

**步骤三：执行测试脚本** 在原终端调用测试接口验证您的推理逻辑：

```bash
# 执行测试脚本，传入实际的模型权重文件路径
python3 test.py --checkpoint {您的模型权重文件路径}
```

运行后，`test.py` 将自动循环执行：获取 Mock 机器人的实时状态 ➔ 调用自定义逻辑生成动作指令 ➔ 下发指令 ➔ 输出推理耗时与动作日志。请根据控制台输出定位并修复代码问题。

### 3.4 提交评估请求

本地测试通过后，需在 RC 平台提交正式评测请求：

1. 登录 RoboChallenge 官方网站；

2. 进入「My Submissions」页面查看提交记录，点击【Detail】查看提交详情，并记录页面显示的 `SubmissionId`（后续正式推理需用到该 ID）。

### 3.5 执行正式推理任务

等待 RC 平台的任务分配通知，在已确认的预约时间段内执行以下操作：

1. 确保已完成修改的推理代码处于可运行状态；

2. 执行正式推理脚本，传入平台分配的核心参数：

```bash
python3 demo.py --user_token {你的用户令牌} --submission_id {3.4 中获取的 SubmissionId} --checkpoint {模型权重路径}
```

3. 任务执行过程中，程序会自动监听任务状态、获取真实机器人的实时状态、执行推理并下发动作；任务完成后程序会正常退出，若出现异常（如连接失败、推理报错），可通过官方渠道反馈（微信群）。

**⚠️ 注意：同一个 `submission_id` 只能启动一个 `demo.py`。**

### 3.6 查看测试结果

任务执行完成后，返回 RC 平台「My Submissions」页面，即可查看本次真机测试的详细结果，包括动作执行成功率、任务得分等核心指标。

## 四、资料和相关链接

为方便用户快速查找参加 RoboChallenge Table30 V2 所需的所有资源，我们会将各核心平台、开源代码库及联络渠道汇总如下，建议选手收藏备用：

### 4.1 官方平台

- **RoboChallenge 官网主页：** [https://robochallenge.cn/home](https://robochallenge.cn/home)

### 4.2 数据与代码仓库

- **官方训练数据集（HuggingFace）：** [https://huggingface.co/datasets/RoboChallenge/Table30v2](https://huggingface.co/datasets/RoboChallenge/Table30v2)

- **Table30 V2 技术报告：** [https://robochallenge.cn/robochallenge_techreport_V2.pdf](https://robochallenge.cn/robochallenge_techreport_V2.pdf)

- **官方推理 Client 脚本库（GitHub）：** [https://github.com/RoboChallenge/RoboChallengeInference/tree/table30_v2](https://github.com/RoboChallenge/RoboChallengeInference/tree/table30_v2)

- **30 个任务记分点说明（仅供参考，需以官方回复为准）：** [Table30 V2 任务介绍](https://dexmal-inc.feishu.cn/sheets/YghpsZ3a3hmBB3tHPQPcMiXUncg)

### 4.3 官方联系方式

- **官方报名邮箱：** [join-robochallenge@robochallenge.ai](mailto:join-robochallenge@robochallenge.ai)

- **运营助手微信**：添加时备注（Table30 V2 评测预约）

<p align="center">
  <img src="../assets/table30-v2-guide/10-wechat-contact.jpg" alt="Table30 V2 运营助手微信二维码" width="260">
</p>
