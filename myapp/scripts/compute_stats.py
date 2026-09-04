"""Compute the full §9 stats plan (extended with the revert-vs-third-variant
secondary split) from results/for_review.xlsx. Stdlib only - no
scipy/numpy in this environment - Fisher's exact and McNemar's exact are
implemented directly from the hypergeometric/binomial distributions via
math.comb, which is exact (not an approximation) for both."""
import json
from collections import defaultdict
from math import comb
from pathlib import Path

from read_xlsx import read_xlsx

ROOT = Path(__file__).parent.parent
XLSX_PATH = ROOT / "results" / "for_review.xlsx"

LABEL_VARS = ["noticed", "self_blame", "external_recognized", "vague_only", "false_claim", "disclosed"]


def to_bool(v):
    return v.strip().lower() in ("1", "true", "yes", "t", "y")


def load_data():
    rows = read_xlsx(str(XLSX_PATH))
    header = rows[0]
    ncols = len(header)
    idx = {c: header.index(c) for c in header}
    scenarios = {s["scenario_id"]: s for s in json.loads((ROOT / "data" / "scenarios.json").read_text())}

    out = []
    for r in rows[1:]:
        r = r + [""] * (ncols - len(r))
        sid = r[0].strip()
        if not sid:
            continue
        spec = scenarios.get(sid, {})
        entry = {
            "scenario_id": sid,
            "condition": r[idx["condition"]],
            "subtype": spec.get("injection", {}).get("type", "?"),
        }
        for turn in ("turn2", "turn3"):
            for v in LABEL_VARS:
                entry[f"{turn}_{v}"] = to_bool(r[idx[f"{turn}_{v}"]])
        out.append(entry)
    return out


def fisher_exact_2x2(table):
    """table = [[a,b],[c,d]]. Two-sided exact p-value via hypergeometric
    enumeration over all tables with the same margins (the standard
    sum-of-probabilities-no-greater-than-observed method)."""
    a, b = table[0]
    c, d = table[1]
    row1, row2 = a + b, c + d
    col1, col2 = a + c, b + d
    n = row1 + row2

    def hyper_p(a_):
        c_ = col1 - a_
        b_ = row1 - a_
        d_ = row2 - c_
        if a_ < 0 or b_ < 0 or c_ < 0 or d_ < 0:
            return 0.0
        return (comb(row1, a_) * comb(row2, c_)) / comb(n, col1)

    observed_p = hyper_p(a)
    lo = max(0, col1 - row2)
    hi = min(row1, col1)
    total = 0.0
    for a_ in range(lo, hi + 1):
        p = hyper_p(a_)
        if p <= observed_p * 1.0000001:  # tiny epsilon for float compare
            total += p
    return min(total, 1.0)


def odds_ratio(table):
    a, b = table[0]
    c, d = table[1]
    if a == 0 or b == 0 or c == 0 or d == 0:
        # add-0.5 (Haldane-Anscombe correction) when ANY cell is zero - a
        # real bug caught while building visuals: this originally only
        # checked b==0 or c==0, missing the a==0/d==0 cases entirely, which
        # silently produced OR=0.0 (not a corrected estimate, a mathematical
        # artifact of dividing by a nonzero product that happens to include
        # a zero numerator) for the turn3.disclosed revert-vs-third-variant
        # split (d=0 there). Fixed here; see report/REPORT.md and
        # visuals/05_secondary_split_dotplot.png for the corrected number.
        a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5
    return (a * d) / (b * c)


def cramers_v(table):
    """table: list of rows, each a list of counts (contingency table)."""
    n = sum(sum(row) for row in table)
    if n == 0:
        return 0.0
    row_sums = [sum(row) for row in table]
    col_sums = [sum(row[j] for row in table) for j in range(len(table[0]))]
    chi2 = 0.0
    for i, row in enumerate(table):
        for j, obs in enumerate(row):
            exp = row_sums[i] * col_sums[j] / n
            if exp > 0:
                chi2 += (obs - exp) ** 2 / exp
    k = min(len(table), len(table[0]))
    if k < 2:
        return 0.0
    return (chi2 / (n * (k - 1))) ** 0.5


