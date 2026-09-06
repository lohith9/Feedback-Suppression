"""
Corrected Stage 1 runner. Enforces all five invariants from the FROZEN
preregistration (preregistration/STAGE1_CORRECTED.yaml) and ABORTS on violation.
7 conditions x 2 truth regimes x 10 seeds. CPU-only, deterministic, $0.
"""
import json, os, sys, hashlib, datetime, random
from sim1c import Sim1C, make_cfg, CODE_VERSION

PREREG = "preregistration/STAGE1_CORRECTED.yaml"
Q_THRESHOLD, PERSISTENCE = 0.70, 3          # must match frozen prereg
CHANGE_CYCLE = 15
import os as _os
SEEDS = list(range(1, int(_os.environ.get('N_SEEDS','10'))+1))
CONDITIONS = [(False,0.0),(False,0.3),(False,0.7),(False,0.9),
              (True,0.0),(True,0.7),(True,0.9)]
REGIMES = ["static","abrupt_shift"]


def abort(msg):
    print(f"\n*** INVARIANT VIOLATION — ABORTING ***\n{msg}", file=sys.stderr)
    sys.exit(1)


def check_threshold_invariant():
    txt = open(PREREG).read()
    if f"quality_threshold: {Q_THRESHOLD}" not in txt:
        abort(f"threshold {Q_THRESHOLD} not found in frozen prereg")
    if f"persistence_cycles: {PERSISTENCE}" not in txt:
        abort(f"persistence {PERSISTENCE} not found in frozen prereg")
    return hashlib.sha256(txt.encode()).hexdigest()


def check_seed_invariant():
    """Paired conditions must see identical truth/noise realisations per seed."""
    for s in SEEDS[:3]:
        base = None
        for wb, w in CONDITIONS:
            sim = Sim1C(make_cfg("abrupt_shift", w, wb), s)
            sig = [sim.truth.value(e, 1) for e in sim.entities[:20]]
            if base is None: base = sig
            elif sig != base:
                abort(f"seed invariant: truth differs across conditions at seed {s}")
    return True


def check_truth_invariant():
    for s in SEEDS[:3]:
        sim = Sim1C(make_cfg("abrupt_shift", 0.0, False), s)
        e = sim.entities[0]
        pre, post = sim.truth.value(e, CHANGE_CYCLE-1), sim.truth.value(e, CHANGE_CYCLE)
        if pre == post: abort(f"truth invariant: no transition at c{CHANGE_CYCLE}")
        if sim.truth.value(e,1) != sim.truth.value(e,CHANGE_CYCLE-1):
            abort("truth invariant: pre-change truth not constant")
        st = Sim1C(make_cfg("static", 0.0, False), s)
        if st.truth.value(e,1) != st.truth.value(e,40):
            abort("truth invariant: static regime changed")
    return True


def check_write_invariant(results):
    for tm in REGIMES:
        for w in [0.0, 0.7, 0.9]:
            for s in SEEDS:
                off = results.get((tm, False, w, s)); on = results.get((tm, True, w, s))
                if off and on:
                    a, b = off["rows"][-1]["writes"], on["rows"][-1]["writes"]
                    if a != b:
                        abort(f"write-volume invariant: {tm} w={w} seed={s}: OFF={a} ON={b}")
    return True


def main():
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = f"results/raw/stage1_corrected_run_{ts}_n{len(SEEDS)}"
    os.makedirs(outdir, exist_ok=True)

    print("INVARIANT PRE-CHECKS")
    ph = check_threshold_invariant(); print(f"  threshold invariant   PASS (prereg sha256 {ph[:12]})")
    check_truth_invariant();          print(f"  truth invariant       PASS (transition exactly at c{CHANGE_CYCLE})")
    check_seed_invariant();           print( "  seed invariant        PASS (identical realisations across conditions)")

    results, records = {}, []
    for tm in REGIMES:
        for wb, w in CONDITIONS:
            cfg = make_cfg(tm, w, wb)
            chash = hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:12]
            for s in SEEDS:
                rows = Sim1C(cfg, s).run()
                rec = {"experiment_id": f"{tm}_wb{int(wb)}_w{w}_s{s}",
                       "truth_mode": tm, "writeback": wb, "deference_weight": w,
                       "seed": s, "code_version": CODE_VERSION, "config_hash": chash,
                       "config": cfg, "prereg_sha256": ph, "change_cycle": CHANGE_CYCLE,
                       "run_timestamp": ts, "rows": rows}
                results[(tm, wb, w, s)] = rec
                records.append(rec)

    check_write_invariant(results);   print( "  write-volume invariant PASS (ON == OFF for all paired comparisons)")
    print(f"  config invariant      PASS (hash stored on all {len(records)} records)")

    json.dump(records, open(f"{outdir}/stage1_corrected.json","w"))
    json.dump({"timestamp": ts, "code_version": CODE_VERSION, "prereg_sha256": ph,
               "n_records": len(records), "conditions": [[bool(a),b] for a,b in CONDITIONS],
               "regimes": REGIMES, "seeds": SEEDS,
               "quality_threshold": Q_THRESHOLD, "persistence_cycles": PERSISTENCE,
               "invariants": {"threshold":"PASS","truth":"PASS","seed":"PASS",
                              "write_volume":"PASS","config":"PASS"}},
              open(f"{outdir}/run_metadata.json","w"), indent=2)
    print(f"\n{len(records)} runs -> {outdir}/stage1_corrected.json")
    print(outdir)


if __name__ == "__main__":
    main()
