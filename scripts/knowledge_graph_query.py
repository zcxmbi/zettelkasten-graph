"""
知识图检索器 — 替代文件夹和 MOC 的图论检索工具

用法：
  python knowledge_graph_query.py 社区              → 列出所有社区
  python knowledge_graph_query.py 社区 <社区ID>     → 查看某个社区的笔记
  python knowledge_graph_query.py 核心              → PageRank top 核心笔记
  python knowledge_graph_query.py 邻居 <笔记名>     → 某个笔记的所有邻居（按权重排序）
  python knowledge_graph_query.py 路径 <A> <B>      → 两笔记间的最短路径
  python knowledge_graph_query.py 扩展 <笔记名> [跳数] → BFS N跳可达的所有笔记
  python knowledge_graph_query.py 桥接              → 介数中心性 top 桥接笔记
"""
import json, sys
from pathlib import Path
from collections import defaultdict

GRAPH = Path(os.environ.get("GRAPH_KASTEN_VAULT", ".")) / "knowledge_graph.json"


def load():
    with open(GRAPH, encoding="utf-8") as f:
        return json.load(f)


def show_communities(g):
    """列出所有社区"""
    communities = defaultdict(list)
    for name, node in g["nodes"].items():
        communities[node["community"]].append(name)
    
    print(f"\n🏘️ {len(communities)} 个社区\n")
    for cid in sorted(communities.keys(), key=lambda c: -len(communities[c])):
        members = sorted(communities[cid])
        folder = Path(g["nodes"][members[0]]["path"]).parent if members else "?"
        print(f"社区 {cid} ({len(members)} 笔记, 主要来源: {folder})")
        if len(members) <= 15:
            for m in members:
                pr = g["pagerank"].get(m, 0)
                print(f"  {pr:.4f}  {m}")
        else:
            for m in members[:10]:
                pr = g["pagerank"].get(m, 0)
                print(f"  {pr:.4f}  {m}")
            print(f"  ... 还有 {len(members)-10} 个")
        print()


def show_community(g, cid: int):
    """显示某个社区详情"""
    members = [(name, g["pagerank"].get(name, 0)) for name, node in g["nodes"].items() if node["community"] == cid]
    members.sort(key=lambda x: -x[1])
    if not members:
        print(f"社区 {cid} 不存在")
        return
    print(f"\n社区 {cid} ({len(members)} 笔记)\n")
    for name, pr in members:
        node = g["nodes"][name]
        print(f"  {pr:.4f}  {name}  [出{node['out_degree']}/入{node['in_degree']}]  {node['path']}")


def show_core(g, top_n: int = 20):
    """PageRank 核心笔记"""
    pr_sorted = sorted(g["pagerank"].items(), key=lambda x: -x[1])[:top_n]
    print(f"\n⭐ PageRank top {top_n}\n")
    for name, score in pr_sorted:
        node = g["nodes"][name]
        print(f"  {score:.4f}  {name}  [出{node['out_degree']}/入{node['in_degree']}]")


def show_neighbors(g, name: str):
    """某个笔记的邻居"""
    if name not in g["nodes"]:
        print(f"笔记「{name}」不存在")
        return
    
    # 出边（我引用的）
    out_edges = [(e["to"], e["weight"]) for e in g["edges"] if e["from"] == name]
    out_edges.sort(key=lambda x: -x[1])
    
    # 入边（引用我的）
    in_edges = [(e["from"], e["weight"]) for e in g["edges"] if e["to"] == name]
    in_edges.sort(key=lambda x: -x[1])
    
    print(f"\n🔗 {name}\n")
    if out_edges:
        print("  📤 引用 →")
        for target, w in out_edges:
            print(f"    {w:.2f}  [[{target}]]")
    if in_edges:
        print("  📥 被引用 ←")
        for source, w in in_edges:
            print(f"    {w:.2f}  [[{source}]]")
    
    if not out_edges and not in_edges:
        print("  (孤立节点)")


