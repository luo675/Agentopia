---
title: Agentopia — 项目入口
type: project-readme
created: 2026-06-22
updated: 2026-06-28
---

# Agentopia 小模型长期社会模拟研究

> 在 RTX 5070 Ti 笔记本上复现并改进 Agentopia 论文——8B 模型能否涌现社会行为？

## 一句话

基线实验 ✅                       代码改进 🔄
T1-T5 + T3A + T3B-T4 全部完成    ③✅ ④✅ ⑤🔄
根因已确认（Prompt 诱导）          下步：⑤ R3 运行中

## 源论文

**Agentopia: Long-Term Life Simulation and Learning in Agent Societies**
arXiv: 2606.07513v1 (2026-06-05)，复旦 & 米哈游 AI。100 个 AI 角色自主生活 10 年。

## 当前状态（2026-07-03）

```
基线实验 ✅                       代码改进 ✅
T1-T5 + T3A + T3B-T4 全部完成    ③✅ ④✅ ⑤✅
根因已确认（Prompt 诱导）          下步：T6 → 论文
```

## 核心文档

| 文档 | 用途 |
|------|------|
| [研究方案.md](研究方案.md) | 实验设计、贡献线、已有发现 |
| [环境搭建.md](环境搭建.md) | WSL2 + vLLM + Qwen3-8B 部署 |
| [故障记录.md](故障记录.md) | 17 个环境故障及修复方案 |
| [代码改进计划.md](代码改进计划.md) | 三轮迭代实施方案（③→④→⑤） |
| [待办清单.md](待办清单.md) | 当前待办 + 进度追踪 |
| [讨论记录.md](讨论记录.md) | 历史讨论对话记录 |
| [论文/写作脉络.md](论文/写作脉络.md) | 论文章节大纲 |

## 创新点储备

| 文档 | 简述 |
|------|------|
| [创新点/24小时细粒度时间.md](创新点/24小时细粒度时间.md) | 每天 4 时段 × 自主作息 |
| [创新点/懒激活机制.md](创新点/懒激活机制.md) | 按需唤醒 agent，消费级友好 |

## 硬件

RTX 5070 Ti 12GB + WSL2 Ubuntu 22.04 + vLLM 0.19.1 + Qwen3-8B AWQ 4-bit

## 快速启动

```bash
# WSL2 终端1: 启动 vLLM
cd ~/agentopia && source .venv/bin/activate
vllm serve ~/models/Qwen3-8B-AWQ --served-model-name Qwen/Qwen3-8B-AWQ \
  --port 8000 --gpu-memory-utilization 0.85 --max-model-len 20480 \
  --enable-auto-tool-choice --tool-call-parser hermes

# WSL2 终端2: 跑实验
cd ~/agentopia && source .venv/bin/activate
python scripts/run_world.py --max-agents 3 --years 1 --weeks 10 --no-parallel
```