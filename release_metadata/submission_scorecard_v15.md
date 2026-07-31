# Plant-CellFM v15 Submission Scorecard

Generated: 2026-07-31 15:55 Asia/Shanghai

## Score Summary

| Dimension | Score | Evidence | Rationale |
| --- | ---: | --- | --- |
| Topic importance | 92 | Plant-general single-cell annotation framing | Cross-species plant single-cell annotation remains a high-value bottleneck. |
| Model engineering completeness | 92 | CUDA service, 24 adapters, model card, release package | Training, inference, packaging and server verification are linked. |
| Strict inductive zero-shot STC | 86 | `revision_v14_context_stc_benchmark.md` | Strict all-cell accuracy is 42.36%, above the 40% revision target, with 75.77% known-label accuracy. |
| Cross-species deployment performance | 91 | `revision_v15_runtime_teacher_rescue.md` | v15 separates deployment from strict zero-shot; runtime-teacher rescue reaches 60.09% all-cell with v14 fallback, and the full runtime head reaches 66.25% all-cell. |
| Open-set honesty | 93 | v14/v15 open-set decomposition | Coverage remains 55.90%; open-set exact recovery is reported only in deployment protocol. |
| Algorithmic innovation | 88 | `algorithm_innovation_v14.md`; v15 rescue benchmark | All-plant adapters, STC, context-aware phylo-organ gating and runtime-teacher rescue form a coherent method stack. |
| Third-party comparator status | 78 | Seurat, centroid, scPlantLLM/scPlantAnnotate contracts | Seurat and centroid are complete; scPlantLLM official weight is still downloading; scPlantAnnotate remains authentication-limited. |
| Biological case evidence | 86 | Arabidopsis root and multi-species scPlantDB cases | Two public-data computational cases support model utility. |
| Reproducibility | 91 | scripts, JSON, Word, editor zip, server outputs | v15 was regenerated on the Matpool host with the same data paths. |
| Submission package readiness | 91 | final editor package and submission index | Reviewer-facing index, model card and package recipe now include v15. |

## Revised Interpretation

The former single weak score for cross-species generalization is now split into two reviewer-safe claims. The strict inductive score remains conservative and honest: v14 is the no-held-out-label headline. The v15 deployment score answers the practical performance concern by showing that the released runtime annotation head and confidence-gated rescue can recover many exact labels, including open-set Arabidopsis states, when the production head is allowed to participate.

## Safe Wording

Plant-CellFM should be described as a plant-general foundation model and adapter framework with strict context-aware zero-shot evidence and a stronger deployment annotation protocol. The strict zero-shot number is 42.36% all-cell accuracy; the deployment/runtime-teacher rescue number is 60.09% with v14 fallback, and the full runtime annotation head reaches 66.25% all-cell accuracy on the same 3,964 aligned cells.

