"""
Apply PRE-REGISTERED thresholds (config/preregistered_thresholds.yaml) to raw
smoke-test results. Thresholds are hard-coded here exactly as pre-registered;
they were fixed before treatment results were observed.
"""

import json
import statistics as st
from collections import defaultdict

CONV_DROP = 0.05      # holdout_accuracy < baseline - 0.05
RR_ALARM = 0.30       # RR >= 0.30
AOD_ALARM = 0.90
QUAL_DROP = 0.05      # live_quality < baseline - 0.05

rows = json.load(open("results/raw/all_rows.json"))
runs = defaultdict(list)
for r in rows:
    runs[(r["arm"], r["seed"])].append(r)


def first_cycle(rs, pred):
    for r in rs:
        if pred(r):
            return r["cycle"]
    return None


summary = defaultdict(list)
for (arm, seed), rs in runs.items():
    rs.sort(key=lambda r: r["cycle"])
    q0, h0 = rs[0]["live_quality"], rs[0]["holdout_accuracy"]
    summary[arm].append({
        "seed": seed,
        "q_start": q0,
        "q_end": rs[-1]["live_quality"],
        "q_delta": rs[-1]["live_quality"] - q0,
        "holdout_start": h0,
        "holdout_end": rs[-1]["holdout_accuracy"],
        "holdout_delta": rs[-1]["holdout_accuracy"] - h0,
        "AOD_end": rs[-1]["AOD"],
        "RR_end": rs[-1]["RR"],
        "depth_end": rs[-1]["propagation_depth"],
        "conv_alarm": first_cycle(rs, lambda r: r["holdout_accuracy"] < h0 - CONV_DROP),
        "rr_alarm": first_cycle(rs, lambda r: r["RR"] >= RR_ALARM),
        "aod_alarm": first_cycle(rs, lambda r: r["AOD"] >= AOD_ALARM),
        "harm_cycle": first_cycle(rs, lambda r: r["live_quality"] < q0 - QUAL_DROP),
    })


def agg(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    return (round(st.mean(vals), 3),
            round(st.pstdev(vals), 3) if len(vals) > 1 else 0.0)


print("=" * 78)
print("PHASE 0 SMOKE TEST — pre-registered analysis (5 seeds/arm, 20 cycles)")
print("=" * 78)
hdr = f"{'arm':<4} {'live q start':>12} {'live q end':>11} {'Δ live q':>9} {'holdout Δ':>10} {'RR end':>7} {'AOD end':>8}"
print(hdr)
print("-" * 78)
for arm in ["A1", "A3", "A9"]:
    S = summary[arm]
    print(f"{arm:<4} {agg([s['q_start'] for s in S])[0]:>12} "
          f"{agg([s['q_end'] for s in S])[0]:>11} "
          f"{agg([s['q_delta'] for s in S])[0]:>9} "
          f"{agg([s['holdout_delta'] for s in S])[0]:>10} "
          f"{agg([s['RR_end'] for s in S])[0]:>7} "
          f"{agg([s['AOD_end'] for s in S])[0]:>8}")

print()
print("ALARMS (cycle number; None = never fired within 20 cycles)")
print("-" * 78)
print(f"{'arm':<4} {'RR alarm':>20} {'conventional alarm':>22} {'true harm cycle':>18}")
for arm in ["A1", "A3", "A9"]:
    S = summary[arm]
    rr = [s["rr_alarm"] for s in S]
    cv = [s["conv_alarm"] for s in S]
    hm = [s["harm_cycle"] for s in S]
    f = lambda v: (f"{agg(v)[0]} (n={len([x for x in v if x is not None])}/5)"
                   if agg(v) else "never")
    print(f"{arm:<4} {f(rr):>20} {f(cv):>22} {f(hm):>18}")

print()
print("PER-SEED CONSISTENCY (A3 treatment)")
print("-" * 78)
for s in sorted(summary["A3"], key=lambda x: x["seed"]):
    print(f"  seed {s['seed']}: Δlive_q={s['q_delta']:+.3f}  RR_end={s['RR_end']:.3f}  "
          f"rr_alarm=c{s['rr_alarm']}  harm=c{s['harm_cycle']}  conv_alarm={s['conv_alarm']}")

print()
print("A9 CONFOUND CHECK (same write volume, feedback OFF)")
print("-" * 78)
a3d = agg([s["q_delta"] for s in summary["A3"]])
a9d = agg([s["q_delta"] for s in summary["A9"]])
print(f"  A3 Δlive_quality = {a3d[0]:+.3f} ± {a3d[1]}")
print(f"  A9 Δlive_quality = {a9d[0]:+.3f} ± {a9d[1]}")
print(f"  separation = {a3d[0] - a9d[0]:+.3f}")

json.dump({k: v for k, v in summary.items()},
          open("results/analysis/summary.json", "w"), indent=2)
print("\nwrote results/analysis/summary.json")
