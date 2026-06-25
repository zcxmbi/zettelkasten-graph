"""
单节点注意力蒸馏脚本 — LLM as Teacher Model

用法：
  python distill_attention.py "<节点名>"           # 调 API
  python distill_attention.py "<节点名>" --dry-run  # 只看 prompt

环境变量（.env 或系统环境）：
  ATTENTION_API_KEY      API 密钥（必填）
  ATTENTION_BASE_URL     API 地址（默认 https://api.deepseek.com）
  ATTENTION_MODEL        模型名（默认 deepseek-chat）
  GRAPH_KASTEN_VAULT     笔记目录路径

原理：
  LLM 读取源笔记 + 所有出链目标，输出注意力百分比分布。
  对比你设定的绝对权重归一化后的差异 → 暴露偏差 → 人做最终修正。
  这是个体级别的知识蒸馏：你的知识图权重 vs 万亿参数模型的判断。
"""
import os
import re
import json
import sys
from pathlib import Path

import networkx as nx


# === 加载环境 ===
SCRIPT_DIR = Path(__file__).resolve().parent
ENV_FILE = SCRIPT_DIR / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").split("\n"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

API_KEY = os.environ.get("ATTENTION_API_KEY", "")
BASE_URL = os.environ.get("ATTENTION_BASE_URL", "https://api.deepseek.com")
MODEL = os.environ.get("ATTENTION_MODEL", "deepseek-chat")
VAULT_DIR = Path(os.environ.get("GRAPH_KASTEN_VAULT", "."))
GRAPH_JSON = VAULT_DIR / "knowledge_graph.json"


def strip_wikilinks(text: str) -> str:
    """移除 [[...]] 但保留链接文字"""
    return re.sub(r"\[\[([^\]|#]+?)(?:\|[^\]]+)?\]\]", r"\1", text)


def load_graph():
    with open(GRAPH_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    G = nx.DiGraph()
    for node_id, node_data in data["nodes"].items():
        G.add_node(node_id, **node_data)
    for edge in data["edges"]:
        G.add_edge(edge["from"], edge["to"], weight=edge["weight"])
    return G


def build_prompt(source_name: str, G: nx.DiGraph):
    """构建蒸馏 prompt"""
    if source_name not in G:
        sys.exit(f"节点 '{source_name}' 在图中不存在")

    out_edges = [(t, d["weight"]) for _, t, d in G.out_edges(source_name, data=True)]
    if len(out_edges) < 2:
        sys.exit(f"节点 '{source_name}' 只有 {len(out_edges)} 条出边，训练价值过低")

    out_edges.sort(key=lambda x: -x[1])
    current_weights = dict(out_edges)

    src_path = VAULT_DIR / f"{source_name}.md"
    if not src_path.exists():
        sys.exit(f"源笔记文件不存在: {src_path}")
    src_content = strip_wikilinks(src_path.read_text(encoding="utf-8"))
    src_title = source_name.split("-", 1)[-1] if "-" in source_name else source_name

    prompt_parts = [
        f"你是知识蒸馏教师。阅读以下源笔记和它引用的 {len(out_edges)} 个笔记。",
        "你的任务：将 100% 注意力分配给这些被引笔记。只输出百分比，不要解释。\n",
        f"# 源笔记：{src_title}\n",
        src_content,
        "",
    ]

    targets_short = {}
    for i, (target, _) in enumerate(out_edges, 1):
        tgt_path = VAULT_DIR / f"{target}.md"
        if not tgt_path.exists():
            print(f"  ⚠️ 目标笔记不存在: {target}，跳过")
            continue
        tgt_content = strip_wikilinks(tgt_path.read_text(encoding="utf-8"))
        tgt_title = target.split("-", 1)[-1] if "-" in target else target
        targets_short[target] = tgt_title
        prompt_parts.append(f"# 被引笔记 B{i}：{tgt_title}\n")
        prompt_parts.append(tgt_content)
        prompt_parts.append("")

    prompt_parts.append("将 100% 注意力分配给以上被引笔记。输出格式：")
    for target, _ in out_edges:
        short = targets_short.get(target, target)
        prompt_parts.append(f"{short}: XX%")
    prompt_parts.append("总和必须为 100%。只输出上述格式，不要任何解释。")

    return "\n".join(prompt_parts), current_weights, src_title


def call_llm(prompt: str) -> str:
    """调用 LLM API (OpenAI-compatible)"""
    try:
        import requests
    except ImportError:
        sys.exit("需要安装 requests: pip install requests")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 200,
    }

    resp = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=120,
    )
    if resp.status_code != 200:
        sys.exit(f"API 错误 ({resp.status_code}): {resp.text}")
    return resp.json()["choices"][0]["message"]["content"]


