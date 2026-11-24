# 项目进度同步与 3 人开发分工简报

**项目**：Household Electricity Consumption Analysis（500 户欧洲智能家居 / 100,000 条记录）  
**时间线**：11/23–11/24 设计（已完成）→ 11/25–11/30 并行开发 → 12/01–12/02 测试与文档收口 → **12/03 最终演示（占 50%，缺席=0）**  
**技术栈**：Python + Streamlit + Pandas/NumPy + Matplotlib/Seaborn + Statsmodels/Scikit-learn + Pytest（存储用 5 张规范化 CSV）

---

## 一、目前已完成进度（A 阶段 + 数据底座已就绪）

| 阶段 | 已产出文件 | 说明 |
| :--- | :--- | :--- |
| **工程骨架** | `app.py`, `requirements.txt`, `.gitignore`, `README.md` | 统一依赖与目录结构 |
| **SRS 草稿与图** | `docs/SRS/SRS_requirements_draft.md`<br>`docs/SRS/SRS_documentation_slips.md`<br>`docs/diagrams/use_case_diagram.png` | 需求编号 `FR-01~08`、8 份用例卡、用例图已齐（第 5 章界面图等做完直接截图） |
| **SDD 设计图** | `docs/SDD/data_schema.md`<br>`docs/diagrams/class_diagram.png`<br>`docs/diagrams/database_diagram.png` | 5 张表结构与 UML 类图已定稿（**列名和类方法签名不要擅改**） |
| **SVVP 测试计划** | `docs/SVVP/SVVP_v0.1.md` | 18 条测试用例已写好，S12 实测填 `OK/KO` 即可 |
| **S6 数据层** | `src/models.py`<br>`src/data/repository.py` | 4 个实体类 + `CSVDataRepository`（含 `cp1252` 原样拆表 ETL + PK/FK 完整性校验） |

> **教授硬性要求（全员牢记）**：原始数据里的异常温度、矛盾季节等，在存储和可视化阶段**必须 100% 原样保留，不能删改**；**只有 AI 预测模块**在训练时可以对内存副本做清洗。

---

## 二、拿到代码后 2 分钟本地启动

```powershell
# 1. 拉取 main 分支并装依赖
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. 把原始 CSV 放到 data/raw/household_electricity_consumption.csv，运行一次 ETL 生成 5 张规范化 CSV
python -c "from pathlib import Path; from src.data.repository import CSVDataRepository; repo = CSVDataRepository(Path('data/processed')); print(repo.ingest_raw_csv(Path('data/raw/household_electricity_consumption.csv'))); print('Integrity OK:', repo.validate_referential_integrity())"
```
看到 `{'measurements': 100000, 'households': 500, 'appliances': 10}` 和 `Integrity OK: True` 即可开工。  
*(内置 3 个演示账号：`admin / admin123`、`user1 / user123` 绑 1 户、`user_multi / user123` 绑 3 户。)*

---

## 三、3 人分支与任务分工（文件完全隔离，零冲突）

### 成员 A：认证、权限与数据管理（分支 `feat/auth-admin`）
- **负责代码**：
  - `src/services/auth_service.py`：登录校验（调用 `User.verify_password`）、查询用户授权 `home_id` 列表、越权拦截。
  - `src/ui/login_view.py`：暴露 `render_login_view(auth_service)`，登录表单与退出按钮。
  - `src/ui/admin_view.py`：暴露 `render_admin_view(repo, user)`，仅 Admin 可见的数据重载与完整性检查页。
- **负责文档**：把 `docs/diagrams/` 的类图 + 数据库图 + `docs/SDD/data_schema.md` 组装进官方 **SDD Word**。
- **演示负责（第 1 分钟）**：5 表数据架构、Admin vs User 登录权限隔离与越权拦截。

### 成员 B：可视化分析与主界面集成（分支 `feat/analytics-ui`）
- **负责代码**：
  - `src/services/analytics_service.py`：按 `home_id` 与电器过滤、日/月/年聚合、全网 500 户均线计算、KPI 统计。
  - `src/ui/dashboard_view.py`：暴露 `render_dashboard_view(analytics_service, user, authorized_homes)`，默认按日折线图、切换月/年、最多 5 户同图不同色对比、叠加全网均线、10 类电器勾选过滤（支持排除冰箱）。
  - `app.py`：主路由与 Tab 拼接（把 A 和 C 的 view 接进来）。
- **负责文档**：组装官方 **SRS Word**，并把做好的登录页和仪表盘截图贴进第 5 章。
- **演示负责（第 2 分钟）**：主仪表盘全流程实操（日→月/年、5 户对比、全网均线、排除冰箱）。

### 成员 C：AI 预测、Bonus 导出与测试验收（分支 `feat/ai-export`）
- **负责代码**：
  - `src/services/prediction_service.py` & `src/ui/prediction_view.py`：暴露 `render_prediction_view(prediction_service, user, authorized_homes)`；**仅在内部内存副本清洗**，训练 Statsmodels OLS + Scikit-learn 双模型，如实展示预测值与 R²/MAE/RMSE（说明天气信号弱）。
  - `src/services/export_service.py` & `src/ui/export_view.py`：暴露 `render_export_view(export_service, user, authorized_homes)`；生成月/年汇总表（总能耗 + 人均能耗）并支持下载 CSV。
  - `tests/`：编写 `pytest` 单元测试覆盖核心 Service。
- **负责文档**：逐条跑完 `docs/SVVP/SVVP_v0.1.md` 的 18 条用例，填实 `OK/KO` 与通过率，组装官方 **SVVP Word**。
- **演示负责（第 3 分钟）**：AI 预测与数据洞察、Bonus 报表导出、Pytest & SVVP 验收结果。

> **个人报告（占 25% 个人分）**：3 人各自独立提交，直接围绕自己负责的分支模块写即可。

---

## 四、协作约定（3 条）
1. **编码规范**：全英文代码注释与 docstring，遵循 PEP 8，单个函数尽量 < 50 行。
2. **各自独立测试**：每个 `*_view.py` 可先在本地单独跑通，A 和 C 先合并到 `main`，B 最后在 `app.py` 统一联调。
3. **每日同步**：每晚拉一次 `main` 跑 `streamlit run app.py` + `pytest`，确保随时可演示。
