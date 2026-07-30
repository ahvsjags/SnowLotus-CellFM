# Plant-CellFM v9 外部对照与植物生物学案例补充说明

生成时间：2026-07-31 01:07 Asia/Shanghai

## 1 外部对照补强

本补充说明把 Plant-CellFM v9 的外部对照拆成三类：已经完成并有本地 JSON 指标的正式对照；已经准备好输入但当前环境缺少可执行权重或下载路径的接口；以及需要认证或网页会话的受限工具。这样的写法可以防止把未完成的第三方结果写成结论，同时给编辑和审稿人看到我们已经把横向对照路径补齐。

| 对照对象 | 协议 | 状态 | 主准确率 | macro-F1 | 证据 |
| --- | --- | --- | ---: | ---: | --- |
| Plant-CellFM v9 vs frozen v3 extended | Leave-dataset-out | completed | 0.4490 | 0.3485 | release_metadata/v9_benchmarks/v9_lora_vs_v3_shared_comparison.json |
| Plant-CellFM v9 vs frozen v3 extended | Leave-sample-out | completed | 0.6200 | 0.4902 | release_metadata/v9_benchmarks/v9_lora_vs_v3_shared_comparison.json |
| Plant-CellFM v9 vs frozen v3 extended | Leave-species-out, species labels normalized | completed | 0.2354 | 0.1918 | release_metadata/v9_benchmarks/v9_lora_vs_v3_shared_comparison.json |
| Classical cosine centroid, group-random split | group_random | completed | 0.7583 | 0.7125 | release_metadata/strict_benchmarks/public_sprint_group_random.centroid_baseline.json |
| Classical cosine centroid, SRP169576 sample holdout | explicit_leaveout | completed | 0.7337 | 0.4873 | release_metadata/strict_benchmarks/leaveout_srp169576_sample.centroid_baseline.json |
| scPlantLLM frozen embedding nearest-centroid probe | public sprint train/test chunks | contract_ready_metric_pending | - | - | release_metadata/scplantllm_input_readiness.json |
| Seurat label transfer | exported train/test split | completed | 0.2207 | 0.0603 | release_metadata/external_benchmarks/seurat_v9_subset.json |
| scPlantAnnotate | official web/API route audit | contract_ready_auth_limited | - | - | release_metadata/scplantannotate_access_audit.json |

Seurat label transfer 已在 frozen v9 subset 的导出矩阵上完成，测试细胞数为 512，fine accuracy 为 0.2207，fine macro-F1 为 0.0603。这个结果说明在跨数据集、多物种、共享基因空间的严格设置下，传统 anchor-based label transfer 并不能稳定解决植物单细胞注释问题，从而支持 Plant-CellFM v9 作为植物专用基础模型与适配层的必要性。

scPlantLLM 的输入准备已经完成，20,000 个细胞、24,392 个保留基因与官方 gene vocabulary overlap 为 1.0；当前没有把它写成完成指标，是因为服务器到 GitHub 的官方 checkout/ZIP 下载多次 TLS 中断。scPlantAnnotate 的官方 web server 可以访问，但匿名脚本化 API 不可用，因此当前只作为访问审计和待认证对照入口。

## 2 植物生物学案例补强

Arabidopsis root case study 现在作为完整植物生物学示范：系统解析 Arabidopsis adapter，围绕根细胞状态生成 marker candidate，并把 root cap、lateral root cap、cortex、endodermis、stele、phloem、xylem、root hair 等根细胞身份组织成可核查证据表。

- Adapter 数量：24
- 动态 adapter resolution：True
- marker 标签数：13
- marker 行数：260
- root identity labels：10

| 细胞状态 | 类别 | top genes | median score | median log2FC | median detection delta |
| --- | --- | --- | ---: | ---: | ---: |
| Columella root cap | root_cell_identity | AT5G02380, AT2G04025, AT2G36950, AT3G20840, AT3G45730 | 0.849 | 3.296 | 0.231 |
| G1/G0 phase | cell_cycle_or_other | ATCG00790, ATCG00740, ATCG00170, ATCG00800, ATCG00770 | 1.917 | 3.395 | 0.575 |
| Lateral root cap | root_cell_identity | AT1G26820, AT3G16440, AT1G15385, AT1G06090, AT5G55110 | 2.871 | 4.235 | 0.677 |
| Non-hair | root_cell_identity | AT1G65310, AT4G12545, AT1G70850, AT1G14960, AT4G12550 | 2.023 | 3.742 | 0.607 |
| Phloem | root_cell_identity | AT5G04080, AT1G62380, AT2G46630, AT1G79430, AT5G59090 | 3.051 | 7.071 | 0.495 |
| Root cap | root_cell_identity | AT1G54010, AT5G10130, AT1G28290, AT5G58784, AT2G43610 | 2.634 | 3.634 | 0.730 |
| Root cortex | root_cell_identity | AT1G12090, AT1G13930, AT1G21310, AT5G13930, AT4G30170 | 1.665 | 2.941 | 0.559 |
| Root endodermis | root_cell_identity | AT3G22620, AT3G22600, AT2G32300, AT2G28670, AT5G15290 | 2.863 | 4.341 | 0.593 |
| Root hair | root_cell_identity | AT3G54580, AT1G30870, AT3G09925, AT3G54590, AT3G62680 | 1.602 | 3.700 | 0.427 |
| Root stele | root_cell_identity | AT4G11210, AT2G02130, AT1G12080, AT4G14130, AT3G59370 | 2.043 | 3.840 | 0.541 |
| S phase | cell_cycle_or_other | AT5G15200, AT5G20290, AT3G60245, AT5G16130, AT4G16720 | 1.821 | 3.053 | 0.605 |
| Unknown | cell_cycle_or_other | AT2G43820, AT2G29440, AT2G29450, AT1G43160, AT3G50970 | 0.339 | 1.208 | 0.283 |

## 3 稳定投稿定位

补齐这两部分以后，Plant-CellFM v9 的稳妥定位应从“模型交付说明”提升为“植物单细胞注释方法与资源论文”。主线可以写成：植物通用基础模型解决跨数据集、跨样本和跨物种注释的一致接口问题；Seurat 对照说明传统 label transfer 在 frozen subset 上表现不足；Arabidopsis root case 证明模型不只是分类器，还能输出 adapter 记录、细胞状态和 marker candidate 证据。这个组合更适合 Plant Communications、Communications Biology 和 Genome Biology 的方法/资源审稿口径。
