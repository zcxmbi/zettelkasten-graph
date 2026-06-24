"""
知识体系图论分析器 v2
- 解析 [[目标]] [权重] 语法
- 构建加权有向图
- 输出 knowledge_graph.json 供总检索
"""
import os, re, json, sys, random
from pathlib import Path
from collections import defaultdict
import networkx as nx

# === 配置 ===
VAULT = Path(os.environ.get("GRAPH_KASTEN_VAULT", "."))
OUTPUT_JSON = VAULT / "knowledge_graph.json"
EXCLUDE_DIRS = {".git", ".obsidian", ".trash"}
DEFAULT_WEIGHT = 0.5

# === 解析 ===
# [[目标]] [可选权重(0.01~1.0)]
LINK_RE = re.compile(r"\[\[([^\]|#]+?)\]\](?:\s+(\d+\.?\d*))?")

def parse_note(filepath: Path) -> tuple[str, list[tuple[str, float]]]:
    """返回 (笔记名, [(目标笔记名, 权重)])"""
    name = filepath.stem
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        return name, []
    results = []
    for m in LINK_RE.finditer(content):
        target = m.group(1).strip()
        weight_str = m.group(2)
        weight = float(weight_str) if weight_str else DEFAULT_WEIGHT
        weight = max(0.01, min(1.0, weight))
        results.append((target, weight))
    return name, results


def build_graph() -> tuple[nx.DiGraph, set[str]]:
    """扫描知识体系，构建加权有向图"""
    G = nx.DiGraph()
    
    md_files = []
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            if f.endswith(".md"):
                md_files.append(Path(root) / f)
    
    all_names = {p.stem for p in md_files}
    orphan_targets = set()
    
    for fp in md_files:
        name, targets = parse_note(fp)
        G.add_node(name, path=str(fp.relative_to(VAULT)))
        
        for t, w in targets:
            if t in all_names:
                G.add_edge(name, t, weight=w)
            else:
                orphan_targets.add(t)
    
    return G, orphan_targets


