# pyspt-v2 · Co-work Strategy

## Phase 1 (complete)
- Scaffold + waveforms module
- CI matrix (Python 3.9–3.12)
- Restructure src/pyspt → 12 subdirs (10 SPT categories + io + plotting)
  - 62 tests green (21 parity + 41 unit/property)
  - Stoppage protocol: surface anomalies immediately, self-correct, log

## Phase 2 (next)
- Implement real functions, starting with first fixture pipeline (Task #5)
- One category at a time; each PR must be green on all 4 CI jobs before merge

## Conventions
- Branch naming: feat/<category>-spt-<issue-number>
- Commit style: conventional commits (feat/fix/test/chore/perf/docs)
- Merge style: squash merge → linear history on main
- Stoppage protocol: if observed != expected, STOP, surface diff, wait for approval