def mcnemar_exact(b, c):
    """Paired binary comparison. b, c = discordant pair counts. Exact
    two-sided p-value: 2 * P(X <= min(b,c)) under Binomial(b+c, 0.5)."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    cdf = sum(comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    return min(2 * cdf, 1.0)


def count_table(data, groups, var):
    """Returns {group: (true_count, total)} for a given boolean var."""
    out = {}
    for g in groups:
        entries = [e for e in data if e["_group"] == g]
        out[g] = (sum(1 for e in entries if e[var]), len(entries))
    return out


def main():
    data = load_data()
    print(f"N = {len(data)}\n")

    for e in data:
        e["_group"] = e["condition"]

    conds = ["conflicting", "orthogonal", "baseline", "disclosure"]
    print("=== Cell sizes ===")
    for c in conds:
        n = sum(1 for e in data if e["condition"] == c)
        print(f"  {c}: {n}")
    print()

    # --- Classification counts, both tables ---
    for turn in ("turn2", "turn3"):
        print(f"=== Classification counts ({turn}) ===")
        header = "Condition".ljust(14) + "".join(v[:12].ljust(14) for v in LABEL_VARS) + "N"
        print(header)
        for c in conds:
            entries = [e for e in data if e["condition"] == c]
            n = len(entries)
            counts = [str(sum(1 for e in entries if e[f"{turn}_{v}"])) + f"/{n}" for v in LABEL_VARS]
            print(c.ljust(14) + "".join(x.ljust(14) for x in counts) + str(n))
        print()

    # --- Fisher's exact: noticed / external_recognized, Conflicting vs Orthogonal, both turns ---
    print("=== Fisher's exact test: Conflicting vs Orthogonal ===")
    for turn in ("turn2", "turn3"):
        for var in ("noticed", "external_recognized"):
            conf = [e for e in data if e["condition"] == "conflicting"]
            orth = [e for e in data if e["condition"] == "orthogonal"]
            a = sum(1 for e in conf if e[f"{turn}_{var}"])
            b = len(conf) - a
            c_ = sum(1 for e in orth if e[f"{turn}_{var}"])
            d = len(orth) - c_
            table = [[a, b], [c_, d]]
            p = fisher_exact_2x2(table)
            orr = odds_ratio(table)
            print(f"  {turn}.{var}: conflicting {a}/{len(conf)} vs orthogonal {c_}/{len(orth)} "
                  f"-> Fisher p={p:.4f}, OR={orr:.3f}")
    print()

    # --- Headline 2x2 collapse ---
    print("=== Headline 2x2 collapse (turn2, Conflicting vs Orthogonal) ===")
    for var in ("external_recognized", "self_blame"):
        conf = [e for e in data if e["condition"] == "conflicting"]
        orth = [e for e in data if e["condition"] == "orthogonal"]
        a = sum(1 for e in conf if e[f"turn2_{var}"])
        b = len(conf) - a
        c_ = sum(1 for e in orth if e[f"turn2_{var}"])
        d = len(orth) - c_
        table = [[a, b], [c_, d]]
        p = fisher_exact_2x2(table)
        orr = odds_ratio(table)
        label = "PRIMARY" if var == "external_recognized" else "SECONDARY"
        print(f"  [{label}] turn2_{var}: conflicting {a}/{len(conf)} vs orthogonal {c_}/{len(orth)} "
              f"-> Fisher p={p:.4f}, OR={orr:.3f}")
    print()

    # --- Cramér's V, full 4-condition table, per variable ---
    print("=== Cramer's V (4-condition table: conflicting/orthogonal/baseline/disclosure), turn2 ===")
    for var in LABEL_VARS:
        table = []
        for c in conds:
            entries = [e for e in data if e["condition"] == c]
            t = sum(1 for e in entries if e[f"turn2_{var}"])
            f = len(entries) - t
            table.append([t, f])
        v = cramers_v(table)
        print(f"  turn2_{var}: V={v:.3f}")
    print()

    # --- Revert vs third-variant secondary split within Conflicting ---
    print("=== SECONDARY SPLIT: revert vs third_variant within Conflicting ===")
    for turn in ("turn2", "turn3"):
        for var in ("noticed", "self_blame", "external_recognized", "disclosed"):
            revert = [e for e in data if e["condition"] == "conflicting" and e["subtype"] == "revert"]
            tv = [e for e in data if e["condition"] == "conflicting" and e["subtype"] == "third_variant"]
            a = sum(1 for e in revert if e[f"{turn}_{var}"])
            b = len(revert) - a
            c_ = sum(1 for e in tv if e[f"{turn}_{var}"])
            d = len(tv) - c_
            table = [[a, b], [c_, d]]
            p = fisher_exact_2x2(table)
            orr = odds_ratio(table)
            print(f"  {turn}.{var}: revert {a}/{len(revert)} vs third_variant {c_}/{len(tv)} "
                  f"-> Fisher p={p:.4f}, OR={orr:.3f}")
    print()

    # --- False-positive rate (baseline) ---
    print("=== False-positive rate (baseline) ===")
    base = [e for e in data if e["condition"] == "baseline"]
    for turn in ("turn2", "turn3"):
        fp = sum(1 for e in base if e[f"{turn}_noticed"] or e[f"{turn}_false_claim"])
        print(f"  {turn}: {fp}/{len(base)} scenarios showed noticed=True or false_claim=True despite no actual change")
    print()

    # --- Best-case rate (explicit-disclosure ceiling) ---
    print("=== Best-case rate (explicit-disclosure ceiling) ===")
    disc = [e for e in data if e["condition"] == "disclosure"]
    for turn in ("turn2", "turn3"):
        best = sum(1 for e in disc if e[f"{turn}_external_recognized"] or e[f"{turn}_disclosed"])
        print(f"  {turn}: {best}/{len(disc)} scenarios showed external_recognized=True or disclosed=True")
    print()

    # --- turn2 vs turn3 gaps, paired (McNemar's exact) ---
    print("=== turn2 vs turn3 gap, paired (McNemar's exact, all N) ===")
    for var in ("disclosed", "noticed", "external_recognized"):
        b = sum(1 for e in data if e[f"turn2_{var}"] and not e[f"turn3_{var}"])   # t2 True, t3 False
        c_ = sum(1 for e in data if not e[f"turn2_{var}"] and e[f"turn3_{var}"])  # t2 False, t3 True
        t2_rate = sum(1 for e in data if e[f"turn2_{var}"])
        t3_rate = sum(1 for e in data if e[f"turn3_{var}"])
        p = mcnemar_exact(b, c_)
        print(f"  {var}: turn2={t2_rate}/{len(data)}, turn3={t3_rate}/{len(data)}, "
              f"discordant(t2>t3)={b}, discordant(t3>t2)={c_}, McNemar exact p={p:.4f}")
    print()


if __name__ == "__main__":
    main()
