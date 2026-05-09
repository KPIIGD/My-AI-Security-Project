# Phase 6 Korean Preprocess 10k Comparison

Input: `PII/results/data/payloads_10k.json`

Preprocess: `PII/layer_0/KoreanNormalizer.normalize()` before model inference.

Metric: `target_hit_rate`; higher is better.

## Overall 10k

| Model | Before | After preprocess | Delta | After bypass | After any detection |
|---|---:|---:|---:|---:|---:|
| `alphagyuu` | 74.35% | 96.27% | +21.92%p | 3.73% | 100.00% |
| `mncai` | 62.94% | 80.97% | +18.03%p | 19.03% | 91.90% |
| `aegis` | 44.73% | 57.07% | +12.34%p | 42.93% | 73.58% |
| `piilot` | 28.61% | 42.85% | +14.24%p | 57.15% | 60.62% |
| `seungkukim` | 16.30% | 22.73% | +6.43%p | 77.27% | 70.18% |

## Korean all

| Model | Before | After preprocess | Delta | After bypass | After any detection |
|---|---:|---:|---:|---:|---:|
| `alphagyuu` | 80.39% | 94.33% | +13.94%p | 5.67% | 100.00% |
| `mncai` | 57.13% | 70.95% | +13.82%p | 29.05% | 87.62% |
| `aegis` | 27.81% | 34.10% | +6.29%p | 65.90% | 59.45% |
| `piilot` | 35.33% | 48.44% | +13.11%p | 51.56% | 75.73% |
| `seungkukim` | 23.26% | 31.57% | +8.31%p | 68.43% | 69.11% |

## Korean original L0

| Model | Before | After preprocess | Delta | After bypass | After any detection |
|---|---:|---:|---:|---:|---:|
| `alphagyuu` | 94.43% | 94.43% | +0.00%p | 5.57% | 100.00% |
| `mncai` | 71.85% | 72.14% | +0.29%p | 27.86% | 89.74% |
| `aegis` | 28.74% | 28.45% | -0.29%p | 71.55% | 55.13% |
| `piilot` | 46.63% | 46.63% | +0.00%p | 53.37% | 75.66% |
| `seungkukim` | 31.67% | 31.67% | +0.00%p | 68.33% | 71.26% |

## Korean mutated L1-L5

| Model | Before | After preprocess | Delta | After bypass | After any detection |
|---|---:|---:|---:|---:|---:|
| `alphagyuu` | 79.62% | 94.33% | +14.71%p | 5.67% | 100.00% |
| `mncai` | 56.32% | 70.88% | +14.56%p | 29.12% | 87.51% |
| `aegis` | 27.75% | 34.41% | +6.66%p | 65.59% | 59.69% |
| `piilot` | 34.71% | 48.54% | +13.83%p | 51.46% | 75.73% |
| `seungkukim` | 22.80% | 31.56% | +8.76%p | 68.44% | 68.99% |

## English all

| Model | Before | After preprocess | Delta | After bypass | After any detection |
|---|---:|---:|---:|---:|---:|
| `alphagyuu` | 63.06% | 99.89% | +36.83%p | 0.11% | 100.00% |
| `mncai` | 73.79% | 99.68% | +25.89%p | 0.32% | 99.89% |
| `aegis` | 76.34% | 99.97% | +23.63%p | 0.03% | 99.97% |
| `piilot` | 16.06% | 32.41% | +16.35%p | 67.59% | 32.41% |
| `seungkukim` | 3.30% | 6.22% | +2.92%p | 93.78% | 72.18% |

## Notes

- Korean preprocessing substantially improves target hits for every model.

- `alphagyuu` remains the strongest target-hit model, but its any-detection rate is 100%, so false positive analysis is still required.

- `aegis` is still the fastest path and improves meaningfully with preprocessing.

- The previous all-model run was slow because CPU execution ran TensorFlow, PyTorch, and ONNX models sequentially; rerunning only failed or changed models is faster.
