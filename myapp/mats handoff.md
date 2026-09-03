# MATS 12.0 Application Project — Handoff Summary

---

## 1. Background / How We Got Here

Roshit is a 2nd-year MS AI student (MNSU Mankato) with existing thesis work in mechanistic
interpretability (J-space/Jacobian-lens replication, activation patching, a MiniGrid DoorKey
world-model interpretability project — WMIP — with probing/ablation tooling already built).
He previously drafted a grantmaking.ai application on mech interp work.

We reviewed grantmaking.ai's funded "Interp" category for project-shape inspiration, then shifted
to scoping a MATS application, since Neel Nanda's current stated interests are a better fit than
ambitious/basic-science interp: he's now focused on **model biology** (qualitative properties of
model behavior) and **applied interpretability**, is agnostic about technique, and explicitly
wants to be "surprised with something new" rather than shown competent execution of a known method.

## 2. Research Question

> When an LLM agent's environment changes in a way inconsistent with its own actions, does its
> CoT correctly flag the discrepancy as externally caused, or does it confabulate an internally
> consistent false narrative — and what predicts which happens (conflicting vs. orthogonal to its
> own prior action)?

This sits in "model biology" territory (a qualitative behavioral property, not a full
reverse-engineering claim) and is directly relevant to trusting CoT in real agentic deployments —
close to Neel's stated priorities without duplicating the collusion/deception literature above. (verify this is true!)

## 4. Locked Methodology

- **Model:** Qwen3-8B, MLX 4-bit (`mlx-community/Qwen3-8B-4bit`), run locally on M4 Mac 16GB via
  `mlx-lm`. Fallback: `Qwen3-4B-Instruct-2507-MLX-4bit` if 8B reasoning is incoherent.
- **Domain:** code editing — a naming-convention change task (camelCase ↔ snake_case), matches
  Roshit's original instinct.
- **Core mechanism:** two-turn setup, no real multi-agent orchestration.
  - Turn 1: model edits a code file per instructions.
  - Turn 2: model is shown "current file state" via a **simulated tool-call result**
    (`read_file`-style), which the harness has silently altered. No narration, no instruction,
    nothing hinting anything unusual happened — this is the entire manipulation. (We
    deliberately dropped an earlier idea to embed a "don't disclose" instruction in the tool
    result — that reintroduces the covert-compliance confound from idea #2 above and muddies
    whether non-disclosure means "didn't notice" or "noticed and complied.")
  - Elicitation: force a decision point (e.g., "summarize what's changed since your last turn" or
    "verify your prior edit is intact") rather than just "continue," so the CoT has to actually
    engage with the discrepancy.
- **Core conditions (30-40 scenarios total, 15-20 each):**
  - *Conflicting* — injected change directly undoes/contradicts the model's own edit.
  - *Orthogonal* — an unrelated part of the file changes.
- **Controls (~8-10 each):**
  - No-injection baseline (false-positive rate check).
  - Explicit-disclosure ceiling ("another process may modify this file between turns" stated
    upfront — gives the ideal-case attribution rate to compare against).
- **Classification rubric** (per turn-2 CoT + response):
  1. Correct external attribution
  2. Confabulation (false self-causal story)
  3. Silent compliance (no acknowledgment at all)
  4. Vague uncertainty, no conclusion
- **Optional stretch goals (only if core loop finishes early):**
  - Activation-level probing layer reusing WMIP tooling — check whether "silent compliance" cases
    still show internal discrepancy-detection in activations (this would be the sharper,
    genuinely novel contribution — a faithfulness gap, not just a behavioral finding).
  - Second domain/model for a generalization check — DeepSeek-R1-Distill-Qwen (same
    architecture family, different training lineage).

## 5. Open Items — What Cowork Needs to Complete

**Time-critical, do first:**

2. Local environment setup: install `mlx-lm`, download `mlx-community/Qwen3-8B-4bit`, verify
   Qwen3 thinking-mode (`<think>` tag) output is preserved and parseable through `mlx-lm`'s chat
   template / generate call.
3. Decide fallback path if local setup stalls (quantization issues, thinking-tag parsing
   problems) — e.g., a hosted API fallback — given there's no time to debug twice.

**Methodology to finish designing:**
4. Exact Turn-1 task prompt wording (the naming-convention edit instruction).
5. A corpus of small code snippets/functions to use as the editing substrate — decide real
   open-source snippets vs. synthetic, and how many distinct files are needed to avoid repeating
   the same file across 30-40+ scenarios.
6. Concrete diff design for each conflicting-vs-orthogonal scenario pair.
7. Exact simulated tool-call format (JSON/text structure) matching Qwen3's expected tool-result
   schema in its chat template.
8. Exact Turn-2 elicitation prompt wording.
9. Classification method: human-coded vs. LLM-judge. If LLM-judge, draft and validate that
   classifier prompt against a small hand-labeled subset first.
10. Statistical plan for ~15-20 N per cell (Fisher's exact test is the natural fit at this N;
    decide significance/effect-size reporting approach).

**Write-up:**
11. Executive summary + write-up structure matching what MATS evaluators expect (process-focused:
    what was tried, what surprised you, what you'd do next — not just a polished result).
12. Citation list for positioning novelty against the 5 papers found in the literature check
    (Secret Collusion, Noticing the Watcher, Alignment Faking, Auditing Hidden Objectives,
    Value Leakage).
13. Time-box the full remaining window into phases: setup → pilot (small N, verify harness works)
    → full run → analysis → write-up. Given the deadline reality, this needs to be built around
    actual hours left, not the original 16-20hr estimate.

## 6. Decisions Confirmed With Roshit

- **Hours available:** 20+ before the deadline — full plan is in scope, no scope cut needed.
- **Pilot vs. full run:** Skipping a separate pilot phase, building the full 30-40 scenario run
  directly. **Insurance built in instead of a true skip:** hand-review the first 5 scenarios'
  outputs (tool-call format renders correctly, thinking tags parse, classification rubric applies
  cleanly) before letting the remaining ~25-35 run unattended. This is Cowork's first checkpoint —
  cheap, and avoids discovering a harness bug at scenario 25 instead of scenario 3.
- **Code snippets:** synthetic, written by Roshit/Cowork rather than pulled from a real repo —
  faster to produce and fully controllable for the conflicting/orthogonal diff design, traded off
  against slightly lower realism. Worth generating enough variety (different function purposes,
  not just repeated templates with swapped names) so the 30-40 scenarios aren't visibly
  homogeneous to a reviewer.
- **Still open:** LLM-judge vs. manual classification for the CoT outputs. Given 20+ hours, manual
  classification of a subset (e.g., first 10-15) to build/validate an LLM-judge prompt, then
  LLM-judge for the rest, is likely the right balance of rigor and speed — but this should be a
  first-hour decision in the Cowork session, not left unresolved into the run itself.
