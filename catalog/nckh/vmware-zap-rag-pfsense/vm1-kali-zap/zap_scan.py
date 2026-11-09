#!/usr/bin/env python3
"""
THMD-Guru LAB vmware-zap-rag-pfsense — VM1: OWASP ZAP scan + export Alert/Evidence + push to VM3 AI-RAG.

Bước (1): điều khiển ZAP daemon qua REST API (spider, ajax spider, passive/active scan).
Bước (2): chuẩn hoá cảnh báo + bằng chứng HTTP (request/response) thành JSON và gửi sang AI-RAG.

Chỉ dùng thư viện chuẩn Python 3.9+ (chạy được ngay trên Kali / THMD-Guru ATTT).

Ví dụ:
  python3 zap_scan.py --target http://192.168.80.20:3000 --mode baseline --push http://192.168.80.30:8000/api/v1/alerts
  python3 zap_scan.py --target http://192.168.80.20:8081 --mode full
  python3 zap_scan.py --from-report zap-report.json --target http://192.168.80.20:3000 --push http://192.168.80.30:8000/api/v1/alerts
"""
import argparse
import datetime as dt
import ipaddress
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parent.parent
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
SNIPPET = 1500  # số ký tự request/response giữ lại làm bằng chứng

# Mức độ quan trọng tài sản theo cổng dịch vụ mục tiêu (dùng cho điểm ưu tiên ở VM3)
ASSET_CRITICALITY = {3000: 9.0, 8081: 7.0, 8080: 6.5, 80: 6.0, 443: 6.0}


def log(msg: str) -> None:
    print(f"[VM1 {dt.datetime.now():%H:%M:%S}] {msg}", flush=True)


def load_allowed_targets() -> list:
    try:
        topo = json.loads((LAB_DIR / "topology.json").read_text(encoding="utf-8"))
        return topo.get("allowed_scan_targets", ["192.168.80.20"])
    except (OSError, ValueError):
        return ["192.168.80.20"]


def assert_in_scope(target: str, allowed: list) -> None:
    """Phạm vi an toàn: từ chối mọi mục tiêu không nằm trong allowed_scan_targets."""
    host = urllib.parse.urlparse(target).hostname or ""
    try:
        ips = {ai[4][0] for ai in socket.getaddrinfo(host, None, socket.AF_INET)}
    except socket.gaierror:
        sys.exit(f"[DENY] Không phân giải được '{host}'.")
    for ip in ips:
        if not any(ipaddress.ip_address(ip) in ipaddress.ip_network(a, strict=False) for a in allowed):
            sys.exit(f"[DENY] {host} ({ip}) nằm ngoài phạm vi LAB được cấp phép {allowed}. Dừng quét.")
    log(f"Scope OK: {host} -> {sorted(ips)} thuộc {allowed}")


class Zap:
    def __init__(self, base: str, key: str):
        self.base = base.rstrip("/")
        self.key = key

    def call(self, path: str, **params):
        url = f"{self.base}/JSON/{path}/?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"X-ZAP-API-Key": self.key})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except urllib.error.URLError as e:
            sys.exit(f"[ERR] Không gọi được ZAP API {self.base} ({e}). ZAP daemon đã chạy chưa?")

    def wait(self, label: str, fn, done, interval: float = 3.0, timeout: int = 3600):
        t0 = time.time()
        while time.time() - t0 < timeout:
            val = fn()
            log(f"{label}: {val}")
            if done(val):
                return
            time.sleep(interval)
        log(f"{label}: hết thời gian chờ {timeout}s, tiếp tục với kết quả hiện có")


