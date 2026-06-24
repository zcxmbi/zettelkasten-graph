# Quick Start

## For AI Agents

If you are an AI setting up agent-note-graph for a user, follow these steps:

1. **Ask the user** where their Markdown notes live (flat directory, no subfolders):

   > "Where are your Markdown notes stored? I need the absolute path to the directory."

2. **Configure the vault path** by writing `.env` in the scripts directory:

   ```bash
   echo "GRAPH_KASTEN_VAULT=/absolute/path/to/notes" > scripts/.env
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Verify** the setup works:

   ```bash
   python scripts/knowledge_graph_analyzer.py
   ```

   This will scan all `.md` files, build the graph, run all 14 analyses, and generate `knowledge_graph.json` in the vault directory.

5. **Report** the summary to the user — node count, edge count, connectivity %, ghost links.

## For Humans

### 1. Clone and Install

```bash
git clone https://github.com/yourname/agent-note-graph.git
cd agent-note-graph
pip install -r requirements.txt
```

### 2. Configure

Copy the example env file and set your notes directory:

```bash
cp .env.example .env
# Edit .env: GRAPH_KASTEN_VAULT=/path/to/your/notes
```

Or export the environment variable:

```bash
export GRAPH_KASTEN_VAULT=/path/to/your/notes
```

### 3. Prepare Your Notes

All notes must be in one flat directory. Use the weighted link syntax:

```markdown
# Scene

> The basic dynamic unit of story design.

## 相关笔记

- [[节拍]] 0.95 — scene is composed of beats
- [[事件]] 0.9 — an ideal scene is a story event
```

### 4. Build and Analyze

```bash
python scripts/knowledge_graph_analyzer.py
```

### 5. Query

```bash
python scripts/knowledge_graph_query.py core 10       # top 10 most important
python scripts/knowledge_graph_query.py neighbors 场景  # what links to 场景?
python scripts/knowledge_graph_query.py path 节拍 利益矛盾的建立  # how are they related?
python scripts/knowledge_graph_query.py expand 场景 2   # explore 2 hops from 场景
python scripts/knowledge_graph_query.py community     # natural clusters
```

## Link Syntax

```
[[target]]                 → weight 0.5, A→B
[[target]] 0.9             → weight 0.9
[[target]] 0.3 — notes     → weight + description
```

| Weight | Relationship |
|:---|:---|
| 0.7–0.9 | Structural / causal |
| 0.5–0.7 | Complementary principles |
| 0.3–0.5 | Combinable techniques |
| 0.1–0.3 | Loose thematic link |