def analyze(G: nx.DiGraph, orphan_targets: set[str]):
    """运行全套图论分析"""
    n = G.number_of_nodes()
    m = G.number_of_edges()
    
    # 统计有权重的边
    edges_with_custom_weight = sum(1 for _, _, d in G.edges(data=True) if d.get("weight", DEFAULT_WEIGHT) != DEFAULT_WEIGHT)
    weight_avg = sum(d.get("weight", DEFAULT_WEIGHT) for _, _, d in G.edges(data=True)) / m if m > 0 else 0
    
    print("=" * 60)
    print("📊 知识体系图论分析报告 v2（加权有向图）")
    print("=" * 60)
    print(f"\n节点数（笔记）: {n}")
    print(f"边数（链接）: {m}")
    print(f"  其中自定义权重: {edges_with_custom_weight}")
    print(f"  平均权重: {weight_avg:.3f}")
    print(f"平均出度: {m/n:.2f}")
    print(f"密度: {m / (n*(n-1)):.6f}" if n > 1 else "密度: N/A")
    
    if orphan_targets:
        print(f"\n⚠️ 幽灵链接 ({len(orphan_targets)} 个目标笔记不存在):")
        for t in sorted(orphan_targets)[:20]:
            print(f"  → [[{t}]]")
        if len(orphan_targets) > 20:
            print(f"  ... 还有 {len(orphan_targets)-20} 个")
    
    # === 有向边统计 ===
    UG = G.to_undirected()
    reciprocal = sum(1 for u, v in G.edges() if G.has_edge(v, u))
    one_way = m - reciprocal
    
    print(f"\n— 有向边统计 —")
    print(f"  单向边: {one_way}")
    print(f"  双向边（互链）: {reciprocal}")
    print(f"  总无向边（合并后）: {UG.number_of_edges()}")
    
    # === 1. 入度（被引用次数）===
    if m > 0:
        print("\n" + "─" * 60)
        print("📌 入度排名（被引用最多的笔记）")
        print("─" * 60)
        indeg = sorted(G.in_degree(weight=None), key=lambda x: -x[1])
        for node, deg in indeg[:15]:
            if deg > 0:
                # 显示入边平均权重
                in_edges = [(u, d.get("weight", DEFAULT_WEIGHT)) for u, _, d in G.in_edges(node, data=True)]
                avg_w = sum(w for _, w in in_edges) / len(in_edges) if in_edges else 0
                print(f"  {deg:3d} ← {node}  (入边均权 {avg_w:.2f})")
    
    # === 2. 加权出度 ===
    if m > 0:
        print("\n" + "─" * 60)
        print("📤 出度排名（引用最多的笔记 — 可能是 MOC）")
        print("─" * 60)
        outdeg = sorted(G.out_degree(weight=None), key=lambda x: -x[1])
        for node, deg in outdeg[:15]:
            if deg > 0:
                print(f"  {node} → {deg:3d}")
    
    # === 3. 加权 PageRank ===
    if m > 0 and n > 1:
        print("\n" + "─" * 60)
        print("⭐ PageRank 排名（加权，全局重要性）")
        print("─" * 60)
        try:
            pr = nx.pagerank(G, alpha=0.85, weight="weight")
            for node, score in sorted(pr.items(), key=lambda x: -x[1])[:15]:
                print(f"  {score:.6f}  {node}")
        except nx.PowerIterationFailedConvergence:
            print("  (PageRank 未收敛)")
    
    # === 4. 介数中心性（加权）===
    if m > 1 and n > 2:
        print("\n" + "─" * 60)
        print("🌉 介数中心性排名（加权，桥接笔记）")
        print("─" * 60)
        try:
            bc = nx.betweenness_centrality(UG, k=min(n, 100), weight="weight")
            for node, score in sorted(bc.items(), key=lambda x: -x[1])[:15]:
                if score > 0:
                    print(f"  {score:.6f}  {node}")
        except Exception as e:
            print(f"  (计算失败: {e})")
    
    # === 5. 连通分量 ===
    print("\n" + "─" * 60)
    print("🔗 弱连通分量分析")
    print("─" * 60)
    wcc = sorted(nx.connected_components(UG), key=len, reverse=True)
    giant = wcc[0] if wcc else set()
    
    print(f"  连通分量总数: {len(wcc)}")
    print(f"  最大连通分量: {len(giant)} 个笔记 ({100*len(giant)/n:.1f}%)")
    
    isolates = [node for node in G.nodes() if G.degree(node) == 0]
    if isolates:
        print(f"\n  🔴 完全孤立笔记 ({len(isolates)} 个):")
        for node in sorted(isolates)[:20]:
            print(f"    - {node}")
        if len(isolates) > 20:
            print(f"    ... 还有 {len(isolates)-20} 个")
    
    # === 6. 加权最短路径示例 ===
    if m > 0 and n > 5:
        print("\n" + "─" * 60)
        print("🛤️ 加权最短路径示例（权重越高 = 关系越近 = 距离越短）")
        print("─" * 60)
        # 将权重转为距离：距离 = 1/weight（权重越大距离越小）
        candidates = [n for n, d in G.in_degree() if d >= 1]
        random.seed(42)
        sample = random.sample(candidates, min(6, len(candidates)))
        for i in range(0, len(sample)-1, 2):
            s, t = sample[i], sample[i+1]
            try:
                # 用 1/weight 作距离
                path = nx.dijkstra_path(UG, source=s, target=t, weight=lambda u, v, d: 1.0 / max(d.get("weight", DEFAULT_WEIGHT), 0.01))
                dist = nx.dijkstra_path_length(UG, source=s, target=t, weight=lambda u, v, d: 1.0 / max(d.get("weight", DEFAULT_WEIGHT), 0.01))
                print(f"  {s} → {t}: {' → '.join(path)} (语义距离 {dist:.2f}, {len(path)-1} 跳)")
            except nx.NetworkXNoPath:
                print(f"  {s} → {t}: 无路径（不同连通分量）")
    
    # === 7. 社区检测 ===
    communities_map = {}
    if m > 5 and n > 3:
        print("\n" + "─" * 60)
        print("🏘️ 社区检测（Louvain 算法）")
        print("─" * 60)
        try:
            from networkx.algorithms.community import louvain_communities
            communities = louvain_communities(UG, seed=42, weight="weight")
            print(f"  检测到 {len(communities)} 个社区\n")
            for i, comm in enumerate(sorted(communities, key=len, reverse=True)):
                members = sorted(comm)
                for node in members:
                    communities_map[node] = i
                if len(members) <= 12:
                    print(f"  社区 {i+1} ({len(members)} 笔记): {', '.join(members)}")
                else:
                    print(f"  社区 {i+1} ({len(members)} 笔记): {', '.join(members[:8])} ... (+{len(members)-8} 个)")
        except Exception as e:
            print(f"  (社区检测失败: {e})")
    
    # === 8. 角色区分（HITS）===
    if m > 5 and n > 3:
        print("\n" + "─" * 60)
        print("🎯 角色区分（HITS）— Hub vs Authority")
        print("─" * 60)
        try:
            hub, auth = nx.hits(G, max_iter=100)
            print("\n  📤 Hub（擅长引路，出链多）:")
            for node, score in sorted(hub.items(), key=lambda x: -x[1])[:8]:
                if score > 0.01:
                    print(f"    {score:.4f}  {node}")
            print("\n  📥 Authority（被广泛引用，入链多）:")
            for node, score in sorted(auth.items(), key=lambda x: -x[1])[:8]:
                if score > 0.01:
                    print(f"    {score:.4f}  {node}")
        except Exception as e:
            print(f"  (HITS 失败: {e})")
    
    # === 9. 知识内核（K-core）===
    if m > 3:
        print("\n" + "─" * 60)
        print("🫀 知识内核（K-core 分解）")
        print("─" * 60)
        core = nx.core_number(UG)
        max_k = max(core.values()) if core else 0
        for k in range(max_k, 0, -1):
            members = [n for n, c in core.items() if c == k]
            if members:
                print(f"  {k}-core ({len(members)} 个): {', '.join(sorted(members)[:10])}")
                if len(members) > 10:
                    print(f"    ... 还有 {len(members)-10} 个")
        if max_k == 0:
            print("  (图太小，无 K-core)")
    
    # === 10. 最佳起点（紧密度）===
    if n > 5 and m > 0:
        print("\n" + "─" * 60)
        print("🚀 最佳起点（紧密度）— 从哪出发最快到达全局")
        print("─" * 60)
        try:
            cc = nx.closeness_centrality(UG, distance=lambda u, v, d: 1.0 / max(d.get("weight", DEFAULT_WEIGHT), 0.01))
            for node, score in sorted(cc.items(), key=lambda x: -x[1])[:10]:
                print(f"  {score:.4f}  {node}")
        except Exception as e:
            print(f"  (紧密度失败: {e})")
    
    # === 11. 区域密度（聚类系数）===
    if n > 5:
        print("\n" + "─" * 60)
        print("📐 区域密度（聚类系数）— 局部链接扎实度")
        print("─" * 60)
        try:
            clustering = nx.clustering(UG, weight="weight")
            avg_cc = sum(clustering.values()) / len(clustering) if clustering else 0
            print(f"  平均聚类系数: {avg_cc:.4f}")
            # 找出聚类系数最高和最低的
            sorted_cc = sorted(clustering.items(), key=lambda x: -x[1])
            print(f"\n  🔺 最密集区域:")
            for node, cc_val in sorted_cc[:5]:
                if cc_val > 0:
                    print(f"    {cc_val:.3f}  {node}")
            print(f"\n  🔻 最稀疏区域:")
            for node, cc_val in sorted_cc[-5:]:
                print(f"    {cc_val:.3f}  {node}")
        except Exception as e:
            print(f"  (聚类系数失败: {e})")
    
    # === 12. 断点检测（割点）===
    if n > 3 and m > 2:
        print("\n" + "─" * 60)
        print("⚠️ 断点检测（割点）— 移除它图就断裂的节点")
        print("─" * 60)
        try:
            cut_points = list(nx.articulation_points(UG))
            if cut_points:
                # 按度排序
                cut_points.sort(key=lambda x: -UG.degree(x))
                for node in cut_points[:10]:
                    print(f"  {node}  (度: {UG.degree(node)})")
                print(f"\n  共 {len(cut_points)} 个割点")
            else:
                print("  ✅ 无割点（图具有良好的冗余度）")
        except Exception as e:
            print(f"  (割点检测失败: {e})")
    
    # === 13. 知识骨架（最小生成树）===
    if n > 3 and m > n - 1:
        print("\n" + "─" * 60)
        print("🦴 知识骨架（最小生成树）— 保持连通的最少链接")
        print("─" * 60)
        try:
            mst = nx.minimum_spanning_tree(UG, weight=lambda u, v, d: 1.0 / max(d.get("weight", DEFAULT_WEIGHT), 0.01))
            print(f"  原边数: {m} → 骨架边数: {mst.number_of_edges()} (保留 {100*mst.number_of_edges()/m:.0f}%)")
            print(f"  被剪掉的冗余边: {m - mst.number_of_edges()}")
            # 显示骨架中权重最高的边
            print(f"\n  骨架核心链路:")
            top_edges = sorted(mst.edges(data=True), key=lambda x: -UG[x[0]][x[1]].get("weight", DEFAULT_WEIGHT))[:8]
            for u, v, d in top_edges:
                w = UG[u][v].get("weight", DEFAULT_WEIGHT)
                print(f"    {w:.2f}  {u} — {v}")
        except Exception as e:
            print(f"  (MST 失败: {e})")
    
    # === 14. 知识宽度（图直径）===
    if n > 3 and m > 0:
        print("\n" + "─" * 60)
        print("📏 知识宽度（图直径）— 最远两个概念的距离")
        print("─" * 60)
        try:
            # 在主连通分量上算直径
            giant_comp = max(nx.connected_components(UG), key=len)
            sub = UG.subgraph(giant_comp)
            if sub.number_of_nodes() > 1:
                diam = nx.diameter(sub, weight=lambda u, v, d: 1.0 / max(d.get("weight", DEFAULT_WEIGHT), 0.01))
                avg_dist = nx.average_shortest_path_length(sub, weight=lambda u, v, d: 1.0 / max(d.get("weight", DEFAULT_WEIGHT), 0.01))
                print(f"  直径（最远语义距离）: {diam:.2f}")
                print(f"  平均语义距离: {avg_dist:.2f}")
                print(f"  （在主连通分量 {sub.number_of_nodes()} 个节点上计算）")
        except Exception as e:
            print(f"  (直径计算失败: {e})")
    
    print("\n" + "=" * 60)
    print("✅ 分析完成")
    print("=" * 60)
    
    return G, communities_map


