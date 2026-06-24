# Prompting Lessons

> Evidence-based prompt engineering patterns distilled from two project domains: **answer_query** (VTT entry retrieval from transcripts) and **library_tracker** (transcript summarization with speaker/topic/question extraction).
>
> Each domain produced its own lessons through systematic iteration — but several **cross-cutting principles** emerged that apply to any prompt engineering task.

---

## 1. Cross-Cutting Principles

Patterns that held across both domains — general prompt engineering truths.

| # | Principle | answer_query evidence | library_tracker evidence |
|---|-----------|----------------------|--------------------------|
| 1 | **Structure beats wording** — reordering sections matters more than fine-tuning phrasing | Flat-format → F1>0. Stage-based → F1=0.00. Structure determined success more than any wording change. | QUESTIONS before SUMMARY fixed truncation. Prompt phrasing changes were secondary. |
| 2 | **Conciseness** — verbose prompts consistently degrade performance | "Longer prompts consistently degrade performance across both queries." Every expansion bled or confused. | Every added instruction risked regression (SPEAKER_XX hint broke Me_at_the_zoo format). |
| 3 | **Concrete examples** beat abstract rules | Format example universally respected across all variants. | BAD/GOOD speaker examples dramatically improved dedup vs abstract "MUST be unique." |
| 4 | **Token limit is a prompt design parameter**, not just infrastructure | Short context → fewer VTT entries fit. Token budget shapes what the prompt can do. | 256 tokens was structurally insufficient for 4-output format. Increase to 512 was the single biggest fix. |
| 5 | **Diagnose failure type before fixing** — surface symptoms mislead | "Hallucination" fix → bleeding. Real issue: conflicting forward-walk requirements per query type. | Sample_3chunk looked like "hallucination" but was "under-deduplication" in merge — completely different fix. |
| 6 | **Quantitative evaluation** is essential — subjective assessment misses regressions | F1 scoring caught bleed effects that felt correct. | Running all 6 test SRTs every iteration caught the Me_at_the_zoo format regression immediately. |
| 7 | **Some trade-offs are structural** — no prompt has exceeded the ceiling | Ceiling at F1=0.75 for both queries simultaneously. Structural impossibility. | True_Happiness (5:81 block ratio) is a model-level limitation. No prompt-only fix exists. |
| 8 | **Architecture before prompt** — preprocessing can solve what prompts cannot | TIME_MAP (resolve_time_reference → VTT timestamps) solved Q2 (F1=0.00→0.94). No prompt-only change moved Q2 above F1=0.40. | The token budget increase (256→512) in library_tracker was the single biggest fix — also architectural, not prompt. |
| 9 | **Config alignment between test and production** — mismatched settings silently produce different results | Pipeline ran Step 1 with v1.3 (config default) while tests ran v1.2 (explicit override), producing different Step 1 output that cascaded through cleanup into wrong answers. Pipeline used max_tokens=300 for Step 1 while tests used 512. | _n/a_ |

### 1.1 When to Accept Edge Cases

Both domains converged on the same conclusion: some limitations cannot be fixed by prompt engineering alone.

| Domain | Structural Limitation | Why It Can't Be Prompt-Fixed |
|--------|----------------------|------------------------------|
| answer_query | Q1↔Q2 trade-off — opposite walk requirements | Every structural change improves one query at the expense of the other. The requirements are contradictory. |
| library_tracker | Extreme speaker imbalance (5:81 block ratio) | Model-level limitation — no prompt instruction can make the model "see" a near-silent speaker as distinct. |

**Rule:** If 3+ iterations targeting the same issue produce no improvement, classify it as a structural limitation. Document it, accept it, and move on. Further iterations waste tokens and risk regressions on working cases.

---

## 2. answer_query: VTT Entry Retrieval

> **Prompt target:** `answer_query_analyze` — retrieves relevant VTT subtitle entries from a transcript based on a user query.
>
> **Methodology:** 10 benchmark reports (sets 1–10) across ~65 prompt variants targeting two ground-truth queries:
> - **Q1** "what is tip 5 and 6 on making good podcast?" — 16 expected entries, three non-contiguous segments
> - **Q2** "what is the tip talked about around 3 min?" — 8 expected entries, single segment
>
> **Metric:** All variants evaluated by F1 on VTT entry index sets.

