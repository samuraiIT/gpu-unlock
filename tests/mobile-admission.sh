#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-only
# Compile and exercise the real selector with no hardware access.
set -eu
repo=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
test_dir=$(mktemp -d)
trap 'rm -f "$test_dir/test-mobile-admission"; rmdir "$test_dir"' EXIT HUP INT TERM
# Upstream recipe tables intentionally omit zero-initialized trailing fields
# and retain an unused GA100 family. Keep all other warnings fatal.
${CC:-cc} -std=c11 -Wall -Wextra -Werror \
    -Wno-missing-field-initializers -Wno-unused-const-variable \
    -I "$repo/kernel/gpu_unlock" \
    "$repo/tests/test_mobile_admission.c" "$repo/kernel/gpu_unlock/recipes.c" \
    -o "$test_dir/test-mobile-admission"
"$test_dir/test-mobile-admission"
