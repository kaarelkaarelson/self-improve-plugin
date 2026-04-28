---
date: 2026-04-28
topic: si-improve-verification
---

# si:improve Verification — Session Checkpoint Replay

## Problem Frame

`si:improve` analyzes session failures and applies fixes to skills and CLAUDE.md files. But it never answers the only question that matters: did the fix actually work? Without a verification step, si:improve is compounding analysis, not compounding knowledge. Fixes that don't work still get baked into the harness, creating false confidence.

The solution is a feedback loop: after applying a fix, replay from the exact point of failure in a fresh subagent context — with the improvement in place — and verify that the workflow now completes without errors and without unnecessary steps.

## Requirements

- **R1.** After si:improve applies a change (Step 5), it calls `si:verify` with a checkpoint: the session ID and the message index at which the user originally invoked the failing skill or workflow.
- **R2.** `si:verify` is a new, standalone skill — separate from si:improve — that can also be invoked directly by the user to replay any saved checkpoint.
- **R3.** A checkpoint contains exactly: session ID + message index. The session JSONL already captures everything else (failing tool call, error output, surrounding context).
- **R4.** `si:verify` reads the session JSONL up to the checkpoint message index and injects that context into a subagent. The subagent does not re-run si:errors; it operates directly on the session context.
- **R5.** The subagent attempts the same workflow from the checkpoint. It has access to the updated skill/CLAUDE.md (the improvement is already written to disk).
- **R6.** Verification succeeds when: (a) the action completes without errors, and (b) no unnecessary or empty steps are taken — the workflow is the shortest path to the intended outcome.
- **R7.** si:improve reports the verification result in its Step 6 summary: `Verified: yes / no / skipped` per applied change.
- **R8.** Checkpoints are saved alongside the si:errors log at `~/.si-errors/<session-id>-checkpoints.json` so they can be replayed independently.
- **R9.** si:verify does not alter the current session or any existing files. It is purely a read + subagent operation.

## Success Criteria

- After running si:improve, the user knows with confidence whether each applied fix actually works — without having to manually reproduce the failure.
- si:verify can be invoked standalone (`/si:verify <session-id> <message-index>`) to replay any checkpoint at any time.
- Verification adds no unnecessary ceremony: if a fix is unverifiable (e.g. a style guide addition with no checkable output), si:verify reports `skipped` with a reason rather than blocking.

## Scope Boundaries

- `si:verify` runs as an in-process subagent, not a new terminal or CLI session. Spawning a real new terminal is out of scope.
- Workspace file state (git snapshot) is out of scope for this ticket. Verification assumes the workspace hasn't diverged significantly from the failure point; if it has, the subagent will surface that as a gap.
- `si:verify` does not re-run `si:errors` extraction — that is si:improve's responsibility.
- Loop-back (auto-retry with a new fix if verification fails) is out of scope. si:improve reports the failure; the user decides whether to run si:improve again.
- si:verify does not evaluate subjective or non-verifiable improvements (style, wording changes). It reports `skipped` for these.

## Key Decisions

- **Separate si:verify skill**: Atomically testable, invocable standalone, clean separation from si:improve's analysis logic.
- **Checkpoint = session ID + message index only**: The session JSONL is the source of truth for everything else. Storing redundant data in the checkpoint creates drift.
- **Subagent, not new terminal**: Simpler to orchestrate, observable within the current session, easier to verify that the test itself is correct.
- **Success = no errors + shortest path**: Mechanical correctness (no errors) is necessary but not sufficient. A workflow with unnecessary steps indicates the improvement is incomplete.

## Dependencies / Assumptions

- `resume-claude-session` skill already exists and reads `~/.claude/projects/**/<sessionId>.jsonl`. si:verify can reuse or mirror this pattern for context injection.
- The session JSONL format is stable and contains enough context to reconstruct the failure scenario without re-running si:errors.
- si:improve must be updated to: (a) record a checkpoint when it identifies a failure, and (b) call si:verify after Step 5.

## Outstanding Questions

### Resolve Before Planning

- None.

### Deferred to Planning

- [Affects R4][Technical] How exactly is session JSONL context injected into the subagent? Options: pass the raw JSONL slice as context, synthesize a compact prompt from the relevant turns, or use the Agent tool with a pre-built context string.
- [Affects R1][Technical] At what point in si:improve's Step 2 (failure analysis) is the checkpoint message index determined? It should be the index of the turn where the user invoked the failing skill — needs to be extracted reliably from the JSONL.
- [Affects R6][Needs research] How does the subagent know what "shortest path" means for the specific workflow? Does si:verify receive the expected steps from si:improve, or does it infer from the session context?
- [Affects R9][Technical] Checkpoint file format: JSON array of `{sessionId, messageIndex, failureDescription, appliedFix}` entries, written to `~/.si-errors/<session-id>-checkpoints.json`.

## Next Steps

→ `/ce:plan` for structured implementation planning
