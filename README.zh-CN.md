# agent-note-graph

> Zettelkasten 遇上图论。为原子笔记打造的加权知识图分析工具。

用数学知识图替代文件夹和 MOC。每篇笔记是一个节点，每条 `[[链接]]` 是一条加权边。运行网络分析，发现你思维中隐藏的结构。

## 解决的问题

传统 Zettelkasten 用文件夹、MOC 和平面的 `[[链接]]`。这导致：
- 文件夹强加了人为层级
- MOC 成为"超级枢纽"，扭曲网络指标
- 无法量化哪些笔记真正重要
- 无法检测知识空白或过载概念

## 解决方案 — 14 种图分析方法

| # | 方法 | 做什么 |
|:---|:---|:---|
| 1 | **核心排序** (PageRank) | 哪些笔记全局最重要 |
| 2 | **桥梁检测** (介数中心性) | 哪些笔记连接不同知识域 |
| 3 | **自然分组** (Louvain) | 知识如何自然聚成主题 |
| 4 | **概念路径** (Dijkstra) | 任意两个概念之间的最优路径 |
| 5 | **补链推荐** (Jaccard/Adamic-Adar) | 哪些笔记应该连接 |
| 6 | **链接质量审查** | 哪些边破坏了结构一致性 |
| 7 | **拆分建议** (过载检测) | 哪个笔记承载了过多概念 |
| 8 | **空白定位** (缺失节点预测) | 哪里需要一个新概念 |
| 9 | **角色区分** (HITS) | Hub（导航者）vs Authority（基石） |
| 10 | **知识内核** (K-core) | 剥掉表层后剩下的硬核概念 |
| 11 | **最佳起点** (紧密度) | 从哪里出发最快到达全部知识 |
| 12 | **区域密度** (聚类系数) | 哪些知识区域链接扎实 |
| 13 | **断点检测** (割点) | 移除哪些节点图会断裂 |
| 14 | **知识宽度** (直径) | 你的知识网络有多宽广 |

## 链接语法

```markdown
[[目标]]                 → 默认权重 0.5，有向边 A→B
[[目标]] 0.9             → 权重 0.9（亲密度，0.01–1.0）
[[目标]] 0.3 — 描述      → 权重 + 描述
```

方向：在笔记 A 中写 `[[B]]` = A→B。若 B 也写了 `[[A]]`，则形成双向边。

## 使用方法

### AI Agent 安装

如果你是 AI，为用户设置 agent-note-graph：

1. 询问用户的笔记目录路径
2. `echo "GRAPH_KASTEN_VAULT=/路径" > scripts/.env`
3. `pip install -r requirements.txt`
4. `python scripts/knowledge_graph_analyzer.py`
5. 向用户报告：节点数、边数、连通率、断链数

### 人类安装

```bash
git clone https://github.com/yourname/agent-note-graph.git
cd agent-note-graph
pip install -r requirements.txt
cp scripts/.env.example scripts/.env
# 编辑 scripts/.env 设置笔记路径
```

### 分析

```bash
python scripts/knowledge_graph_analyzer.py
```

### 查询

```bash
python scripts/knowledge_graph_query.py 核心 10       # 最重要的 10 篇
python scripts/knowledge_graph_query.py 邻居 场景      # 场景的入链/出链
python scripts/knowledge_graph_query.py 路径 A B      # 两概念间最短路径
python scripts/knowledge_graph_query.py 扩展 场景 2    # 从场景出发 2 跳
python scripts/knowledge_graph_query.py 社区          # 自然聚类
```

## 原则

1. **不要文件夹。** 所有笔记扁平放在一个目录。图是唯一的组织结构。
2. **不要 MOC。** 索引文件是人造的超级枢纽，会扭曲指标。
3. **每条链接加权。** 不是所有连接都一样。使用 0.01–1.0。
4. **图驱动置信度。** 低自信 + 高图验证 → 调高置信度。
5. **图驱动记忆晋升。** 入度 ≥ 7 + 3 个以上社区 + PR ≥ 0.01 → 活跃记忆。
6. **零幽灵链接。** 绝不链接不存在的笔记。待建笔记用 `## 待探索` 纯文本记录。

## 许可证

MIT
