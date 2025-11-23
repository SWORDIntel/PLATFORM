#!/usr/bin/env bash
set -euo pipefail

# Run any command with optimal C/C++/LD flags injected.

# Load defaults if not already set
if [[ -f "$(dirname "$0")/opt_flags.env" ]]; then
  # shellcheck source=/home/john/Documents/IntelStack/opt_flags.env
  source "$(dirname "$0")/opt_flags.env"
fi

export CFLAGS="${CFLAGS_OPTIMAL:-${CFLAGS:-}}"
export CXXFLAGS="${CFLAGS_OPTIMAL:-${CXXFLAGS:-}}"
export LDFLAGS="${LDFLAGS_OPTIMAL:-${LDFLAGS:-}}"

exec "$@"
