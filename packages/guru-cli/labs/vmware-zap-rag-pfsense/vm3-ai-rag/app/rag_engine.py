"""
THMD-Guru LAB vmware-zap-rag-pfsense — VM3 AI-RAG engine (pure Python standard library).

Pipeline for each ZAP alert:
  1. Retrieve knowledge (Hybrid RAG): BM25 lexical + optional dense vectors (Ollama embeddings in Qdrant),
     fused with Reciprocal Rank Fusion, plus exact CWE / ZAP plugin match.
  2. Verify True/False Positive:
       - rule signals from the KB (regex checks on real request/response evidence), and
       - local LLM (Ollama) grounded on the retrieved context, if reachable.
  3. Prioritize: S_priority = 0.35*CVSS + 0.45*(10*P_tp) + 0.20*asset_criticality  ->  P1 / P2 / P3.

Three methods are produced for the research comparison:
  zap_raw        raw ZAP output (every alert is treated as positive, ranked by ZAP risk)
  llm_zero_shot  LLM without retrieved knowledge (offline: simulated by ZAP-confidence prior)
  rag            proposed method: Hybrid RAG + verification + priority scoring
"""
from __future__ import annotations

import html
import json
import math
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

KB_DIR = Path(os.environ.get("KB_DIR", Path(__file__).resolve().parent.parent / "kb"))

W_CVSS, W_PTP, W_ASSET = 0.35, 0.45, 0.20
ZAP_RISK_SCORE = {"High": 8.5, "Medium": 5.5, "Low": 3.0, "Informational": 1.0}
CONF_PRIOR = {"Confirmed": 0.9, "User Confirmed": 0.9, "High": 0.7, "Medium": 0.55, "Low": 0.4, "False Positive": 0.05}
METHODS = ("zap_raw", "llm_zero_shot", "rag")


# ----------------------------------------------------------------------------------------------
# Utilities
# ----------------------------------------------------------------------------------------------
def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+(?:-[0-9]+)?", (text or "").lower())


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def logit(p: float) -> float:
    p = min(max(p, 1e-4), 1 - 1e-4)
    return math.log(p / (1 - p))


