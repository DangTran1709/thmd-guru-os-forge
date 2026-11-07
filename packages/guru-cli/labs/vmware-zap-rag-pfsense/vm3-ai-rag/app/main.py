"""
THMD-Guru LAB — VM3 AI-RAG Server (FastAPI). Run:
  uvicorn app.main:app --host 192.168.80.30 --port 8000
Environment: OLLAMA_URL, LLM_MODEL, EMBED_MODEL, QDRANT_URL, USE_LLM (auto|0), DATA_DIR, USD_PER_1K_TOKENS
"""
from __future__ import annotations

import csv
import io
import json
import os
import sqlite3
import threading
from pathlib import Path

from fastapi import BackgroundTasks, Body, FastAPI, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse

from .rag_engine import METHODS, RagEngine, build_report_html, build_report_md, compute_metrics, metrics_table

DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).resolve().parent.parent / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB = DATA_DIR / "lab.db"
PRICE = float(os.environ.get("USD_PER_1K_TOKENS", "0"))
_lock = threading.Lock()

app = FastAPI(title="THMD-Guru LAB AI-RAG Server", version="2.0.0",
              description="Xác minh và ưu tiên cảnh báo OWASP ZAP bằng AI + RAG (VM3 192.168.80.30)")
engine = RagEngine()


def db() -> sqlite3.Connection:
    con = sqlite3.connect(DB, check_same_thread=False)
    con.executescript("""
        CREATE TABLE IF NOT EXISTS runs(run_id TEXT PRIMARY KEY, meta TEXT, status TEXT DEFAULT 'received',
                                        created TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS alerts(run_id TEXT, alert_id TEXT, data TEXT, PRIMARY KEY(run_id, alert_id));
        CREATE TABLE IF NOT EXISTS results(run_id TEXT, method TEXT, alert_id TEXT, data TEXT,
                                           PRIMARY KEY(run_id, method, alert_id));
        CREATE TABLE IF NOT EXISTS labels(run_id TEXT, alert_id TEXT, gt INTEGER, rel INTEGER, note TEXT,
                                          reviewer TEXT, PRIMARY KEY(run_id, alert_id));
    """)
    return con


def load_run(run_id: str):
    con = db()
    row = con.execute("SELECT meta, status FROM runs WHERE run_id=?", (run_id,)).fetchone()
    if not row:
        raise HTTPException(404, f"run {run_id} not found")
    meta = json.loads(row[0]) | {"status": row[1]}
    alerts = [json.loads(r[0]) for r in con.execute("SELECT data FROM alerts WHERE run_id=? ORDER BY alert_id", (run_id,))]
    results: dict[str, list] = {}
    for m, d in con.execute("SELECT method, data FROM results WHERE run_id=? ORDER BY alert_id", (run_id,)):
        results.setdefault(m, []).append(json.loads(d))
    labels = {a: {"gt": bool(g), "rel": r, "note": n} for a, g, r, n in
              con.execute("SELECT alert_id, gt, rel, note FROM labels WHERE run_id=?", (run_id,))}
    return meta, alerts, results, labels


def analyze_run(run_id: str, methods=METHODS) -> None:
    _, alerts, _, _ = load_run(run_id)
    con = db()
    con.execute("UPDATE runs SET status='analyzing' WHERE run_id=?", (run_id,))
    con.commit()
    out = engine.analyze_all(alerts, methods)
    with _lock:
        for m, rows in out.items():
            for r in rows:
                con.execute("INSERT OR REPLACE INTO results VALUES(?,?,?,?)", (run_id, m, r["alert_id"], json.dumps(r)))
        con.execute("UPDATE runs SET status='analyzed' WHERE run_id=?", (run_id,))
        con.commit()


@app.get("/health")
def health():
    return {"status": "ok", "llm": engine.use_llm, "llm_model": engine.ollama.llm_model,
            "qdrant": bool(engine.qdrant), "kb_chunks": len(engine.kb.chunks)}


@app.post("/api/v1/alerts")
def ingest_alerts(background: BackgroundTasks, payload: dict = Body(...), auto_analyze: bool = True):
    """Bước (2): nhận Alert + Evidence từ VM1."""
    run_id = payload.get("run_id")
    alerts = payload.get("alerts", [])
    if not run_id or not isinstance(alerts, list):
        raise HTTPException(400, "payload must contain run_id and alerts[]")
    meta = {k: v for k, v in payload.items() if k != "alerts"}
    con = db()
    with _lock:
        con.execute("INSERT OR REPLACE INTO runs(run_id, meta, status) VALUES(?,?, 'received')", (run_id, json.dumps(meta)))
        for a in alerts:
            con.execute("INSERT OR REPLACE INTO alerts VALUES(?,?,?)", (run_id, a["alert_id"], json.dumps(a)))
        con.commit()
    if auto_analyze:
        background.add_task(analyze_run, run_id)
    return {"run_id": run_id, "received": len(alerts), "auto_analyze": auto_analyze}