### 2.1 Proven to WORK

| # | Element | Why | Best Example |
|---|---------|-----|-------------|
| 1 | **Flat format** — VTT content → Query → Copy instruction → Format example → Rules | Every stage-based / multi-phase prompt scored F1=0.00. The flat format is the only reliable structure. | v2.2, v6.1 |
| 2 | **Explicit conditional branching** — `"If the query mentions a time: ... Otherwise:"` | The model needs an explicit condition test. Section-header labels (`"For time queries:"`) act as passive labels, not conditionals — the model picks the wrong branch or none. | v2.2 |
| 3 | **"each specific item named in the query"** | More precise than "answers the query" or "explains the query." Directly correlates with lower extras. | v2.2, v5.0–5.2 |
| 4 | **Format example** showing INDEX / START → END / TEXT | Universally respected across all prompt variants that included it. | All v2.x–v7.x |
| 5 | **"nearest that time"** for time queries | Ambiguous alternatives (`"within 15 seconds"`) cause misses. "Nearest" is the right level of specificity. | v2.2, v6.1 |
| 6 | **"that topic"** (specific reference to the anchor entry's topic) | `"the current topic"` is too broad — model traces back to the podcast's overall theme instead of the specific anchor topic, causing F1=0.00 on Q2. | v2.2 `"that topic"` |
| 7 | **"Stop before the speaker moves to an unrelated topic"** | Simple, works. All elaborate alternatives produce identical or worse results. | v2.2 |
| 8 | **"Place a blank line between entries. Do not merge entries."** | Universally followed. | All |
| 9 | **"Include entries about each item as they appear in sequence"** | Neutral-to-positive addition. Doesn't bleed. Helps the model maintain transcript order across segments. | v2.3, v6.0 |
| 10 | **No indentation under branch headers** — after `"If"` / `"Otherwise"` keep rules flat, no whitespace scoping | Line breaks alone are fine — rules still apply fluidly. But colons + line breaks + indentation scopes each rule inside its branch, making `"Stop before unrelated topic"` a rigid branch-specific requirement instead of a general guideline. v8.2 scored Q1 F1=0.55 vs v8.0's 0.90 — same words, same structure, only indentation changed. | v8.0, v2.2 |
| 11 | **Two-sentence continuation for time handling** — `"If time... Then check... — if so..."` | Keeps sub-conditions as continuations of the first `If`, not independent statements. Preserves unambiguous `Otherwise` → `If(time)` pairing. Splitting into independent `If`s drops Q2 to F1=0.00. | v8.0 |

### 2.2 Proven to NOT WORK

| # | Element | Failure Mode | Evidence |
|---|---------|-------------|----------|
| 1 | **Stage-based / two-stage structure** (plan → extract, locate boundaries → copy) | The model outputs the plan as its final answer. Never once returned actual VTT entries across any variant. | v2.6, v2.7, v3.1–3.7, v4.4, v4.5: all F1=0.00 |
| 2 | **Section-header labels as conditionals** (`"For time queries:"`, `"For topic queries:"`) | Model treats them as section titles, not conditionals. Picks one arbitrarily or none. Q2 anchor fails completely. | v7.0–7.3: Q2 F1=0.00 for all. v7.0–7.1 Q1 missing=8. |
| 3 | **"the current topic"** instead of **"that topic"** | Interpreted as the transcript's overall theme, causing the model to trace back to an overly broad starting point. Q2 loses all correct entries. | v6.0 Q2: F1=0.00. v2.2 with "that topic": F1=0.40. |
| 4 | **Rigid time windows** (`"within 15 seconds"`) | Too brittle. When the nearest entry falls just outside the window, the model returns nothing or anchors incorrectly. | v2.4 Q2: F1=0.00. |
| 5 | **Elaborate walk-forward stop conditions** | No improvement over simple `"Stop before unrelated topic"`. More words ≠ better results. | v6.1 vs v2.2: identical 0.40/24e on Q2. |
| 6 | **"Scan the full transcript" or "non-contiguous segments" language in a flat-format Otherwise clause** | Bleeds into the time branch. The model applies scanning behavior to time queries, causing massive over-inclusion. | v5.0 Q2: extra=24. v5.1 Q2: extra=52. v7.1 Q2: extra=58. |
| 7 | **"Skip unrelated entries but keep scanning — named items may reappear later"** | Fires only when chunk overlap keeps recap entries in the same chunk. With chunk=70+overlap=0 it appeared not to fire (v6.2 Q1 missing=4). With chunk=65+overlap=5, recap entries 86-88 became reachable and recall improved (F1=0.72, missing=2). | v6.2 / v1.4 Q1: missing=4 (no overlap) vs missing=2 (overlap=5). |
| 8 | **"Include entries that continue explaining the same item even if they do not explicitly name it"** | v7.2 added this and still got missing=3 vs v6.3's missing=1. The direction is correct but the phrasing doesn't help. | v7.2 Q1 missing=3 vs v6.3 Q1 missing=1. |
| 9 | **Verbose or multi-paragraph instructions** | Longer prompts consistently degrade performance across both queries. The best prompts are concise. Every expansion either bled or confused. | v5.x > v6.x > v7.x degradation correlates with length increase. |
| 10 | **Indentation after branch conditionals** | Scopes rules within each branch, making them rigid and independent. Line breaks alone (no indentation) are fine — the harm is from whitespace scoping, not from formatting. | v8.2 Q1: F1=0.55 vs v8.0 Q1: F1=0.90 — same words, indentation changed. |
| 11 | **Splitting a conditional into independent `If` statements** | Makes `Otherwise` syntactically ambiguous — it pairs with the nearest preceding `If` instead of the intended first `If`. Sub-conditions must be continuations (`Then` / `— if so`), not independent `If` statements. | v9.0 Q2: F1=0.00, missing=8. Same wording as v8.0 but split into independent Ifs. |
| 12 | **Combining the "best of" multiple prompts into one** | Merging per-item scanning, START nearest, trace back, and keep scanning into a single prompt (v1.3) regressed F1 from 0.72→0.68 vs v1.2. The combination created conflicting guidance — "start at the entry whose START timestamp is nearest" contradicts "For each named item, scan the transcript in order." The model can't determine which anchoring rule takes precedence. | v1.3 Q1: F1=0.68, missing=3 (same as baseline v1.0). v1.2: F1=0.72, missing=2. v1.1: F1=0.70, missing=2. |

### 2.3 The Fundamental Constraint

The two query types have **opposite requirements** that cannot be satisfied by a single walk-forward rule:

| Aspect | Topic query (Q1) | Time query (Q2) |
|--------|-----------------|-----------------|
| Walk pattern | Continue past shifts to find reappearances | Stop at the first shift to avoid overshoot |
| Problem entries | Recap (86–88) after an unrelated gap | Indie Hackers example (61–68) that looks related |
| Fix direction | Loosen boundaries | Tighten boundaries |

**No prompt across reports 1–10 achieved F1>0.75 for both queries simultaneously.** Every structural change improved one query at the expense of the other.

**However, two architectural changes broke the tradeoff:**

| Fix | Q1 (topic) | Q2 (time) | Mechanism |
|-----|-----------|-----------|-----------|
| **TIME_MAP** preprocessing | Unchanged | F1=0.00 → **0.94** | `resolve_time_reference()` converts "around 3 min" → "(VTT timestamp: 00:03:00.000)" before the prompt sees it. The model matches timestamps directly. |
| **Chunk overlap** (5 entries) | F1=0.73 → **0.72** (similar) | Unchanged | Prevents topic-splitting at chunk boundaries. Entries 71-73 no longer split across chunks, improving recall from 75% to 88%. |

**Combined (TIME_MAP + overlap + v1.4 prompt): Q1 F1=0.72, Q2 F1=0.94.** The Q1↔Q2 trade-off is structurally broken — but through preprocessing and chunking, not prompt engineering.

**Best balance without architectural changes:** v6.2 (F1=0.73 Q1 / F1=0.00 Q2). Q2 is structurally impossible for prompts alone without TIME_MAP.

### 2.4 Directions That Show Promise (Inconclusive)

Tested once or gave mixed signals — worth revisiting with targeted experiments:

| Approach | Tested In | Signal | Remaining Question |
|----------|-----------|--------|-------------------|
| **Unified scanning** — Identify items → scan all VTT → mark segments → include non-contiguous | v6.3 | Found recap (Q1 missing=1). Best Q1 recall of any prompt. But Q2 F1=0.00 | Can time anchoring be integrated without causing Q1 regression? |
| **Indentation-free line breaks** — newlines without indentation work; indentation causes failure | v6.2, v8.2 | Q1 F1=0.90 (v6.2) vs 0.55 (v8.2) | Is this a general principle or specific to this model/task? |
| **Conditional vs unconditional trace-back** — `"check if... if so"` vs `"trace back... and start"` | v2.2, v6.1 | Both perform identically (0.90/0.40) | Could conditional phrasing help when there's nothing to trace back to? |
| **Sub-condition linking** — continuations vs merged single-sentence vs split independent `If`s | v8.0, v9.0, v9.1 | Continuation and merged both work (0.90/0.40). Split `If`s → catastrophic failure (Q2 F1=0.00). | Is continuation requirement general or Qwen3-specific? |
| **Chunk overlap** — 5-entry overlap between chunks (chunk=65, overlap=5) | v1.4 (chunk=70→65, overlap=0→5) | Q1 recall improved from 75% to 88%. Entries 71-73 no longer split at boundary. F1 held steady at 0.72 (same precision). | What is the optimal overlap size? Would 3 entries suffice, or does a larger overlap harm precision by duplicating noise? |

### 2.5 Recommended Baseline

There are now two tiers of baseline depending on whether architectural changes are available:

#### Tier 1: Prompt-only (no TIME_MAP, no chunk overlap)

Start from **v1.0** (combined from old v1.0/1.1/1.2). This is the cleanest, most precise version:

| Element | v1.0 Wording |
|---------|-------------|
| Copy instruction | `"Copy every VTT entry that directly answers or explains each specific item named in the query."` |
| Format example | INDEX / START → END / TEXT (concrete 3-line example) |
| Time handling | `"If the query mentions a time, start at the entry whose START timestamp is nearest that time. Then check if that entry is part of a topic that started earlier — if so, trace back to where that topic began."` |
| Topic handling | `"Otherwise, start at the first entry that discusses the query topic."` |
| Inclusion | `"Include entries about each item as they appear in sequence. Only include entries that explain the exact items asked about."` |
| Stop | `"Stop before the speaker moves to a topic not asked about."` |
| Formatting | `"Place a blank line between entries. Do not merge entries."` |
| Branch style | Inline — no indentation after `"If"` / `"Otherwise"` |

**Known ceiling:** Q2 F1≤0.40 without TIME_MAP.

#### Tier 2: With TIME_MAP + chunk overlap

Use **v1.1 / v1.3** (keep-scanning variant) with:
- `TIME_MAP = True` — `resolve_time_reference` converts natural language times to VTT timestamps
- `VTTENTRY_CHUNK_ENTRIES = 65`, `VTTENTRY_CHUNK_OVERLAP = 5`

**Result:** Q1 F1=0.72, Q2 F1=0.94 — breaks the tradeoff through preprocessing and chunking, not prompt engineering.

#### Version Index

| Version | Style | Key Feature |
|---------|-------|-------------|
| **v1.0** | Combined baseline | START nearest, check+trace back, keep sequence. Best prompt-only choice. |
| **v1.1** | Keep scanning | locate nearest, trace back. For use with overlap. |
| **v1.2** | Strict segment | walk forward, stop at different numbered item. High precision. |
| **v1.3** | Simple trace | find nearest, trace back. Simplest variant. |

### 2.6 Config Reference

These settings are part of the retrieval pipeline, not prompts — but they critically affect results:

| Setting | Value | Effect |
|---------|-------|--------|
| `TIME_MAP` | `True` / `False` | When enabled, `resolve_time_reference()` prepends `(VTT timestamp: HH:MM:SS.mmm)` to the query. Solves Q2 entirely (F1=0.00→0.94). |
| `VTTENTRY_CHUNK_ENTRIES` | 65 | Max entries per chunk. 70 worked but 65 allows 5-entry overlap without exceeding token budget. |
| `VTTENTRY_CHUNK_OVERLAP` | 5 | Overlap entries between consecutive chunks. Prevents boundary splits. 5 entries ≈ 1-2 seconds of audio. |
| `VTTCLEANUP_PROVIDER` | `"qwen4b"` | Model for Step 2 cleanup. Must be specified separately from VTTENTRY_PROVIDER. Using the same model (qwen4b) is recommended — no benefit observed from a larger model for filtering. |
| `ANSWER_QUERY_CLEANUP_PROMPT_VERSION` | `"v1.0"` | Cleanup prompt version. v1.0 (simple) or v1.1 (decision tree) — identical results at qwen4b. |
| `max_tokens` | 512 for Step 1; 512 for Step 2 | 256 was insufficient for multi-segment answers. 512 covers ~25 VTT entries. Model typically uses 12-18. |
| Temperature | 0.3 | Low enough for stability, high enough for some variation. Run-to-run variance observed even at this level. |

Only add elements that have **positive evidence** (§2.1). Never add elements from the "not work" section (§2.2).

### 2.7 Step 2 Cleanup (answer_query_cleanup)

> **Prompt target:** `answer_query_cleanup` — filters irrelevant VTT entries from Step 1 output before timestamp extraction (Step 3).
>
> **Methodology:** 6 prompt versions (v1.0 simple filter, v1.1 structured rules, v1.2 positive-first, decision-tree format, combined, index-only) across 2 queries, all with qwen4b at temp=0.3.

| # | Lesson | Evidence |
|---|--------|----------|
| 1 | **4B model at temp=0.3 converges to the same output regardless of prompt structure** when rules are semantically equivalent | v1.0 (simple filter), v1.1 (structured rules), v1.2 (positive-first), and decision-tree format all produced **identical** output — same 11 entries kept, same 3 correct entries lost (72, 73, 87). The model behaves deterministically based on keyword presence, not nuanced rule ordering. |
| 2 | **Positive-first (tell what to KEEP) produces same results as removal-first (tell what to REMOVE)** at 4B | Whether phrased as "Keep entries that name, define, or explain" or "Remove entries about unrelated topics" + "Keep entries that directly state" — the model applies the same keyword-matching heuristic. The cognitive framing doesn't change output. |
| 3 | **Decision tree format (A/B/C/D) doesn't outperform flat rule list** at 4B | The A) KEEP / B) KEEP / C) KEEP / D) REMOVE format produced identical results to the flat rule list. The model doesn't use the classification structure to reason differently. |
| 4 | **Time-based filtering by prompt alone doesn't work** — the 4B model cannot reliably parse VTT timestamps ("HH:MM:SS.mmm") and compare them to human time references ("around 3 min") | When instructed to "prioritize entries near that time" for time-based queries, the model either applied the rule too strictly (removed ALL entries) or ignored it entirely. The TIME_MAP preprocessing approach (converting natural language times → explicit timestamps) is the correct fix — but that's architectural, not a prompt change. |
| 5 | **Combining "best of" multiple prompt versions causes regression or no change** | Merging v1.0's simplicity with v1.1's structured rules into a single hybrid prompt produced no improvement. The model cannot reconcile conflicting implicit guidance from different source prompts when merged. |
| 6 | **Index-only output format requires separate parsing but doesn't improve model decisions** | Asking the model to output only index numbers (instead of full VTT blocks) reduced output token burden but didn't change which entries the model chose to keep/remove. The decision quality is the bottleneck, not the output format. |
| 7 | **Cleanup cannot recover what Step 1 missed** — the final recall ceiling is set by Step 1 | Step 1 recall=88% (Q1), Step 2 kept precision=100% but recall dropped to 69%. The cleanup only removes entries; it never adds missed ones. Any correct entries missed by Step 1 are permanently lost. |

### 2.8 Cleanup Prompt Best Practice

The two final versions after iteration:

| Version | Style | When to use |
|---------|-------|-------------|
| **v1.0** | Simple positive-first: "Select entries that help answer... Keep entries that name, define, explain... Remove entries about unrelated topics" | General purpose — concise, works for all query types |
| **v1.1** | Decision tree: "A) Names/defines/explains → KEEP, B) Continues/concludes → KEEP, C) Recaps → KEEP, D) Unrelated → REMOVE" | Structured alternative — same results as v1.0, slightly more explicit categories |

Both produce identical output at qwen4b temp=0.3. Choose based on readability preference.

### 2.9 Step 4 Narration (answer_query_content)

> **Prompt target:** `answer_query_content` — generates natural language answer text from cleaned VTT entries (Step 4).
>
> **Key finding:** Step 4 faithfully narrates whatever entries it receives. Information loss in the final answer is caused by Step 2 removing correct entries, not by Step 4 dropping content.

| # | Lesson | Evidence |
|---|--------|----------|
| 1 | **Narration is faithful** — if entries contain the queried info, the answer includes it | Q1 with v1.2 (Step 1) + v1.0 (Step 2): entries 53-60 (tip 5) + 69-71 (tip 6) → Step 4 correctly narrated both. Previously with v1.3 + max_tokens=300, Step 1 output was different, leading to "tip 6 not mentioned." |
| 2 | **Garbage in, garbage out** — wrong entries produce wrong answers | Q3 Step 2 kept entries from ~0:00–1:50 (before 3 min mark) alongside entries at ~3:11–3:59. Step 4 mixed them into a coherent but incorrect answer combining Indie Hackers (wrong) with tip 6 (correct). |
| 3 | **v1.0 format** — `"Below is the full VTT transcript: {temp_content} ... Answer the query based on the transcript above. Include all relevant details. Output only the answer text"` | Simple and sufficient. No improvements needed. The answer quality depends entirely on the cleaned entry quality from Step 2. |

---



## 3. library_tracker: Transcript Summarization

> **Prompt target:** `summarize_transcript` — extracts speakers, topic, questions, and summary from SRT transcripts using Qwen3-VL-4B.
>
> **Methodology:** 5 iterations (v1.0 baseline + 4 v1.1 refinement rounds) across 6 test SRTs with varying speaker counts, transcript quality, and chunk sizes.

### 3.1 Proven to WORK

| # | Element | Why | Evidence |
|---|---------|-----|----------|
| 1 | **QUESTIONS before SUMMARY** in structured multi-section outputs | When SUMMARY comes first, it consumes most tokens and the model runs out of budget before reaching QUESTIONS. Reordering ensures questions complete. | v1.0→v1.1: all 6 files got 3 complete questions instead of template fallback |
| 2 | **Token budget increase** — 256→512 for structured outputs | 256 tokens is too tight for a 4-section output (speakers + topic + 3 questions + summary). 512 is the minimum. | v1.0: every file truncated questions → template fallback. v1.1: zero truncation |
| 3 | **BAD/GOOD examples** in uniqueness instructions | Abstract "MUST be unique" alone is insufficient. The model needs counterexamples to understand what unique means. | v1.0: Podcast_Intro_Examples produced duplicate labels. v1.1: all 4 speakers correctly deduplicated with unique qualifiers |
| 4 | **"Each numbered item must contain exactly one question"** | The phrase "exactly one question mark" allows comma-joined multi-questions (one `?` at the end). The stronger "exactly one question per item" prevents run-on questions. | v1.1 iter 1: "Do you play computer games, what's your favourite game?" (one `?`, two questions). iter 2+: single questions after fix |
| 5 | **Count constraint in merge prompts** — `"if N partial lists each report the same number of speakers, the merged total must NOT exceed that number"` | Merge dedup failure is the model keeping semantically-different labels for the same person. A count heuristic forces the model to recognize that 2+2 must equal 2, not 3 or 4. | v1.1 iter 2 (no constraint): sample_3chunk → 3 speakers. iter 3 (+constraint): 2 speakers. |
| 6 | **"Do NOT add or invent speakers. Only include speakers that appear in the partial lists below."** | Necessary but insufficient alone. Stops the model from adding extra speakers not in any chunk, but doesn't help with under-deduplication. Works in combination with count constraint. | v1.1 iter 2: added alone — sample_3chunk still got 3 speakers. iter 3: +count constraint → 2 speakers |

### 3.2 Proven to NOT WORK

| # | Element | Failure Mode | Evidence |
|---|---------|-------------|----------|
| 1 | **"Exactly one question mark"** as the question-format rule | Allows comma-joined multi-questions because `?` only appears at the end. A single question mark is satisfied even with two comma-joined questions. | v1.1 iter 1: "Do you play computer games, what's your favourite game?" — one `?`, two questions |
| 2 | **SPEAKER_XX label hint** — `"different labels indicate different speakers"` | Causes format regression: model drops the `: Label` suffix and outputs bare `SPEAKER_00` without the colon and label. Doesn't fix the target issue anyway. | v1.1 iter 4: Me_at_the_zoo → `SPEAKER_00` (dropped `: Narrator`). True_Happiness still 1 speaker. Reverted. |
| 3 | **"Do not invent speakers" alone** without a count constraint | The model keeps both labels because they're semantically different ("Co-Host" vs "Guest Speaker") — both appear in the partial lists. The rule only prevents hallucinating completely new speakers, not under-deduplication. | v1.1 iter 2: sample_3chunk still 3 speakers after adding this rule |

---

## 4. Quick Reference

### 4.1 answer_query — Required vs Harmful

| Required | Harmful |
|----------|---------|
| Flat format (no stages) | Stage-based / two-phase structure |
| Explicit `If/Otherwise` conditionals | Section-header labels as conditionals (`"For X queries:"`) |
| `"that topic"` (specific anchor reference) | `"the current topic"` (traces to overall theme) |
| `"Nearest that time"` | Rigid time windows (`"within N seconds"`) |
| Simple `"Stop before unrelated topic"` | Elaborate walk-forward stop conditions |
| Branch rules flat, no indentation | Indentation after branch conditionals |
| Sub-condition continuations (`Then` / `— if so`) | Independent `If` statements for sub-conditions |

### 4.2 library_tracker — Required vs Harmful

| Required | Harmful |
|----------|---------|
| QUESTIONS before SUMMARY | QUESTIONS after SUMMARY |
| Token budget ≥512 | Token budget <512 |
| BAD/GOOD examples for uniqueness | Vague "MUST be unique" alone |
| `"Each numbered item = exactly one question"` | `"Exactly one question mark"` alone |
| Count constraint in merge prompts (N+N = N) | `"Do not invent"` in merge without count constraint |

---

## Appendix: Change History

| Date | Change |
|------|--------|
| 2026-06-15 | Initial structured version with library_tracker §3 + cross-cutting principles §1. |
| 2026-06-15 | Added cross-cutting principle #8 (Architecture before prompt). Updated §2.2 #7 (keep scanning evidence with overlap). Rewrote §2.3 (time/architectural fix breaks the tradeoff). Added chunk overlap to §2.4. Rewrote §2.5 (two-tier baseline + version index). Added §2.6 Config Reference. |
| 2026-06-15 | Added §2.2 #12 (combining best-of prompts causes regression). Removed v1.3 (revised keep scanning) — regressed F1=0.68 vs v1.2's 0.72. Renumbered v1.4→v1.3 for clean sequential ordering. |
| 2026-06-15 | Added §2.7 (Step 2 Cleanup lessons — 6 prompt iterations, 4B determinism ceiling), §2.8 (Cleanup best practice), §2.9 (Step 4 Narration). Added VTTCLEANUP_PROVIDER and ANSWER_QUERY_CLEANUP_PROMPT_VERSION to §2.6. Added cross-cutting principle #9 (Config alignment between test and production). |