def export_json(G: nx.DiGraph, communities_map: dict[str, int]):
    """导出知识图为 JSON 储存文件"""
    n = G.number_of_nodes()
    
    # 节点数据
    nodes = {}
    for node in G.nodes():
        data = G.nodes[node]
        nodes[node] = {
            "path": data.get("path", ""),
            "folder": str(Path(data.get("path", "")).parent) if data.get("path") else "",
            "out_degree": G.out_degree(node),
            "in_degree": G.in_degree(node),
            "community": communities_map.get(node, -1),
        }
    
    # 边数据
    edges = []
    for u, v, d in G.edges(data=True):
        edges.append({
            "from": u,
            "to": v,
            "weight": d.get("weight", DEFAULT_WEIGHT),
            "reciprocal": G.has_edge(v, u),
        })
    
    # PageRank
    pr = {}
    if n > 1 and G.number_of_edges() > 0:
        try:
            pr = nx.pagerank(G, alpha=0.85, weight="weight")
            pr = {k: round(v, 8) for k, v in pr.items()}
        except Exception:
            pass
    
    output = {
        "meta": {
            "version": 2,
            "total_nodes": n,
            "total_edges": G.number_of_edges(),
            "default_weight": DEFAULT_WEIGHT,
        },
        "nodes": nodes,
        "edges": edges,
        "pagerank": pr,
    }
    
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n💾 图储存已导出: {OUTPUT_JSON}")
    print(f"   大小: {OUTPUT_JSON.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    print("🔍 扫描知识体系（解析 [[目标]] [权重] 语法）...")
    G, orphan_targets = build_graph()
    G, communities_map = analyze(G, orphan_targets)
    export_json(G, communities_map)