@app.post("/api/v1/runs/{run_id}/analyze")
def analyze(run_id: str, methods: str = ",".join(METHODS)):
    """Bước (3): RAG truy hồi + xác minh + ưu tiên."""
    selected = tuple(m for m in methods.split(",") if m in METHODS)
    analyze_run(run_id, selected)
    _, _, results, _ = load_run(run_id)
    return {m: len(v) for m, v in results.items()}


@app.get("/api/v1/runs")
def runs():
    con = db()
    return [{"run_id": r, "status": s, "created": c, **json.loads(m)} for r, m, s, c in
            con.execute("SELECT run_id, meta, status, created FROM runs ORDER BY created DESC")]


@app.get("/api/v1/runs/{run_id}/results")
def results(run_id: str):
    return load_run(run_id)[2]


@app.post("/api/v1/runs/{run_id}/labels")
def set_labels(run_id: str, body: dict = Body(...)):
    """Người đánh giá / GVHD gắn nhãn Ground Truth và phản hồi."""
    load_run(run_id)
    con = db()
    with _lock:
        for lb in body.get("labels", []):
            con.execute("INSERT OR REPLACE INTO labels VALUES(?,?,?,?,?,?)", (
                run_id, lb["alert_id"], int(bool(lb["ground_truth_tp"])), int(lb.get("expert_relevance", 0)),
                lb.get("note", ""), body.get("reviewer", "")))
        con.commit()
    return {"run_id": run_id, "labeled": len(body.get("labels", []))}


@app.get("/api/v1/runs/{run_id}/labels/template", response_class=PlainTextResponse)
def labels_template(run_id: str):
    _, alerts, results_, _ = load_run(run_id)
    rag = {r["alert_id"]: r for r in results_.get("rag", [])}
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["alert_id", "alert_name", "url", "ai_tier", "ground_truth_tp", "expert_relevance", "note"])
    for a in alerts:
        w.writerow([a["alert_id"], a.get("alert_name", ""), a.get("url", ""), rag.get(a["alert_id"], {}).get("tier", ""), "", "", ""])
    return buf.getvalue()


@app.get("/api/v1/runs/{run_id}/metrics")
def metrics(run_id: str):
    _, _, results_, labels = load_run(run_id)
    if not labels:
        raise HTTPException(409, "chưa có nhãn Ground Truth: POST /api/v1/runs/{run_id}/labels")
    m = compute_metrics(results_, labels, usd_per_1k_tokens=PRICE)
    return {"labeled": len(labels), "metrics": m, "table_md": metrics_table(m)}


@app.get("/api/v1/runs/{run_id}/report")
def report(run_id: str, format: str = "md"):
    meta, _, results_, labels = load_run(run_id)
    if "rag" not in results_:
        raise HTTPException(409, "run chưa được phân tích")
    m = compute_metrics(results_, labels, usd_per_1k_tokens=PRICE) if labels else None
    md = build_report_md(meta, results_, m)
    if format == "html":
        return HTMLResponse(build_report_html(md))
    if format == "json":
        return {"run": meta, "results": results_, "metrics": m}
    return PlainTextResponse(md, media_type="text/markdown; charset=utf-8")


@app.get("/", response_class=HTMLResponse)
def dashboard():
    rows = "".join(
        f"<tr><td>{r['run_id']}</td><td>{r.get('target', '')}</td><td>{r['status']}</td><td>{r['created']}</td>"
        f"<td><a href='/api/v1/runs/{r['run_id']}/report?format=html'>Báo cáo</a> · "
        f"<a href='/api/v1/runs/{r['run_id']}/labels/template'>Mẫu gắn nhãn</a> · "
        f"<a href='/api/v1/runs/{r['run_id']}/metrics'>Chỉ số</a></td></tr>" for r in runs())
    h = health()
    return HTMLResponse(f"""<!doctype html><html lang="vi"><head><meta charset="utf-8"><title>THMD-Guru AI-RAG</title>
<style>body{{font-family:Segoe UI,sans-serif;background:#0A0F1E;color:#E6ECF7;padding:24px}}h1{{color:#F5D77A}}
table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #234178;padding:8px}}th{{background:#0B3D91;color:#F5D77A}}
a{{color:#60A5FA}}</style></head><body><h1>THMD-Guru LAB — VM3 AI-RAG Server (192.168.80.30)</h1>
<p>LLM: <b>{h['llm_model'] if h['llm'] else 'tắt (chế độ RAG + luật)'}</b> · Qdrant: {h['qdrant']} · Đoạn tri thức: {h['kb_chunks']} ·
<a href="/docs">API docs</a></p><table><tr><th>Run</th><th>Mục tiêu</th><th>Trạng thái</th><th>Thời gian</th><th></th></tr>{rows}</table>
</body></html>""")

