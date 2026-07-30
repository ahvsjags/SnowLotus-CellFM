# Plant-CellFM v9：面向全植物单细胞注释的基础模型与多植物适配层

本文件原为 SnowLotus-CellFM v0_12 中文稿。为避免旧稿继续使用“天山雪莲中心”口径，本文件已改为新版稿件索引。

当前推荐提交稿：[`manuscript/Plant_CellFM_v9_plant_general_submission_zh.md`](Plant_CellFM_v9_plant_general_submission_zh.md)

新版稿件采用以下口径：

- 模型定位为 Plant-CellFM v9 植物通用基础模型，不是天山雪莲专用模型。
- 天山雪莲是目标物种适配场景之一，和其他植物一样通过 h5ad contract、同源基因映射和 adapter 接口接入。
- 留物种 benchmark 已修正为物种名归一化口径，将 `Arabidopsis_thaliana` 与 `Arabidopsis thaliana` 作为同一物种组评估。
- 归一化留物种主指标为 23.54% all-cell accuracy、55.90% coverage、42.10% known-label conditional accuracy 和 0.1918 known-label macro-F1。
- v9 在同一 shared-gene benchmark 上优于 v3 extended baseline：leave-dataset +24.70 percentage points，leave-sample +20.45 percentage points，normalized leave-species +4.41 percentage points。

GitHub Release：https://github.com/ahvsjags/SnowLotus-CellFM/releases/tag/v0.9.0-plant-general-lora

Checkpoint SHA256：`9a98dbc799c062981c1dd895034300b7385e1ecddad88d8d98cff5d1c6962c93`
