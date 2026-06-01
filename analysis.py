#!/usr/bin/env python3
"""
Replication Analysis Script
Paper: Teaching Software Testing and Debugging Through a Serious Game:
       An Empirical Classroom Study with Sojourner under Sabotage
Authors: Aazaade Faraji, Enrico Nunes, Francisco Reis, Nuno Pombo
         Universidade da Beira Interior, Portugal

This script reproduces all statistical results reported in the paper using:
  - data_pre_questionnaire.csv   (pre-session questionnaire, N=22)
  - data_post_questionnaire.csv  (post-session questionnaire, N=21)
  - data_telemetry.json          (in-game behavioral telemetry)

Usage:
  pip install matplotlib numpy
  python analysis.py
"""

import csv, json, math
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths — adjust if running from a different directory
# ---------------------------------------------------------------------------
BASE = Path(__file__).resolve().parent
ROOT = BASE.parent   # Sorjouner_under_SABOTGE/
FIG_DIR  = BASE / "figures"
FIG_DIR.mkdir(exist_ok=True)

# Raw data from results/ (authoritative source)
PRE_CSV   = ROOT / "results" / "Software Testing Knowledge & Background Assessment.csv"
POST_CSV  = ROOT / "results" / "Post-Session Questionnaire: Introduction to Software Testing Activity.csv"
TELE_JSON = ROOT / "results" / "data.json"

# Fallback: replication-package copies
if not PRE_CSV.exists():
    PRE_CSV  = ROOT / "replication-package" / "data" / "sojourner_pre.csv"
if not POST_CSV.exists():
    POST_CSV = ROOT / "replication-package" / "data" / "sojourner_post.csv"
if not TELE_JSON.exists():
    TELE_JSON = ROOT / "replication-package" / "data" / "telemetry.json"

# ---------------------------------------------------------------------------
# Correct answers for 11 MCQ items
# ---------------------------------------------------------------------------
CORRECT_PRE = {
    23: "Testing",
    26: "Debugging",
    29: "Testing a single function in isolation from other components",
    32: "Testing interactions between components",
    35: "Black-box testing",
    38: "Designing tests based on internal code logic",
    41: "Verifying that login works correctly",
    44: "Mutation testing",
    47: "assertEquals(2, sum(1,1))",
    50: "Investigate whether the failure is due to a bug in the code or the test",
    53: "The tests are not effective enough to detect the bug"
}
CORRECT_POST = {
    11: "Testing",
    14: "Debugging",
    17: "Testing a single function in isolation from other components",
    20: "Testing interactions between components",
    23: "Black-box testing",
    26: "Designing tests based on internal code logic",
    29: "Verifying that login works correctly",
    32: "Mutation testing",
    35: "assertEquals(2, sum(1,1))",
    38: "Investigate whether the failure is due to a bug in the code or the test",
    41: "The tests are not effective enough to detect the bug"
}

# Participant code for post row (8305C treated as 8305J — same student, typo)
def normalize_code(code):
    code = code.strip().upper()
    return "8305J" if code == "8305C" else code

# ---------------------------------------------------------------------------
# Load questionnaire data
# ---------------------------------------------------------------------------
def load_scores(path, answer_cols, code_col):
    rows = list(csv.reader(open(path, encoding="utf-8")))
    scores = {}
    for r in rows[1:]:
        code = normalize_code(r[code_col])
        if not code:
            continue
        scores[code] = sum(1 for col, ans in answer_cols.items() if r[col].strip() == ans)
    return scores

pre_scores  = load_scores(PRE_CSV,  CORRECT_PRE,  5)
post_scores = load_scores(POST_CSV, CORRECT_POST, 8)

matched = sorted(set(pre_scores) & set(post_scores))
N = len(matched)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def mean(vals): return sum(vals) / len(vals) if vals else 0

