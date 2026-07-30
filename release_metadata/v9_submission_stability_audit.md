# Plant-CellFM v9 Submission Stability Audit

| Risk | Mitigation | Safe claim | Evidence |
| --- | --- | --- | --- |
| 跨物种泛化指标被质疑偏低 | 主文将留物种结果写成开放集迁移证据，而不是全部植物满覆盖断言；同时报告 all-cell accuracy、coverage 和 known-label conditional metrics。 | Plant-CellFM v9 在同一 shared-gene benchmark 上稳定优于 v3 extended baseline，并提供可复现的全植物适配框架。 | release_metadata/v9_benchmarks/v9_lora_vs_v3_shared_comparison.json |
| 第三方横向对照不完整 | Seurat 作为完成的传统外部基线进入主表；scPlantLLM 和 scPlantAnnotate 只按输入就绪/认证受限状态陈述。 | 当前版本完成了 v3、centroid 和 Seurat 对照，并公开保留 scPlantLLM/scPlantAnnotate 的可复现入口。 | release_metadata/external_benchmark_panel_v9.json |
| 生物学案例被认为只是计算输出 | 把 Arabidopsis root 写成 public-data computational case，强调 adapter resolution、层级注释和 marker candidate mining 的完整链路。 | Arabidopsis root case 证明模型不仅输出标签，也能产生可审计 adapter 记录和根细胞身份 marker 候选。 | release_metadata/plant_biology_case_study_v9.json |
| 雪莲定位被误读为图谱成果 | 主文明确 Snow Lotus 是目标物种接入口和应用场景，当前不写作已发布细胞图谱成果。 | Snow Lotus-ready transfer is supported once a reusable Snow Lotus single-cell matrix is supplied under the h5ad contract. | release_metadata/saussurea_h5ad_contract.md |
| 代码版本和 GitHub 展示不同步 | 主文写入 GitHub release、服务器发布包和 SHA256 校验状态；GitHub auth 未恢复前不声称最新 commit 已推送。 | The integrated manuscript is version-controlled in the repository; the current commit should be read from git log -1 or the final handoff note. | GITHUB_PUSH_INSTRUCTIONS.md |
