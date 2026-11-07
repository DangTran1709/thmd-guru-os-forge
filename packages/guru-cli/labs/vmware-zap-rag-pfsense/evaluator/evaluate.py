#!/usr/bin/env python3
"""
THMD-Guru LAB vmware-zap-rag-pfsense — Người đánh giá / GVHD: gắn nhãn Ground Truth và đo hiệu quả.

Chế độ 1 — LAB thật (VM3 đang chạy):
  python3 evaluate.py --server http://192.168.80.30:8000 --list
  python3 evaluate.py --server http://192.168.80.30:8000 --run <run_id> --template labels.csv   # tải mẫu nhãn
  python3 evaluate.py --server http://192.168.80.30:8000 --run <run_id> --labels labels.csv --reviewer "GVHD"

Chế độ 2 — chạy thử không cần VM (bộ dữ liệu mẫu, RAG + luật, không LLM):
  python3 evaluate.py --offline-demo [--ollama http://127.0.0.1:11434] [--out ./demo-report]

File nhãn CSV: alert_id, ground_truth_tp (1/0), expert_relevance (0-3), note
"""
import argparse
import csv
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "vm3-ai-rag"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def read_labels(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as fp:
        for r in csv.DictReader(fp):
            if str(r.get("ground_truth_tp", "")).strip() == "":
                continue
            rows.append({"alert_id": r["alert_id"].strip(),
                         "ground_truth_tp": str(r["ground_truth_tp"]).strip().lower() in ("1", "true", "tp", "yes", "x"),
                         "expert_relevance": int(r.get("expert_relevance") or 0), "note": r.get("note", "")})
    return rows


def api(server: str, path: str, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(server.rstrip("/") + path, data=data, headers={"Content-Type": "application/json"},
                                 method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            body = r.read().decode("utf-8")
            return json.loads(body) if r.headers.get_content_type() == "application/json" else body
    except urllib.error.HTTPError as e:
        sys.exit(f"[ERR] {e.code} {path}: {e.read().decode()[:300]}")
    except urllib.error.URLError as e:
        sys.exit(f"[ERR] Không kết nối được {server}: {e}")


def offline_demo(args) -> None:
    from app.rag_engine import RagEngine, build_report_md, compute_metrics, metrics_table  # noqa: E402

    run = json.loads((HERE / "sample_run.json").read_text(encoding="utf-8"))
    labels = {r["alert_id"]: {"gt": r["ground_truth_tp"], "rel": r["expert_relevance"]}
              for r in read_labels(HERE / "sample_labels.csv")}
    engine = RagEngine(use_llm=bool(args.ollama), ollama_url=args.ollama or None)
    mode = f"LLM {engine.ollama.llm_model}" if engine.use_llm else "RAG + luật (không LLM; LLM zero-shot được mô phỏng)"
    print("=" * 100)
    print(" THMD-GURU LAB vmware-zap-rag-pfsense — OFFLINE DEMO (dữ liệu mẫu Juice Shop + DVWA, 20 cảnh báo)")
    print(f" Chế độ: {mode}")
    print("=" * 100)
    results = engine.analyze_all(run["alerts"])
    metrics = compute_metrics(results, labels)
    print(metrics_table(metrics))
    print("Hàng đợi ưu tiên (AI + RAG):")
    for i, r in enumerate(sorted(results["rag"], key=lambda r: -r["s_priority"]), 1):
        gt = "TP" if labels[r["alert_id"]]["gt"] else "FP"
        mark = "OK " if (r["verdict_tp"] == labels[r["alert_id"]]["gt"]) else "SAI"
        print(f" {i:>2}. [{r['tier']:<2}] {r['alert_id']} S={r['s_priority']:>5} P={r['p_tp']:.2f} GT={gt} {mark} "
              f"{r['cwe_id']:<9} {r['alert_name'][:48]}")
    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "report.md").write_text(build_report_md(run, results, metrics), encoding="utf-8")
        (out / "results.json").write_text(json.dumps({"metrics": metrics, "results": results}, ensure_ascii=False, indent=2),
                                          encoding="utf-8")
        print(f"\n[OK] Báo cáo: {out / 'report.md'}")
    print("\nLưu ý: số liệu demo chỉ minh hoạ pipeline; kết quả đưa vào báo cáo NCKH phải lấy từ lần quét thật trong LAB")
    print("và nhãn do người đánh giá gắn độc lập (không xem kết luận của AI trước khi gắn nhãn).")


def main() -> None:
    ap = argparse.ArgumentParser(description="THMD-Guru LAB evaluator (Ground Truth + metrics)")
    ap.add_argument("--server", default="http://192.168.80.30:8000")
    ap.add_argument("--run")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--template", type=Path, help="Tải mẫu CSV gắn nhãn của run")
    ap.add_argument("--labels", type=Path, help="CSV nhãn Ground Truth để gửi lên VM3")
    ap.add_argument("--reviewer", default="reviewer")
    ap.add_argument("--report", type=Path, help="Lưu báo cáo HTML của run")
    ap.add_argument("--offline-demo", action="store_true")
    ap.add_argument("--ollama", default="", help="(offline-demo) dùng LLM thật qua Ollama")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    if args.offline_demo:
        offline_demo(args)
        return
    if args.list:
        for r in api(args.server, "/api/v1/runs"):
            print(f"{r['run_id']:<28} {r['status']:<10} {r.get('target', '')}")
        return
    if not args.run:
        ap.error("cần --run <run_id> (xem --list) hoặc --offline-demo")
    if args.template:
        args.template.write_text(api(args.server, f"/api/v1/runs/{args.run}/labels/template"), encoding="utf-8")
        print(f"[OK] Mẫu nhãn: {args.template}. Điền ground_truth_tp (1/0) và expert_relevance (0-3), rồi chạy lại với --labels.")
        return
    if args.labels:
        labels = read_labels(args.labels)
        print(api(args.server, f"/api/v1/runs/{args.run}/labels", {"reviewer": args.reviewer, "labels": labels}))
    m = api(args.server, f"/api/v1/runs/{args.run}/metrics")
    print(f"Số cảnh báo đã gắn nhãn: {m['labeled']}\n")
    print(m["table_md"])
    if args.report:
        args.report.write_text(api(args.server, f"/api/v1/runs/{args.run}/report?format=html"), encoding="utf-8")
        print(f"[OK] Báo cáo HTML: {args.report}")


if __name__ == "__main__":
    main()