def http_json(url: str, payload: dict | None = None, method: str | None = None, timeout: float = 120.0) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method or ("POST" if data else "GET"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8") or "{}")


# ----------------------------------------------------------------------------------------------
# Knowledge base
# ----------------------------------------------------------------------------------------------
class KnowledgeBase:
    def __init__(self, kb_dir: Path = KB_DIR):
        self.entries: dict[str, dict] = {}
        self.zap_rules: dict[str, dict] = {}
        self.chunks: list[dict] = []
        cwe_file = kb_dir / "owasp_cwe_kb.json"
        if cwe_file.is_file():
            for e in json.loads(cwe_file.read_text(encoding="utf-8"))["entries"]:
                self.entries[e["cwe_id"]] = e
                text = (f"{e['cwe_id']} {e['name']}. {e['owasp_top10']}. {e['wstg_id']}. CVSS {e['cvss_base']}. "
                        f"True positive when: {' | '.join(e['tp_indicators'])}. "
                        f"False positive when: {' | '.join(e['fp_exclusion_rules'])}. Fix: {e['remediation']}")
                self.chunks.append({"id": f"kb:{e['cwe_id']}", "kind": "cwe", "cwe_id": e["cwe_id"], "text": text,
                                    "sources": [e["wstg_id"], *e.get("sources", [])]})
        rules_file = kb_dir / "zap_rules.json"
        if rules_file.is_file():
            for r in json.loads(rules_file.read_text(encoding="utf-8"))["rules"]:
                self.zap_rules[r["plugin_id"]] = r
                self.chunks.append({"id": f"zap:{r['plugin_id']}", "kind": "zap_rule", "cwe_id": r["cwe_id"],
                                    "plugin_id": r["plugin_id"],
                                    "text": f"ZAP rule {r['plugin_id']} {r['name']} ({r['cwe_id']}). Known false positives: {r['fp_notes']}",
                                    "sources": [f"https://www.zaproxy.org/docs/alerts/{r['plugin_id']}/"]})
        # Extra free-text documents (Markdown / TXT), split by heading
        for doc in sorted(list(kb_dir.glob("*.md")) + list(kb_dir.glob("*.txt"))):
            parts = re.split(r"\n(?=#+ )", doc.read_text(encoding="utf-8"))
            for i, part in enumerate(p for p in parts if p.strip()):
                cwes = re.findall(r"CWE-\d+", part)
                self.chunks.append({"id": f"doc:{doc.name}#{i}", "kind": "doc", "cwe_id": cwes[0] if cwes else "",
                                    "text": part.strip()[:1500], "sources": [f"{doc.name}#{i}"]})


class BM25:
    def __init__(self, docs: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.toks = [tokenize(d) for d in docs]
        self.avgdl = sum(map(len, self.toks)) / max(len(self.toks), 1)
        df: dict[str, int] = {}
        for t in self.toks:
            for w in set(t):
                df[w] = df.get(w, 0) + 1
        n = len(self.toks)
        self.idf = {w: math.log(1 + (n - f + 0.5) / (f + 0.5)) for w, f in df.items()}

    def scores(self, query: str) -> list[float]:
        q = tokenize(query)
        out = []
        for t in self.toks:
            tf: dict[str, int] = {}
            for w in t:
                tf[w] = tf.get(w, 0) + 1
            s = 0.0
            for w in q:
                if w in tf:
                    s += self.idf.get(w, 0) * tf[w] * (self.k1 + 1) / (tf[w] + self.k1 * (1 - self.b + self.b * len(t) / self.avgdl))
            out.append(s)
        return out


# ----------------------------------------------------------------------------------------------
# Optional local AI services
# ----------------------------------------------------------------------------------------------
class Ollama:
    def __init__(self, base: str, llm_model: str, embed_model: str):
        self.base, self.llm_model, self.embed_model = base.rstrip("/"), llm_model, embed_model
        self._ok: bool | None = None

    def available(self) -> bool:
        if self._ok is None:
            try:
                tags = http_json(f"{self.base}/api/tags", timeout=3)
                names = {m.get("name", "").split(":")[0] for m in tags.get("models", [])}
                self._ok = self.llm_model.split(":")[0] in names
            except (urllib.error.URLError, OSError, ValueError):
                self._ok = False
        return self._ok

    def embed(self, text: str) -> list[float]:
        try:
            return http_json(f"{self.base}/api/embed", {"model": self.embed_model, "input": text})["embeddings"][0]
        except (urllib.error.HTTPError, KeyError):
            return http_json(f"{self.base}/api/embeddings", {"model": self.embed_model, "prompt": text})["embedding"]

    def generate_json(self, prompt: str) -> tuple[dict, int, int]:
        r = http_json(f"{self.base}/api/generate", {
            "model": self.llm_model, "prompt": prompt, "stream": False, "format": "json",
            "options": {"temperature": 0, "num_ctx": 4096}})
        try:
            parsed = json.loads(r.get("response", "{}"))
        except ValueError:
            parsed = {}
        return parsed, int(r.get("prompt_eval_count", 0)), int(r.get("eval_count", 0))


class Qdrant:
    def __init__(self, base: str, collection: str = "thmd_lab_kb"):
        self.base, self.collection = base.rstrip("/"), collection

    def search(self, vector: list[float], k: int) -> list[str]:
        r = http_json(f"{self.base}/collections/{self.collection}/points/search",
                      {"vector": vector, "limit": k, "with_payload": True}, timeout=10)
        return [hit["payload"]["chunk_id"] for hit in r.get("result", [])]


# ----------------------------------------------------------------------------------------------
# Engine
# ----------------------------------------------------------------------------------------------
class RagEngine:
    def __init__(self, use_llm: bool | None = None, ollama_url: str | None = None, qdrant_url: str | None = None,
                 llm_model: str | None = None, embed_model: str | None = None, kb_dir: Path = KB_DIR):
        self.kb = KnowledgeBase(kb_dir)
        self.bm25 = BM25([c["text"] for c in self.kb.chunks])
        self.by_id = {c["id"]: c for c in self.kb.chunks}
        self.ollama = Ollama(ollama_url or os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434"),
                             llm_model or os.environ.get("LLM_MODEL", "qwen2.5:3b"),
                             embed_model or os.environ.get("EMBED_MODEL", "nomic-embed-text"))
        env_flag = os.environ.get("USE_LLM", "auto").lower()
        if use_llm is None:
            use_llm = env_flag != "0" and env_flag != "false"
        self.use_llm = bool(use_llm) and self.ollama.available()
        q = qdrant_url or os.environ.get("QDRANT_URL", "")
        self.qdrant = Qdrant(q) if (q and self.use_llm) else None

    # ---------------- retrieval ----------------
    def retrieve(self, alert: dict, k: int = 4) -> list[dict]:
        query = " ".join(str(alert.get(f, "")) for f in ("alert_name", "cwe_id", "param", "description"))
        query += " " + str(alert.get("http_evidence", ""))[:300]
        lex = self.bm25.scores(query)
        lex_rank = [self.kb.chunks[i]["id"] for i in sorted(range(len(lex)), key=lambda i: -lex[i]) if lex[i] > 0][:10]
        rankings = [lex_rank]
        if self.qdrant:
            try:
                rankings.append(self.qdrant.search(self.ollama.embed(query), 10))
            except (urllib.error.URLError, OSError, KeyError, ValueError):
                pass
        fused: dict[str, float] = {}
        for ranking in rankings:  # Reciprocal Rank Fusion
            for r, cid in enumerate(ranking):
                fused[cid] = fused.get(cid, 0) + 1.0 / (60 + r)
        for cid, c in self.by_id.items():  # exact structured match
            if c.get("cwe_id") and c["cwe_id"] == alert.get("cwe_id"):
                fused[cid] = fused.get(cid, 0) + 0.05
            if c.get("plugin_id") and c["plugin_id"] == str(alert.get("plugin_id", "")):
                fused[cid] = fused.get(cid, 0) + 0.05
        return [self.by_id[cid] for cid, _ in sorted(fused.items(), key=lambda x: -x[1])[:k]]

    # ---------------- rule verification ----------------
    @staticmethod
    def _field(alert: dict, name: str) -> str:
        resp = str(alert.get("response_snippet", ""))
        return {
            "body": resp + "\n" + str(alert.get("http_evidence", "")),
            "response": resp,
            "evidence": str(alert.get("http_evidence", "")),
            "request": str(alert.get("request_snippet", "")),
            "url": str(alert.get("url", "")),
            "content_type": str(alert.get("content_type", "")),
            "status": str(alert.get("status_code", "")),
        }.get(name, "")

    def _special(self, alert: dict, kind: str) -> bool:
        attack = str(alert.get("attack", ""))
        resp = str(alert.get("response_snippet", "")) + str(alert.get("http_evidence", ""))
        if len(attack) < 4 or not any(ch in attack for ch in "<>\"'"):
            return False
        if kind == "reflected_unescaped_html":
            return attack in resp and "html" in str(alert.get("content_type", "")).lower()
        if kind == "reflected_encoded":
            return attack not in resp and html.escape(attack, quote=True) in resp
        return False

    def rule_probability(self, alert: dict) -> tuple[float, list[str]]:
        prior = CONF_PRIOR.get(str(alert.get("zap_confidence", "Medium")), 0.55)
        entry = self.kb.entries.get(alert.get("cwe_id", ""))
        if not entry:
            return prior, ["no KB entry: ZAP confidence prior only"]
        z, found = logit(prior), []
        for sign, key in ((+1, "tp_signals"), (-1, "fp_signals")):
            for s in entry.get(key, []):
                hit = self._special(alert, s["special"]) if "special" in s else bool(
                    re.search(s["regex"], self._field(alert, s["field"]), re.IGNORECASE))
                if hit:
                    z += sign * float(s["weight"])
                    found.append(f"{'TP' if sign > 0 else 'FP'}: {s['desc']}")
        return sigmoid(z), found

    # ---------------- scoring ----------------
    def _priority(self, alert: dict, p_tp: float) -> tuple[float, str, bool]:
        entry = self.kb.entries.get(alert.get("cwe_id", ""), {})
        cvss = float(entry.get("cvss_base", ZAP_RISK_SCORE.get(alert.get("zap_risk", "Low"), 3.0)))
        s = W_CVSS * cvss + W_PTP * 10.0 * p_tp + W_ASSET * float(alert.get("asset_criticality", 5.0))
        is_tp = p_tp >= 0.5
        tier = "FP" if not is_tp else ("P1" if s >= 7.5 else "P2" if s >= 5.5 else "P3")
        return round(s, 2), tier, is_tp

    @staticmethod
    def _alert_brief(alert: dict) -> str:
        keys = ("alert_name", "plugin_id", "cwe_id", "zap_risk", "zap_confidence", "url", "method", "param",
                "attack", "status_code", "content_type")
        brief = {k: alert.get(k) for k in keys}
        brief["evidence"] = str(alert.get("http_evidence", ""))[:500]
        brief["response_excerpt"] = str(alert.get("response_snippet", ""))[:700]
        return json.dumps(brief, ensure_ascii=False)

    # ---------------- methods ----------------
    def analyze(self, alert: dict, method: str) -> dict:
        t0 = time.perf_counter()
        tok_in = tok_out = 0
        reasoning, citations, signals = "", [], []
        engine = method

        if method == "zap_raw":
            p_tp = 0.05 if alert.get("zap_confidence") == "False Positive" else 1.0
            risk = ZAP_RISK_SCORE.get(alert.get("zap_risk", "Low"), 3.0)
            conf = CONF_PRIOR.get(str(alert.get("zap_confidence", "Medium")), 0.55)
            s = round(risk + conf, 2)
            tier = "FP" if p_tp < 0.5 else {"High": "P1", "Medium": "P2"}.get(alert.get("zap_risk"), "P3")
            return self._result(alert, method, p_tp >= 0.5, p_tp, s, tier, "Raw ZAP risk/confidence", [], [],
                                t0, 0, 0, "zap")

        if method == "llm_zero_shot":
            if self.use_llm:
                prompt = ("You are a web security analyst reviewing an OWASP ZAP alert from an authorized lab. "
                          "Decide if it is a true positive (TP) or false positive (FP). Reply JSON only: "
                          '{"verdict":"TP|FP","confidence":0.0-1.0,"reasoning":"<=40 words"}\nALERT: '
                          + self._alert_brief(alert))
                out, tok_in, tok_out = self.ollama.generate_json(prompt)
                p_tp = self._p_from_llm(out)
                reasoning, engine = str(out.get("reasoning", ""))[:300], f"llm:{self.ollama.llm_model}"
            else:
                # Offline simulation of an ungrounded model: ZAP confidence prior + shallow surface cues.
                p_tp = CONF_PRIOR.get(str(alert.get("zap_confidence", "Medium")), 0.55)
                if re.search(r"^(image/|font/)", str(alert.get("content_type", ""))):
                    p_tp -= 0.25
                if str(alert.get("status_code")) == "500":
                    p_tp += 0.2
                p_tp = min(max(p_tp, 0.02), 0.98)
                reasoning, engine = "offline simulation (no knowledge context)", "simulated-zero-shot"
            s, tier, is_tp = self._priority(alert, p_tp)
            return self._result(alert, method, is_tp, p_tp, s, tier, reasoning, [], [], t0, tok_in, tok_out, engine)

        # ---- proposed: Hybrid RAG ----
        ctx = self.retrieve(alert)
        p_rule, signals = self.rule_probability(alert)
        citations = list(dict.fromkeys(src for c in ctx[:2] for src in c["sources"]))[:4]
        if self.use_llm:
            context = "\n".join(f"[{c['id']}] {c['text']}" for c in ctx)
            prompt = ("You are a web security analyst verifying OWASP ZAP alerts in an authorized VMware lab.\n"
                      "Use ONLY the KNOWLEDGE below (OWASP Top 10, CWE, WSTG, ZAP rule notes) and the HTTP evidence.\n"
                      "Apply the 'False positive when' rules strictly. Reply JSON only:\n"
                      '{"verdict":"TP|FP","confidence":0.0-1.0,"reasoning":"<=60 words","citations":["chunk ids"]}\n'
                      f"KNOWLEDGE:\n{context}\n\nRULE CHECKS ON EVIDENCE: {signals or ['none matched']}\n\n"
                      f"ALERT: {self._alert_brief(alert)}")
            out, tok_in, tok_out = self.ollama.generate_json(prompt)
            p_llm = self._p_from_llm(out)
            p_tp = 0.7 * p_llm + 0.3 * p_rule  # grounded LLM decision, stabilized by deterministic checks
            reasoning = str(out.get("reasoning", ""))[:400]
            cited = [self.by_id[c]["sources"][0] for c in out.get("citations", []) if c in self.by_id]
            citations = list(dict.fromkeys(cited + citations))[:4]
            engine = f"rag+llm:{self.ollama.llm_model}" + ("+qdrant" if self.qdrant else "")
        else:
            p_tp = p_rule
            entry = self.kb.entries.get(alert.get("cwe_id", ""), {})
            reasoning = "; ".join(signals) + (f" | {entry.get('wstg_id', '')}" if entry else "")
            engine = "rag+rules"
        s, tier, is_tp = self._priority(alert, p_tp)
        return self._result(alert, method, is_tp, p_tp, s, tier, reasoning, citations, signals, t0, tok_in, tok_out,
                            engine)

    @staticmethod
    def _p_from_llm(out: dict) -> float:
        try:
            conf = float(out.get("confidence", 0.5))
        except (TypeError, ValueError):
            conf = 0.5
        conf = min(max(conf, 0.0), 1.0)
        return conf if str(out.get("verdict", "")).upper().startswith("TP") else 1.0 - conf

    def _result(self, alert, method, is_tp, p_tp, s, tier, reasoning, citations, signals, t0, tok_in, tok_out, engine):
        entry = self.kb.entries.get(alert.get("cwe_id", ""), {})
        return {
            "alert_id": alert["alert_id"], "method": method, "engine": engine,
            "alert_name": alert.get("alert_name", ""), "cwe_id": alert.get("cwe_id", ""), "url": alert.get("url", ""),
            "zap_risk": alert.get("zap_risk", ""), "verdict_tp": bool(is_tp), "p_tp": round(float(p_tp), 4),
            "s_priority": s, "tier": tier, "reasoning": reasoning, "citations": citations, "signals": signals,
            "owasp_top10": entry.get("owasp_top10", ""), "remediation": entry.get("remediation", ""),
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2), "tokens_in": tok_in, "tokens_out": tok_out,
        }

    def analyze_all(self, alerts: list[dict], methods=METHODS) -> dict[str, list[dict]]:
        return {m: [self.analyze(a, m) for a in alerts] for m in methods}


# ----------------------------------------------------------------------------------------------
# Metrics & report
# ----------------------------------------------------------------------------------------------
def compute_metrics(results: dict[str, list[dict]], labels: dict[str, dict], k: int = 5,
                    usd_per_1k_tokens: float = 0.0) -> dict[str, dict]:
    out = {}
    for method, rows in results.items():
        rows_l = [r for r in rows if r["alert_id"] in labels]
        tp = sum(1 for r in rows_l if r["verdict_tp"] and labels[r["alert_id"]]["gt"])
        fp = sum(1 for r in rows_l if r["verdict_tp"] and not labels[r["alert_id"]]["gt"])
        fn = sum(1 for r in rows_l if not r["verdict_tp"] and labels[r["alert_id"]]["gt"])
        tn = len(rows_l) - tp - fp - fn
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        ranked = sorted(rows_l, key=lambda r: -r["s_priority"])
        rel = lambda r: int(labels[r["alert_id"]]["rel"]) if labels[r["alert_id"]]["gt"] else 0
        dcg = sum((2 ** rel(r) - 1) / math.log2(i + 2) for i, r in enumerate(ranked[:k]))
        ideal = sorted((rel(r) for r in rows_l), reverse=True)[:k]
        idcg = sum((2 ** v - 1) / math.log2(i + 2) for i, v in enumerate(ideal))
        positives = [r for r in rows_l if r["verdict_tp"]]
        cited = sum(1 for r in positives if r["citations"])
        toks = sum(r["tokens_in"] + r["tokens_out"] for r in rows_l)
        out[method] = {
            "n": len(rows_l), "TP": tp, "FP": fp, "TN": tn, "FN": fn,
            "precision": round(prec * 100, 2), "recall": round(rec * 100, 2), "f1": round(f1 * 100, 2),
            "ndcg@5": round(dcg / idcg, 4) if idcg else 0.0,
            "citation_coverage": round(cited / len(positives) * 100, 2) if positives else 0.0,
            "avg_latency_ms": round(sum(r["latency_ms"] for r in rows_l) / len(rows_l), 2) if rows_l else 0.0,
            "tokens": toks, "cost_usd": round(toks / 1000 * usd_per_1k_tokens, 4),
            "engine": rows_l[0]["engine"] if rows_l else "",
        }
    base_fp = out.get("zap_raw", {}).get("FP", 0)
    for m in out.values():
        m["fprr"] = round((base_fp - m["FP"]) / base_fp * 100, 2) if base_fp else 0.0
    return out


METHOD_LABEL = {"zap_raw": "1. ZAP thô (baseline)", "llm_zero_shot": "2. LLM không RAG", "rag": "3. AI + RAG (đề xuất)"}


def metrics_table(metrics: dict[str, dict]) -> str:
    head = ("| Phương pháp | Engine | TP | FP | FN | Precision | Recall | F1 | FPRR | NDCG@5 | Có nguồn dẫn | ms/cảnh báo | Token |\n"
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
    rows = "".join(
        f"| {METHOD_LABEL.get(k, k)} | `{m['engine']}` | {m['TP']} | {m['FP']} | {m['FN']} | {m['precision']}% | "
        f"{m['recall']}% | {m['f1']}% | {m['fprr']}% | {m['ndcg@5']} | {m['citation_coverage']}% | "
        f"{m['avg_latency_ms']} | {m['tokens']} |\n" for k, m in metrics.items())
    return head + rows


def build_report_md(run: dict, results: dict[str, list[dict]], metrics: dict | None) -> str:
    rag = sorted(results.get("rag", []), key=lambda r: -r["s_priority"])
    lines = [
        f"# Báo cáo xác minh và ưu tiên cảnh báo ZAP: `{run.get('run_id', '')}`", "",
        f"- Mục tiêu: `{run.get('target', '')}` | Máy quét: {run.get('scanner', 'OWASP ZAP')} ({run.get('scan_mode', '')})",
        f"- Số cảnh báo: **{len(rag)}** | P1: {sum(r['tier'] == 'P1' for r in rag)} | P2: {sum(r['tier'] == 'P2' for r in rag)} "
        f"| P3: {sum(r['tier'] == 'P3' for r in rag)} | Lọc bỏ (FP): {sum(r['tier'] == 'FP' for r in rag)}",
        f"- Phạm vi: chỉ quét trong môi trường LAB được cấp phép trên VMware.", "",
    ]
    if metrics:
        lines += ["## Chỉ số đánh giá (theo nhãn Ground Truth của người đánh giá)", "", metrics_table(metrics), ""]
    lines += ["## Hàng đợi ưu tiên (AI + RAG)", "",
              "| # | Mức | Alert | CWE / OWASP | S | P(TP) | Lý do xác minh | Nguồn dẫn |", "|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rag, 1):
        reason = r["reasoning"].replace("|", "/")[:180]
        cites = "<br>".join(r["citations"][:3])
        lines.append(f"| {i} | **{r['tier']}** | {r['alert_id']} {r['alert_name']}<br>`{r['url'][:60]}` | "
                     f"{r['cwe_id']}<br>{r['owasp_top10']} | {r['s_priority']} | {r['p_tp']} | {reason} | {cites} |")
    lines += ["", "## Khuyến nghị khắc phục cho cảnh báo P1/P2", ""]
    for r in rag:
        if r["tier"] in ("P1", "P2"):
            lines.append(f"- **{r['alert_id']} ({r['cwe_id']})**: {r['remediation']}")
    return "\n".join(lines) + "\n"


def build_report_html(md: str) -> str:
    out, in_table = [], False
    for line in md.splitlines():
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):
                continue
            tag = "th" if not in_table else "td"
            if not in_table:
                out.append("<table>")
                in_table = True
            out.append("<tr>" + "".join(f"<{tag}>{_inline(c)}</{tag}>" for c in cells) + "</tr>")
            continue
        if in_table:
            out.append("</table>")
            in_table = False
        if line.startswith("# "):
            out.append(f"<h1>{_inline(line[2:])}</h1>")
        elif line.startswith("## "):
            out.append(f"<h2>{_inline(line[3:])}</h2>")
        elif line.startswith("- "):
            out.append(f"<p>• {_inline(line[2:])}</p>")
        elif line.strip():
            out.append(f"<p>{_inline(line)}</p>")
    if in_table:
        out.append("</table>")
    css = ("body{font-family:Segoe UI,system-ui,sans-serif;background:#0A0F1E;color:#E6ECF7;padding:24px}"
           "h1,h2{color:#F5D77A}table{border-collapse:collapse;width:100%;margin:12px 0;font-size:13px}"
           "th{background:#0B3D91;color:#F5D77A}td,th{border:1px solid #234178;padding:6px;vertical-align:top}"
           "tr:nth-child(even) td{background:#112244}code{color:#60A5FA}b{color:#F5D77A}")
    return f"<!doctype html><html lang='vi'><head><meta charset='utf-8'><style>{css}</style></head><body>{''.join(out)}</body></html>"


def _inline(text: str) -> str:
    t = html.escape(text).replace("&lt;br&gt;", "<br>")
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    return re.sub(r"`(.+?)`", r"<code>\1</code>", t)

