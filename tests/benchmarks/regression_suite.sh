#!/bin/bash
# Geneva R8 — Regression Suite
#
# Usage:   bash tests/benchmarks/regression_suite.sh
# Purpose: Run all non-live benchmark suites; fail if any score drops >5% vs baseline.
#
# Baselines live at: tests/benchmarks/baselines/{suite_name}.json
# Reports  live at:  tests/benchmarks/reports/{suite_name}-{timestamp}.json
#
# To promote a new baseline after a verified score improvement:
#   cp tests/benchmarks/reports/<suite>-latest.json tests/benchmarks/baselines/<suite>.json

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GENEVA_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

echo "=============================="
echo " Geneva Benchmark Regression  "
echo "=============================="
echo "Root: $GENEVA_ROOT"
cd "$GENEVA_ROOT"

echo ""
echo "[1/2] Running non-live benchmark suites..."
python -m pytest \
    tests/benchmarks/memory \
    tests/benchmarks/tool_use \
    tests/benchmarks/model_normalizer \
    -v --tb=short -q

PYTEST_EXIT=$?
if [ "$PYTEST_EXIT" -ne 0 ]; then
    echo ""
    echo "FAIL: Benchmark tests failed (exit=$PYTEST_EXIT)"
    exit 1
fi

echo ""
echo "[2/2] Checking regression against baselines..."

BASELINES_DIR="$SCRIPT_DIR/baselines"
REPORTS_DIR="$SCRIPT_DIR/reports"

export BASELINES_DIR REPORTS_DIR

python - <<'PYEOF'
import json, sys, glob, os

baselines_dir = os.environ.get("BASELINES_DIR", "tests/benchmarks/baselines")
reports_dir   = os.environ.get("REPORTS_DIR",   "tests/benchmarks/reports")

if not os.path.isdir(baselines_dir):
    print("No baselines directory — skipping regression check (first run)")
    sys.exit(0)

baselines = glob.glob(f"{baselines_dir}/*.json")
if not baselines:
    print("No baseline files — skipping regression check")
    sys.exit(0)

failures = []
for bf in baselines:
    suite = os.path.splitext(os.path.basename(bf))[0]
    reports = sorted(glob.glob(f"{reports_dir}/{suite}-*.json"))
    if not reports:
        print(f"  WARN: no report for suite '{suite}' — skipping")
        continue
    latest  = json.loads(open(reports[-1]).read())
    baseline = json.loads(open(bf).read())
    b_score = baseline.get("overall_score", 0.0)
    c_score = latest.get("overall_score", 0.0)
    drop = b_score - c_score
    if drop > 0.05:
        failures.append(
            f"REGRESSION '{suite}': baseline={b_score:.3f}  current={c_score:.3f}  drop={drop:.3f}"
        )
    else:
        print(f"  OK  {suite}: baseline={b_score:.3f}  current={c_score:.3f}")

if failures:
    print("\nREGRESSION DETECTED:")
    for f in failures:
        print(f"  {f}")
    sys.exit(1)

print("\nAll suites within regression threshold (max_drop=0.05).")
PYEOF

echo ""
echo "=============================="
echo " Regression Suite PASSED      "
echo "=============================="
exit 0
