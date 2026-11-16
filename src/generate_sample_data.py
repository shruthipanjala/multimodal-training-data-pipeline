"""Generate sample raw data that mimics live participant collection sessions.
Each session gets 4 files: metadata, video info, motion, calibration.
Some sessions are deliberately defective so our quality gates can catch them.
"""
import csv, json, math, random
from pathlib import Path

RAW = Path("data/raw/sessions")
TASKS = ["wave_hand", "walk_forward", "pick_up_object", "turn_around",
         "sit_and_stand", "reach_overhead", "step_sideways", "bend_forward"]
random.seed(42)

def motion_rows(n=150):
    rows = []
    for i in range(n):
        t = i / 30.0
        rows.append([round(t, 3),
                     round(math.sin(t) + random.uniform(-0.1, 0.1), 3),
                     round(math.cos(t) + random.uniform(-0.1, 0.1), 3),
                     round(random.uniform(0.8, 1.2), 3)])
    return rows

def write_session(idx, defect=None):
    sid = f"S{idx:03d}"
    folder = RAW / sid
    folder.mkdir(parents=True, exist_ok=True)
    device = f"CAM-{1 + idx % 4:02d}"
    metadata = {"session_id": sid, "participant_id": f"P{100 + idx}",
                "task": TASKS[idx % len(TASKS)],
                "recorded_at": f"2026-10-{(idx % 27) + 1:02d}T09:{idx % 60:02d}:00",
                "device_id": device}
    video = {"file": f"{sid}.mp4", "size_mb": round(random.uniform(40, 90), 1),
             "fps": 30, "duration_sec": 5.0}
    calibration = {"device_id": device, "calibrated": True,
                   "calibration_date": "2026-10-01"}
    if defect == "empty_video":
        video["size_mb"] = 0.0
    elif defect == "low_fps":
        video["fps"] = 10
    elif defect == "missing_metadata":
        metadata.pop("task")
    elif defect == "calibration_mismatch":
        calibration["device_id"] = "CAM-99"
    elif defect == "duplicate":
        metadata["session_id"] = "S001"
    (folder / "metadata.json").write_text(json.dumps(metadata, indent=2))
    (folder / "video_info.json").write_text(json.dumps(video, indent=2))
    (folder / "calibration.json").write_text(json.dumps(calibration, indent=2))
    rows = [] if defect == "empty_motion" else motion_rows()
    with open(folder / "motion.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t_sec", "x", "y", "z"])
        w.writerows(rows)

def main():
    defects = {5: "empty_video", 11: "low_fps", 17: "missing_metadata",
               23: "calibration_mismatch", 29: "empty_motion", 34: "duplicate"}
    for i in range(1, 41):
        write_session(i, defects.get(i))
    print("Generated 40 sample sessions (6 deliberately defective)")

if __name__ == "__main__":
    main()
