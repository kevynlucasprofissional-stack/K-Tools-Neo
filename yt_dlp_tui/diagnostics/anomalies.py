from __future__ import annotations

from pathlib import Path


def detect_anomalies(events=None, control=None, audit=None, now=None):
    """Detects suspicious states without changing download behavior.

    This module is intentionally diagnostic-only. It consumes existing
    structured events/state and never decides retries or download actions.
    """
    events = events or []
    findings = []

    for event in events:
        name = event.get("event")
        data = event.get("data") or {}
        if name == "PLAYLIST_DETECTED" and data.get("entries") == 0:
            findings.append({
                "type": "ANOMALY_PLAYLIST_EMPTY",
                "severity": "ERROR",
                "message": "Playlist identificada sem itens retornados.",
            })

    if control:
        for item in control.get("items", []):
            if item.get("status") == "completed":
                path = item.get("final_file")
                if path and not Path(path).exists():
                    findings.append({
                        "type": "CONTROL_FILE_MISMATCH",
                        "severity": "ERROR",
                        "video_id": item.get("video_id"),
                        "message": "Controle indica concluído, mas arquivo não existe.",
                    })

    if audit:
        if audit.get("status") in {"passed", "passed_with_unavailable"}:
            if audit.get("failed", 0) > 0:
                findings.append({
                    "type": "AUDIT_RESULT_INCONSISTENT",
                    "severity": "ERROR",
                    "message": "Auditoria aprovada com arquivos falhos.",
                })

    return findings