def parse_response(response: str, targets_short: dict[str, str]) -> dict[str, float]:
    """从 LLM 响应中解析百分比"""
    short_to_full = {v: k for k, v in targets_short.items()}
    percentages = {}

    for line in response.strip().split("\n"):
        line = line.strip()
        match = re.match(r"(.+?)[:：]\s*(\d+\.?\d*)\s*%", line)
        if match:
            name = match.group(1).strip()
            value = float(match.group(2))
            if name in short_to_full:
                percentages[short_to_full[name]] = value
            elif name in targets_short:
                percentages[name] = value
            else:
                for short, full in short_to_full.items():
                    if short in name or name in short:
                        percentages[full] = value
                        break

    return percentages


def analyze(targets: dict[str, float], current_weights: dict[str, float]):
    """对比分析"""
    total_weight = sum(current_weights.values())
    normalized = {t: w / total_weight * 100 for t, w in current_weights.items()}

    print("\n" + "=" * 70)
    print("📊 注意力蒸馏结果")
    print("=" * 70)

    missing = [t for t in current_weights if t not in targets]
    if missing:
        print(f"⚠️ 未解析到以下目标的 LLM 响应: {missing}")
        for m in missing:
            targets[m] = 0.0

    print(f"\n{'被引笔记':35s} {'绝对权重':>8s} {'归一化':>8s} {'LLM注意力':>10s} {'偏差':>8s}")
    print("-" * 70)

    deviations = []
    for target, weight in sorted(current_weights.items(), key=lambda x: -x[1]):
        norm = normalized[target]
        llm_pct = targets.get(target, 0)
        deviation = llm_pct - norm
        deviations.append((target, deviation))

        short = target.split("-", 1)[-1] if "-" in target else target
        if len(short) > 34:
            short = short[:31] + "..."

        flag = ""
        if abs(deviation) >= 8:
            flag = " ⚠️ 显著偏差"
        elif abs(deviation) >= 4:
            flag = " ·"

        print(f"  {short:35s} {weight:>7.2f} {norm:>7.1f}% {llm_pct:>9.1f}% {deviation:>+7.1f}%{flag}")

    total = sum(targets.values())
    if abs(total - 100) > 1:
        print(f"\n  ⚠️ LLM 输出总和 = {total:.1f}%（应为 100%）")

    print(f"\n{'─' * 70}")
    significant = [(t, d) for t, d in deviations if abs(d) >= 5]
    if significant:
        print(f"🔴 显著偏差（≥5%）: {len(significant)} 条")
        for target, dev in sorted(significant, key=lambda x: -abs(x[1])):
            short = target.split("-", 1)[-1] if "-" in target else target
            direction = "↑ 低估" if dev > 0 else "↓ 高估"
            print(f"    {short}: {dev:+.1f}% {direction}")
    else:
        print("✅ 所有偏差 <5%，绝对权重与 LLM 判断一致")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    source_name = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    if not API_KEY and not dry_run:
        sys.exit("请设置 ATTENTION_API_KEY 环境变量或在 .env 中配置")

    print(f"🔍 加载知识图: {GRAPH_JSON}")
    G = load_graph()

    print("📖 构建蒸馏 prompt...")
    prompt, current_weights, src_title = build_prompt(source_name, G)

    targets_short = {}
    for target in current_weights:
        short = target.split("-", 1)[-1] if "-" in target else target
        targets_short[target] = short

    if dry_run:
        print(f"\n{'=' * 70}")
        print("DRY RUN — 仅生成 prompt（不调用 API）")
        print(f"{'=' * 70}")
        print(f"\nAPI: {BASE_URL} | Model: {MODEL}")
        print(f"\n--- PROMPT ---\n")
        print(prompt)
        print(f"\n--- PROMPT END ---")
        print(f"\n当前绝对权重: {current_weights}")
        return

    print(f"🤖 调用 LLM: {BASE_URL} | Model: {MODEL}")
    response = call_llm(prompt)
    print(f"   LLM 原始响应:\n    {response.replace(chr(10), chr(10) + '    ')}")

    percentages = parse_response(response, targets_short)
    analyze(percentages, current_weights)


if __name__ == "__main__":
    main()
