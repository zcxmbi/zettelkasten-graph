# Quick Start

## 1. Install

```bash
git clone https://github.com/yourname/graph-kasten.git
cd graph-kasten
pip install -r requirements.txt
```

## 2. Prepare Your Notes

Put all your Markdown notes in one flat directory (no folders). Use the link syntax:

```markdown
# 场景 (Scene)

> The basic dynamic unit of story design.

## Definition

A scene is an action through conflict in a continuous time and space,
that turns a value-charged condition of a character's life.

## 相关笔记

- [[节拍]] 0.95 — 场景由节拍构成，是最小结构成分
- [[事件]] 0.9 — 理想的场景就是一个故事事件
- [[序列]] 0.85 — 若干场景构成一个序列
```

## 3. Set Your Vault Path

Edit `scripts/knowledge_graph_analyzer.py` line 14:

```python
VAULT = Path("/path/to/your/notes")
```

## 4. Build and Analyze

```bash
python scripts/knowledge_graph_analyzer.py
```

Outputs:
- Full 14-method analysis report
- `knowledge_graph.json` — the graph data

## 5. Query

```bash
python scripts/knowledge_graph_query.py core 10       # your most important notes
python scripts/knowledge_graph_query.py neighbors 场景  # what connects to 场景?
python scripts/knowledge_graph_query.py path 节拍 利益矛盾的建立  # how are they related?
python scripts/knowledge_graph_query.py expand 场景 2   # explore 2 hops from 场景
```

## Link Syntax Reference

```
[[target]]                 → weight 0.5, A→B
[[target]] 0.9             → weight 0.9
[[target]] 0.3 — notes     → weight + description
```

| Weight | Relationship | Example |
|:---|:---|:---|
| 0.7–0.9 | Structural / causal | 场景 contains 节拍 |
| 0.5–0.7 | Complementary principles | Two sides of the same idea |
| 0.3–0.5 | Combinable but not direct | Two techniques can be used together |
| 0.1–0.3 | Loose thematic link | Example → concept |
| 0.1 | Floor connection | Barely related, but not isolated |
