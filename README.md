# zettelkasten-graph

> Zettelkasten + Agent + Graph Theory. A knowledge base built by you and AI, together.

AI links your notes. Graph theory audits the AI. An LLM distills its trillion-parameter judgment into your personal knowledge weights. Treat your notes like a social network — rank, navigate, discover hidden clusters.

## The Core Insight — Personal Distillation of LLM Companies' Billions

You can't download GPT-4's weights. But you **can** extract its knowledge.

Every Zettelkasten note encodes a piece of understanding. Every weighted link encodes a judgment about how close two concepts are. This is exactly the same structure as a neural network's attention mechanism — concepts with weighted edges.

**zettelkasten-graph** turns this similarity into a pipeline:

1. You write notes + links (your personal knowledge graph)
2. LLM reads each node's outgoing links and redistributes attention → the LLM becomes your **teacher model**
3. Compare: your weights vs LLM's attention distribution → surface deviations
4. You decide: trust the teacher or your own intuition

This is **knowledge distillation at the individual level**. Every note you write, every link you set, is distilled from the models that cost billions to train. Your graph gets better with every run. And when a more powerful model ships tomorrow — re-run the pipeline. The graph stays, the teacher upgrades.

```
# Distill a single node
python scripts/distill_attention.py "note-name"

# Dry run (see the prompt without API call)
python scripts/distill_attention.py "note-name" --dry-run
```

## The Problem

Traditional Zettelkasten uses folders, MOCs (Maps of Content), and flat `[[links]]`. This leads to:
- Folders impose artificial hierarchies
- MOCs become "super-hubs" that distort the network
- No way to quantify which notes are truly important
- No way to detect knowledge gaps or overloaded concepts
- No external signal to validate whether your link weights are right

## The Solution — 14 Graph Analysis Methods

| # | Method | What it does |
|:---|:---|:---|
| 1 | **Core Ranking** (PageRank) | Which notes are globally most important |
| 2 | **Bridge Detection** (Betweenness) | Which notes connect different knowledge domains |
| 3 | **Natural Groups** (Louvain) | How knowledge naturally clusters into topics |
| 4 | **Concept Path** (Dijkstra) | Optimal path between any two ideas |
| 5 | **Link Suggestions** (Jaccard/Adamic-Adar) | Notes that should be connected |
| 6 | **Link Quality Review** | Detect asymmetry, transitivity gaps, weight deviation |
| 7 | **Split Suggestions** (Overload Detection) | Concepts doing too much work |
| 8 | **Gap Locator** (Missing Node Prediction) | Where a new concept is needed |
| 9 | **Role Split** (HITS) | Hub (navigator) vs Authority (foundation) |
| 10 | **Knowledge Core** (K-core) | Hardcore concepts after peeling surface layers |
| 11 | **Best Entry Point** (Closeness) | Fastest path to all knowledge |
| 12 | **Local Density** (Clustering Coefficient) | Which knowledge areas are tightly linked |
| 13 | **Break Point Detection** (Articulation Points) | Nodes that would fragment the graph if removed |
| 14 | **Knowledge Span** (Diameter) | How wide is your knowledge network |

## Link Syntax

Fully compatible with Obsidian's `[[wikilink]]` syntax, with weight annotation as a natural extension.

```markdown
[[target]]                 → default weight 0.5, directed edge A→B
[[target]] 0.9             → weight 0.9 (intimacy, 0.01–1.0)
[[target]] 0.3 — describes → weight + description
```

Direction: writing `[[B]]` in note A creates edge A→B. If B also writes `[[A]]`, it's reciprocal.

## Usage

### Install

```bash
pip install -r requirements.txt
```

Configure `scripts/.env`:

```
GRAPH_KASTEN_VAULT=/path/to/your/notes
ATTENTION_API_KEY=sk-your-key
```

### Analyze

```bash
python scripts/knowledge_graph_analyzer.py
```

### Query

```bash
python scripts/knowledge_graph_query.py community     # list all communities
python scripts/knowledge_graph_query.py core 10       # top 10 by PageRank
python scripts/knowledge_graph_query.py neighbors X   # neighbors of a note
python scripts/knowledge_graph_query.py path A B      # shortest path between concepts
python scripts/knowledge_graph_query.py expand X 2    # BFS 2 hops from a note
python scripts/knowledge_graph_query.py bridges       # bridge notes (betweenness)
```

### Distill

```bash
python scripts/distill_attention.py "note-name"
```

## Principles

1. **No Folders.** All notes flat in one directory. The graph is the only structure.
2. **No MOCs.** Index files are artificial super-hubs that distort metrics.
3. **Weight Every Link.** Not all connections are equal. Use 0.01–1.0.
4. **Graph-Driven Confidence.** Low confidence + high graph validation → raise it.
5. **Zero Ghost Links.** Never link to non-existent notes. Use `## 待探索` for planned notes.

## License

MIT