def wilcoxon(diffs):
    nonzero = [(abs(d), 1 if d > 0 else -1) for d in diffs if d != 0]
    n = len(nonzero)
    if n < 3:
        return dict(Z=None, p=None, r=None, n=n)
    nonzero.sort(key=lambda x: x[0])
    ranks = []
    i = 0
    while i < n:
        j = i
        while j < n and nonzero[j][0] == nonzero[i][0]:
            j += 1
        avg = (i + 1 + j) / 2
        for k in range(i, j):
            ranks.append((avg, nonzero[k][1]))
        i = j
    W_plus  = sum(r for r, s in ranks if s > 0)
    mean_W  = n * (n + 1) / 4
    std_W   = math.sqrt(n * (n + 1) * (2 * n + 1) / 24)
    Z = (W_plus - mean_W) / std_W if std_W > 0 else 0
    a1,a2,a3,a4,a5 = 0.254829592,-0.284496736,1.421413741,-1.453152027,1.061405429
    pp = 0.3275911
    t_ = 1.0 / (1.0 + pp * abs(Z))
    cdf = 1.0 - (((((a5*t_+a4)*t_)+a3)*t_+a2)*t_+a1)*t_ * math.exp(-Z*Z/2)
    p = 2 * (1 - cdf)
    r = abs(Z) / math.sqrt(len(diffs))
    return dict(Z=round(Z,3), p=round(p,4), r=round(r,3), n=n)

def norm_gain(pre, post, max_=11):
    return (post - pre) / (max_ - pre) if pre < max_ else 0.0

