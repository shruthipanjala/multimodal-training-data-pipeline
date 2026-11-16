"""Multimodal AI Training Data Pipeline.
Stages: ingest -> validate (quality gates) -> transform -> load.
"""
import csv, json
from pathlib import Path

RAW = Path("data/raw/sessions")
CLEAN = Path("data/clean")
QUAR = Path("data/quarantine")

REQUIRED_METADATA = ["session_id", "participant_id", "task", "device_id"]

def ingest():
    sessions = []
    for folder in sorted(RAW.iterdir()):
        if not folder.is_dir():
            continue
        meta = json.loads((folder / "metadata.json").read_text())
        video = json.loads((folder / "video_info.json").read_text())
        calib = json.loads((folder / "calibration.json").read_text())
        with open(folder / "motion.csv") as f:
            motion = list(csv.DictReader(f))
        sessions.append({"folder": folder.name, "metadata": meta,
                         "video": video, "calibration": calib,
                         "motion": motion})
    return sessions

def quality_gates(session):
    """Return a list of failure reasons. Empty list = session passes."""
    reasons = []
    meta = session["metadata"]
    video = session["video"]
    calib = session["calibration"]
    motion = session["motion"]
    for field in REQUIRED_METADATA:
        if not meta.get(field):
            reasons.append(f"missing_metadata:{field}")
    if video["size_mb"] < 1.0:
        reasons.append("empty_or_corrupt_video")
    if video["fps"] < 24:
        reasons.append(f"low_frame_rate:{video['fps']}fps")
    if video["duration_sec"] < 4.0:
        reasons.append("recording_too_short")
    if calib.get("device_id") != meta.get("device_id"):
        reasons.append("calibration_device_mismatch")
    if len(motion) < 100:
        reasons.append(f"insufficient_motion_data:{len(motion)}rows")
    return reasons
def transform(session):
    meta = session["metadata"]
    video = session["video"]
    motion = session["motion"]
    magnitudes = [(float(r["x"]) ** 2 + float(r["y"]) ** 2 + float(r["z"]) ** 2) ** 0.5
                  for r in motion]
    return {"session_id": meta["session_id"],
            "participant_id": meta["participant_id"],
            "task": meta["task"],
            "device_id": meta["device_id"],
            "duration_sec": video["duration_sec"],
            "fps": video["fps"],
            "video_size_mb": video["size_mb"],
            "motion_samples": len(motion),
            "mean_movement": round(sum(magnitudes) / len(magnitudes), 3),
            "quality_status": "validated"}

if __name__ == "__main__":
    CLEAN.mkdir(parents=True, exist_ok=True)
    QUAR.mkdir(parents=True, exist_ok=True)
    sessions = ingest()
    seen_ids = set()
    clean_rows, quarantine_rows = [], []
    for s in sessions:
        sid = s["metadata"].get("session_id", s["folder"])
        reasons = quality_gates(s)
        if sid in seen_ids:
            reasons.append("duplicate_session_id")
        seen_ids.add(sid)
        if reasons:
            quarantine_rows.append({"session_folder": s["folder"],
                                    "session_id": sid,
                                    "reason": "; ".join(reasons)})
        else:
            clean_rows.append(transform(s))
    with open(CLEAN / "training_dataset.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(clean_rows[0].keys()))
        w.writeheader()
        w.writerows(clean_rows)
    with open(QUAR / "quarantine_log.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["session_folder", "session_id", "reason"])
        w.writeheader()
        w.writerows(quarantine_rows)
    manifest = {"total_sessions": len(sessions),
                "validated_for_training": len(clean_rows),
                "quarantined": len(quarantine_rows),
                "delivered_data_accuracy": "100% of delivered rows passed all gates"}
    (CLEAN / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"Training dataset written: {len(clean_rows)} rows")
    print(f"Quarantine log written: {len(quarantine_rows)} rows")
    sessions = ingest()
    seen_ids = set()
    passed, quarantined = [], []
    for s in sessions:
        sid = s["metadata"].get("session_id", s["folder"])
        reasons = quality_gates(s)
        if sid in seen_ids:
            reasons.append("duplicate_session_id")
        seen_ids.add(sid)
        if reasons:
            quarantined.append((s["folder"], "; ".join(reasons)))
        else:
            passed.append(sid)
    print(f"Passed all gates: {len(passed)}")
    print(f"Quarantined: {len(quarantined)}")
    for folder, reason in quarantined:
        print(f"  {folder} -> {reason}")
