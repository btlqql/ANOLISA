#!/bin/bash
# Regression: value-taking options with no value must print an error,
# not exit silently. `shift 2` under `set -e` killed the script with
# rc=1 and zero output when the option was last on the command line.
SCRIPT="$(cd "$(dirname "$0")/../../src/os-skills/ai/install-hermes/scripts" && pwd)/install.sh"
fail=0
for opt in --branch --dir --hermes-home; do
    out=$(bash "$SCRIPT" "$opt" 2>&1)
    rc=$?
    if [[ $rc -eq 0 ]]; then
        echo "FAIL: $opt without a value exited 0"; fail=1
    elif [[ -z "$out" ]]; then
        echo "FAIL: $opt without a value exited silently (rc=$rc)"; fail=1
    else
        echo "ok: $opt without a value reports: $out"
    fi
done
out=$(bash "$SCRIPT" --unknown 2>&1)
[[ $? -ne 0 && -n "$out" ]] && echo "ok: unknown option still rejected" || { echo "FAIL: unknown option handling"; fail=1; }
exit $fail