def spearman(x, y):
    n = len(x)
    def rank(vals):
        idx = sorted(range(n), key=lambda i: vals[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j < n and vals[idx[j]] == vals[idx[i]]:
                j += 1
            avg = (i + 1 + j) / 2
            for k in range(i, j):
                r[idx[k]] = avg
            i = j
        return r
    rx, ry = rank(x), rank(y)
    d2 = sum((rx[i]-ry[i])**2 for i in range(n))
    rho = 1 - 6*d2 / (n*(n**2-1))
    if abs(rho) >= 1:
        return rho, 0.0
    t = rho * math.sqrt((n-2)/(1-rho**2))
    z = abs(t)
    a1,a2,a3,a4,a5 = 0.254829592,-0.284496736,1.421413741,-1.453152027,1.061405429
    pp = 0.3275911
    tp = 1.0/(1.0+pp*z)
    cdf = 1.0-(((((a5*tp+a4)*tp)+a3)*tp+a2)*tp+a1)*tp*math.exp(-z*z/2)
    p = 2*(1-cdf)
    return round(rho,3), round(p,4)

# ---------------------------------------------------------------------------
# MCQ Analysis (Section IV.A / RQ1)
# ---------------------------------------------------------------------------
print("=" * 60)
print("MCQ KNOWLEDGE ASSESSMENT")
print("=" * 60)

pre_vals  = [pre_scores[c]  for c in matched]
post_vals = [post_scores[c] for c in matched]
deltas    = [post_vals[i] - pre_vals[i] for i in range(N)]
ng        = [norm_gain(pre_vals[i], post_vals[i]) for i in range(N)]
w         = wilcoxon(deltas)

print(f"N matched pairs: {N}")
print(f"Pre  mean: {mean(pre_vals):.2f}")
print(f"Post mean: {mean(post_vals):.2f}")
print(f"Delta:     {mean(deltas):+.2f}")
print(f"Improved / Same / Declined: {sum(1 for d in deltas if d>0)} / {sum(1 for d in deltas if d==0)} / {sum(1 for d in deltas if d<0)}")
print(f"Wilcoxon Z={w['Z']}, p={w['p']}, r={w['r']}")
print(f"Normalized gain (mean): {mean(ng):.3f}")

# Sub-groups
print("\nSub-group analysis:")
for label, cond in [("Low (<8)", lambda p: p<8), ("Mid (8-9)", lambda p: 8<=p<=9), ("High (>=10)", lambda p: p>=10)]:
    grp = [c for c in matched if cond(pre_scores[c])]
    if grp:
        gd  = [post_scores[c]-pre_scores[c] for c in grp]
        gng = [norm_gain(pre_scores[c], post_scores[c]) for c in grp]
        print(f"  {label}: N={len(grp)}, pre={mean([pre_scores[c] for c in grp]):.2f}, "
              f"post={mean([post_scores[c] for c in grp]):.2f}, "
              f"gain={mean(gd):+.2f}, norm_gain={mean(gng):.3f}")

# Per-item accuracy
print("\nPer-item accuracy (%):")
pre_rows_all  = list(csv.reader(open(PRE_CSV,  encoding="utf-8")))
post_rows_all = list(csv.reader(open(POST_CSV, encoding="utf-8")))
n_pre  = len(pre_rows_all) - 1
n_post = len(post_rows_all) - 1
for i, (col, ans) in enumerate(CORRECT_PRE.items()):
    pre_pct  = sum(1 for r in pre_rows_all[1:]  if r[col].strip() == ans) / n_pre  * 100
    post_col = list(CORRECT_POST.keys())[i]
    post_ans = list(CORRECT_POST.values())[i]
    post_pct = sum(1 for r in post_rows_all[1:] if r[post_col].strip() == post_ans) / n_post * 100
    print(f"  Q{i+1:2d}: pre={pre_pct:5.1f}%  post={post_pct:5.1f}%  delta={post_pct-pre_pct:+.1f}%")

# ---------------------------------------------------------------------------
# Self-Confidence (Section IV.A / RQ1)
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("SELF-CONFIDENCE")
print("=" * 60)

SC_PRE_COLS  = [56, 58, 60, 62]
SC_POST_COLS = [44, 46, 48, 50]
SC_LABELS    = ["Understand concepts", "Write test case", "Identify/debug errors", "Analyze test failures"]

def parse_likert(v):
    for i in range(1, 6):
        if v.strip().startswith(str(i)):
            return i
    return None

pre_sc  = {}
for r in pre_rows_all[1:]:
    code = normalize_code(r[5])
    pre_sc[code] = [parse_likert(r[c]) for c in SC_PRE_COLS]
post_sc = {}
for r in post_rows_all[1:]:
    code = normalize_code(r[8])
    post_sc[code] = [parse_likert(r[c]) for c in SC_POST_COLS]

sc_matched = [c for c in matched if all(pre_sc.get(c,[])) and all(post_sc.get(c,[]))]
for i, label in enumerate(SC_LABELS):
    pv = [pre_sc[c][i]  for c in sc_matched]
    qv = [post_sc[c][i] for c in sc_matched]
    dv = [qv[j]-pv[j] for j in range(len(pv))]
    up = sum(1 for d in dv if d>0)
    same = sum(1 for d in dv if d==0)
    down = sum(1 for d in dv if d<0)
    print(f"  {label:30s}: pre={mean(pv):.2f} post={mean(qv):.2f} delta={mean(dv):+.2f}  {up}/{same}/{down}")

# ---------------------------------------------------------------------------
# Telemetry Analysis (Section IV.C / RQ3)
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("TELEMETRY ANALYSIS")
print("=" * 60)

# Username → survey-code mapping (identified post-hoc from game registration data)
# Students who registered with their name instead of the anonymous participant code.
NAME_TO_CODE = {
    "TIAGO195":    "0209E",
    "GUSTAVOPINA": "9709C",
    "RODRIGOFSTX": "4309A",
    "RIVALDO26":   "8305J",
    "ENRICO":      "5707C",
    "FASM":        "7105P",
    "DIMS":        "8701S",
    "RAINHA5":     "2701L",   # duplicate account; events merged into 2701L
    "GUIVICENTE10":"4008A",   # duplicate account; events merged into 4008A
}
# Accounts to discard entirely (admin, instructor, test)
HARD_EXCLUDE = {"AAZAADE", "ADMIN", "4507C"}

def resolve_user(username):
    u = username.upper()
    if u in HARD_EXCLUDE:
        return None
    return NAME_TO_CODE.get(u, u)

tele = json.loads(TELE_JSON.read_text())

user_events     = defaultdict(list)
user_max_room   = defaultdict(int)
user_test_execs = defaultdict(int)

for e in tele:
    code = resolve_user(e["user"]["username"])
    if code is None:
        continue
    user_events[code].append(e)
    if e["eventType"] == "GameProgressionChangedEvent":
        prog = json.loads(e["json"]).get("progression", {})
        user_max_room[code] = max(user_max_room[code], prog.get("room", 0))
    elif e["eventType"] in ("test-executed", "TestExecutedEvent"):
        user_test_execs[code] += 1

# Spearman: progression vs MCQ gain (N=21 matched after mapping)
tele_matched = sorted(set(pre_scores) & set(post_scores) & set(user_max_room))
rooms   = [user_max_room[c]              for c in tele_matched]
mcq_dlt = [post_scores[c]-pre_scores[c] for c in tele_matched]
tests   = [user_test_execs.get(c, 0)    for c in tele_matched]

rho1, p1 = spearman(rooms, mcq_dlt)
rho2, p2 = spearman(rooms, tests)

print(f"N (pre+post+tele matched): {len(tele_matched)}")
print(f"Spearman: progression vs MCQ gain:       rho={rho1}, p={p1}")
print(f"Spearman: progression vs test executions: rho={rho2}, p={p2}")

# ---------------------------------------------------------------------------
# Generate Figures
# ---------------------------------------------------------------------------
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    # Figure: Per-item MCQ accuracy
    pre_pcts  = []
    post_pcts = []
    for i, (col, ans) in enumerate(CORRECT_PRE.items()):
        pre_pcts.append(sum(1 for r in pre_rows_all[1:] if r[col].strip() == ans) / n_pre * 100)
        pc = list(CORRECT_POST.keys())[i]
        pa = list(CORRECT_POST.values())[i]
        post_pcts.append(sum(1 for r in post_rows_all[1:] if r[pc].strip() == pa) / n_post * 100)

    fig, ax = plt.subplots(figsize=(6, 3.5))
    x = range(11)
    ax.bar([i-0.2 for i in x], pre_pcts,  0.35, label="Pre",  color="#4472C4", alpha=0.85)
    ax.bar([i+0.2 for i in x], post_pcts, 0.35, label="Post", color="#ED7D31", alpha=0.85)
    ax.set_ylabel("% Correct"); ax.set_xlabel("Question")
    ax.set_title("Per-item MCQ Accuracy")
    ax.set_xticks(list(x)); ax.set_xticklabels([f"Q{i+1}" for i in range(11)], fontsize=7)
    ax.set_ylim(0, 110); ax.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig_mcq_peritem.pdf", dpi=300, bbox_inches="tight")
    plt.close()

    # Figure: Correlation scatter
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7, 3.2))
    for ax, y, rho, p, ylabel, color, title in [
        (ax1, mcq_dlt, rho1, p1, "MCQ Score Change (post−pre)", "#4472C4", "(a) Progression vs. Knowledge Gain"),
        (ax2, tests,   rho2, p2, "Number of Test Executions",   "#ED7D31", "(b) Progression vs. Testing Activity"),
    ]:
        ax.scatter(rooms, y, c=color, s=60, alpha=0.7, edgecolors="white", linewidth=0.5, zorder=3)
        z = np.polyfit(rooms, y, 1)
        xl = np.linspace(min(rooms)-0.3, max(rooms)+0.3, 50)
        ax.plot(xl, np.polyval(z, xl), "--", color="#C0392B", linewidth=1.5, alpha=0.7)
        ax.set_xlabel("Max Room Reached", fontsize=9)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.set_title(title, fontsize=9, fontweight="bold")
        lbl = f"ρ = {rho}, p = {p}" if p >= 0.001 else f"ρ = {rho}, p < 0.001"
        ax.text(0.05, 0.95, lbl, transform=ax.transAxes, fontsize=8, va="top",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#E8F0FE" if color=="#4472C4" else "#FFF2CC",
                          edgecolor=color, alpha=0.9))
        ax.set_xlim(0, 8); ax.grid(alpha=0.2)
    if mcq_dlt: ax1.set_ylim(-4, 9); ax1.axhline(y=0, color="gray", linewidth=0.5, alpha=0.4)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig_correlation.pdf", dpi=300, bbox_inches="tight")
    plt.close()

    print("\nFigures saved to figures/")
except ImportError:
    print("\nmatplotlib not installed — skipping figures. Run: pip install matplotlib numpy")

print("\n" + "=" * 60)
print("ANALYSIS COMPLETE")
print("=" * 60)
