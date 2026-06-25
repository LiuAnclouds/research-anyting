# /mr — Moon-Research Command Reference

All commands use the `/mr` prefix. This prevents conflicts with other Claude Code plugins.

## Domain Research

```
/mr gnn <cmd>              GNN 图神经网络研究
/mr vla-vlm <cmd>          VLA-VLM 多模态+具身智能
/mr vla <cmd>              VLA 子域
/mr vlm <cmd>              VLM 子域
/mr <domain> <cmd>         用户创建领域 (via /mr new-domain)
```

每个领域的 `<cmd>`:
```
idea "topic"                生成研究方向
survey "topic"              系统文献调研 (15+来源)
read <paper>                深度论文精读
theory                      数学推导+算法设计
prototype "approach"        快速可行性验证 (1-2天)
experiment [--monitor]      完整实验 (--monitor 实时监控)
analyze <results>           根因分析+叙事构建
verify                      独立验证所有声称
review <manuscript>         4角色预审稿
explore "topic"             探索三件套 (idea→survey→read)
full "hypothesis"           完整9Agent流水线
auto "topic"                自主全流程
```

## Autonomous Pipeline

```
/mr auto "topic"                       全自主6阶段管线
/mr auto "topic" --human-gates         关键节点人工审批
/mr auto "topic" --stop-at <phase>     运行到指定阶段
/mr auto "topic" --target <tier>       按CCF等级校准
/mr auto "topic" --dry-run             预演不执行
/mr auto status                        查看当前进度
/mr auto resume                        从断点恢复
```

## Literature & Discovery

```
/mr search "query"                     跨KB统一搜索
/mr papers [--domain] [--tier]         论文库浏览
/mr paper <slug>                       论文详情+模块分解
/mr modules [--domain] [--category]    模块库浏览
/mr module <slug>                      模块详情+可组合性
/mr alert                              最新文献监控
```

## Idea Management

```
/mr ideas [--domain] [--status]        全部Idea列表
/mr idea <slug>                        Idea详情 (模块+论文+期刊)
/mr idea promote <slug>                孵育→活跃
/mr idea discard <slug>                放弃+记录原因
/mr combinations                       重新计算K-way超图
/mr decompose <paper>                  论文→模块分解
```

## Construction

```
/mr code-gen                           理论→可执行代码
/mr hyperopt                           系统化超参调优
/mr preprocess                         数据准备+标准化
```

## Debugging

```
/mr debug                              实验失败根因诊断
/mr monitor                            训练实时监控
```

## Venue & Submission

```
/mr venues [--tier] [--domain]         期刊数据库浏览
/mr venue <slug>                       期刊详情+投稿要求
/mr recommend-venue <idea>             为Idea推荐目标期刊
```

## Writing

```
/mr write "section" → "venue"          分节生成论文
/mr rebuttal <reviews>                 逐条审稿回复
/mr present                            生成答辩/组会PPT
```

## Discussion

```
/mr discuss "question"                 导师/同行/质疑者三角色
```

## Knowledge Base

```
/mr store session info                 手动持久化当前session
/mr auto-store on|off                  自动持久化开关
/mr recall "query"                     从KB恢复上下文
/mr kb-check                           KB完整性验证
/mr fuse                               KB条目合并去重
```

## Management

```
/mr new-domain <name> "<desc>"         创建新研究领域
/mr status [--domain]                  管线概览
/mr log                                科研日志
/mr export idea|bib <target>           导出数据
/mr help                               显示此命令参考
```

## Quick Examples

```bash
# 探索方向
/mr gnn idea "dynamic graph anomaly detection"

# 系统调研
/mr gnn survey "heterophilic GNN 2022-2025"

# 一键全流程
/mr auto "heterophily-aware dynamic graph anomaly detection"

# 跨session恢复
/mr auto-store on
/mr recall "active GNN hypotheses"

# 创建新领域
/mr new-domain nlp "NLP with Large Language Models"
/mr nlp idea "efficient fine-tuning"
```