def show_path(g, a: str, b: str):
    """加权最短路径"""
    import heapq
    
    if a not in g["nodes"] or b not in g["nodes"]:
        print("笔记不存在")
        return
    
    # 构建邻接表（无向，权重转距离）
    adj = defaultdict(list)
    for e in g["edges"]:
        w = e["weight"]
        dist = 1.0 / max(w, 0.01)
        adj[e["from"]].append((e["to"], dist))
        adj[e["to"]].append((e["from"], dist))
    
    # Dijkstra
    dist = {a: 0}
    prev = {}
    pq = [(0, a)]
    
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist.get(u, float("inf")):
            continue
        if u == b:
            break
        for v, w in adj[u]:
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))
    
    if b not in prev:
        print(f"无路径：{a} 和 {b} 不在同一连通分量")
        return
    
    # 回溯路径
    path = []
    curr = b
    while curr != a:
        path.append(curr)
        curr = prev[curr]
    path.append(a)
    path.reverse()
    
    print(f"\n🛤️ {a} → {b}")
    print(f"  语义距离: {dist[b]:.2f}, {len(path)-1} 跳")
    print(f"  {' → '.join(path)}")


def show_bfs(g, name: str, hops: int = 2):
    """BFS N 跳扩展"""
    if name not in g["nodes"]:
        print(f"笔记「{name}」不存在")
        return
    
    adj = defaultdict(list)
    for e in g["edges"]:
        adj[e["from"]].append((e["to"], e["weight"]))
        adj[e["to"]].append((e["from"], e["weight"]))
    
    visited = {name: 0}
    queue = [(name, 0)]
    by_hop = defaultdict(list)
    
    while queue:
        u, d = queue.pop(0)
        if d >= hops:
            continue
        for v, w in adj[u]:
            if v not in visited:
                visited[v] = d + 1
                queue.append((v, d + 1))
                by_hop[d + 1].append((v, w))
    
    print(f"\n🔍 从 {name} 出发 {hops} 跳内可达\n")
    for hop in range(1, hops + 1):
        items = sorted(by_hop[hop], key=lambda x: -x[1])
        print(f"  {hop} 跳 ({len(items)} 个):")
        for v, w in items[:10]:
            pr = g["pagerank"].get(v, 0)
            print(f"    {w:.2f}  {v}  (PR {pr:.4f})")
        if len(items) > 10:
            print(f"    ... 还有 {len(items)-10} 个")
        print()


def show_bridges(g, top_n: int = 15):
    """介数中心性 top"""
    # 用入度+出度+PageRank 近似介数（JSON 里没有直接存介数）
    # 精确介数需要 networkx 重算，这里用出度×入度 做近似
    candidates = []
    for name, node in g["nodes"].items():
        score = node["out_degree"] * node["in_degree"]
        pr = g["pagerank"].get(name, 0)
        candidates.append((name, score, pr, node))
    candidates.sort(key=lambda x: -x[1])
    
    print(f"\n🌉 桥接笔记 Top {top_n} (出度×入度)\n")
    for name, score, pr, node in candidates[:top_n]:
        print(f"  {name}  [出{node['out_degree']}/入{node['in_degree']}]  PR {pr:.4f}")


def show_orphans(g):
    """孤立节点"""
    orphans = [name for name, node in g["nodes"].items() if node["out_degree"] == 0 and node["in_degree"] == 0]
    if orphans:
        print(f"\n🔴 孤立节点 ({len(orphans)}):")
        for name in orphans:
            print(f"  {name}")
    else:
        print("\n✅ 无孤立节点")


if __name__ == "__main__":
    g = load()
    
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "社区":
        if len(sys.argv) >= 3:
            show_community(g, int(sys.argv[2]))
        else:
            show_communities(g)
    elif cmd == "核心":
        n = int(sys.argv[2]) if len(sys.argv) >= 3 else 20
        show_core(g, n)
    elif cmd == "邻居":
        if len(sys.argv) < 3:
            print("用法: 邻居 <笔记名>")
        else:
            show_neighbors(g, sys.argv[2])
    elif cmd == "路径":
        if len(sys.argv) < 4:
            print("用法: 路径 <笔记A> <笔记B>")
        else:
            show_path(g, sys.argv[2], sys.argv[3])
    elif cmd == "扩展":
        if len(sys.argv) < 3:
            print("用法: 扩展 <笔记名> [跳数]")
        else:
            hops = int(sys.argv[3]) if len(sys.argv) >= 4 else 2
            show_bfs(g, sys.argv[2], hops)
    elif cmd == "桥接":
        n = int(sys.argv[2]) if len(sys.argv) >= 3 else 15
        show_bridges(g, n)
    elif cmd == "孤立":
        show_orphans(g)
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)