def run_scan(zap: Zap, target: str, mode: str, max_minutes: int) -> None:
    zap.call("core/action/newSession", name=f"thmd-lab-{int(time.time())}", overwrite="true")
    zap.call("core/action/accessUrl", url=target, followRedirects="true")

    sid = zap.call("spider/action/scan", url=target, maxChildren="0", recurse="true")["scan"]
    zap.wait("Spider %", lambda: int(zap.call("spider/view/status", scanId=sid)["status"]), lambda v: v >= 100)

    if mode in ("full", "ajax"):
        zap.call("ajaxSpider/action/scan", url=target, inScope="false")
        zap.wait("AJAX spider", lambda: zap.call("ajaxSpider/view/status")["status"], lambda v: v == "stopped",
                 timeout=max_minutes * 60 // 2)

    zap.wait("Passive queue", lambda: int(zap.call("pscan/view/recordsToScan")["recordsToScan"]), lambda v: v == 0)

    if mode == "full":
        aid = zap.call("ascan/action/scan", url=target, recurse="true", inScopeOnly="false")["scan"]
        zap.wait("Active scan %", lambda: int(zap.call("ascan/view/status", scanId=aid)["status"]),
                 lambda v: v >= 100, interval=10, timeout=max_minutes * 60)


def http_parts(zap: Zap, message_id: str) -> dict:
    if not message_id:
        return {}
    try:
        m = zap.call("core/view/message", id=message_id).get("message", {})
    except SystemExit:
        return {}
    rh = m.get("responseHeader", "")
    status = 0
    if rh.startswith("HTTP/"):
        try:
            status = int(rh.split()[1])
        except (IndexError, ValueError):
            pass
    ctype = ""
    for line in rh.splitlines():
        if line.lower().startswith("content-type:"):
            ctype = line.split(":", 1)[1].strip()
    return {
        "status_code": status,
        "content_type": ctype,
        "request_snippet": (m.get("requestHeader", "") + m.get("requestBody", ""))[:SNIPPET],
        "response_snippet": (rh + m.get("responseBody", ""))[:SNIPPET],
    }


def normalize(raw: dict, idx: int, extra: dict, target_port: int) -> dict:
    cwe = str(raw.get("cweid", raw.get("cwe_id", "")) or "").replace("CWE-", "")
    evidence = raw.get("evidence", "") or ""
    other = raw.get("other", raw.get("otherinfo", "")) or ""
    resp = extra.get("response_snippet", "")
    return {
        "alert_id": f"ZAP-{idx:03d}",
        "alert_name": raw.get("alert") or raw.get("name") or raw.get("alertRef", "Unknown"),
        "plugin_id": str(raw.get("pluginId", raw.get("pluginid", ""))),
        "cwe_id": f"CWE-{cwe}" if cwe and cwe not in ("0", "-1") else "CWE-UNKNOWN",
        "wasc_id": str(raw.get("wascid", "")),
        "zap_risk": str(raw.get("risk", raw.get("riskdesc", "Low"))).split(" ")[0],
        "zap_confidence": str(raw.get("confidence", "Medium")),
        "url": raw.get("url", raw.get("uri", "")),
        "method": raw.get("method", "GET"),
        "param": raw.get("param", ""),
        "attack": raw.get("attack", ""),
        "status_code": extra.get("status_code", 0),
        "content_type": extra.get("content_type", ""),
        "http_evidence": " / ".join(x for x in (evidence, other[:400], resp[-600:]) if x)[:2000],
        "request_snippet": extra.get("request_snippet", ""),
        "response_snippet": resp,
        "description": (raw.get("description", "") or raw.get("desc", ""))[:800],
        "solution": (raw.get("solution", "") or "")[:500],
        "reference": (raw.get("reference", "") or "")[:500],
        "asset_criticality": ASSET_CRITICALITY.get(target_port, 6.0),
    }


def collect_from_zap(zap: Zap, target: str, target_port: int) -> list:
    raw, start = [], 0
    while True:
        page = zap.call("core/view/alerts", baseurl=target, start=str(start), count="500").get("alerts", [])
        raw.extend(page)
        if len(page) < 500:
            break
        start += 500
    seen, out = set(), []
    for a in raw:
        key = (a.get("pluginId"), a.get("url", "").split("?")[0], a.get("param", ""))
        if key in seen:
            continue
        seen.add(key)
        out.append(normalize(a, len(out) + 1, http_parts(zap, a.get("messageId", "")), target_port))
    return out


def collect_from_report(path: Path, target_port: int) -> list:
    """Đọc báo cáo ZAP dạng 'Traditional JSON' (zap-baseline.py -J / Report -> JSON)."""
    data = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for site in data.get("site", []):
        for a in site.get("alerts", []):
            for inst in a.get("instances", [{}])[:5]:
                merged = {**a, **inst, "risk": a.get("riskdesc", "Low")}
                out.append(normalize(merged, len(out) + 1, {}, target_port))
    return out


def push(url: str, payload: dict) -> None:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            log(f"Đã gửi {len(payload['alerts'])} cảnh báo tới AI-RAG: HTTP {r.status} {r.read().decode()[:200]}")
    except urllib.error.URLError as e:
        log(f"[WARN] Không gửi được tới {url}: {e}. File JSON vẫn được lưu, có thể gửi lại bằng --from-json.")


def main() -> None:
    ap = argparse.ArgumentParser(description="THMD-Guru LAB VM1: OWASP ZAP scan -> AI-RAG")
    ap.add_argument("--target", required=True, help="URL mục tiêu, ví dụ http://192.168.80.20:3000")
    ap.add_argument("--mode", choices=["baseline", "ajax", "full"], default="baseline",
                    help="baseline = spider + passive; ajax = thêm AJAX spider (SPA); full = thêm active scan")
    ap.add_argument("--zap", default=os.environ.get("ZAP_API", "http://127.0.0.1:8090"))
    ap.add_argument("--api-key", default=os.environ.get("ZAP_API_KEY", ""))
    ap.add_argument("--max-minutes", type=int, default=60)
    ap.add_argument("--from-report", type=Path, help="Bỏ qua quét, đọc báo cáo ZAP JSON có sẵn")
    ap.add_argument("--from-json", type=Path, help="Gửi lại file zap_alerts.json đã chuẩn hoá")
    ap.add_argument("--push", default="", help="URL AI-RAG, ví dụ http://192.168.80.30:8000/api/v1/alerts")
    ap.add_argument("--out", type=Path, default=Path("zap-output"))
    args = ap.parse_args()

    allowed = load_allowed_targets()
    assert_in_scope(args.target, allowed)
    port = urllib.parse.urlparse(args.target).port or 80

    if args.from_json:
        payload = json.loads(args.from_json.read_text(encoding="utf-8"))
        if args.push:
            push(args.push, payload)
        return

    run_id = f"run-{dt.datetime.now():%Y%m%d-%H%M%S}"
    started = dt.datetime.now().isoformat(timespec="seconds")
    t0 = time.time()

    if args.from_report:
        alerts = collect_from_report(args.from_report, port)
    else:
        key = args.api_key
        if not key and Path("/etc/thmd-guru/zap-api-key").is_file():
            key = Path("/etc/thmd-guru/zap-api-key").read_text().strip()
        zap = Zap(args.zap, key)
        log(f"ZAP {zap.call('core/view/version').get('version', '?')} | mode={args.mode} | target={args.target}")
        run_scan(zap, args.target, args.mode, args.max_minutes)
        alerts = collect_from_zap(zap, args.target, port)

    payload = {
        "run_id": run_id,
        "target": args.target,
        "scanner": "OWASP ZAP",
        "scan_mode": args.mode if not args.from_report else "imported-report",
        "scanner_host": socket.gethostname(),
        "started_at": started,
        "finished_at": dt.datetime.now().isoformat(timespec="seconds"),
        "scan_seconds": round(time.time() - t0, 1),
        "alerts": alerts,
    }
    out_dir = args.out / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "zap_alerts.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    by_risk = {}
    for a in alerts:
        by_risk[a["zap_risk"]] = by_risk.get(a["zap_risk"], 0) + 1
    log(f"{len(alerts)} cảnh báo (đã khử trùng lặp) {by_risk} -> {out_dir / 'zap_alerts.json'}")

    if args.push:
        push(args.push, payload)
    print(run_id)


if __name__ == "__main__":
    main()

