# Karpathy's 4 Coding Principles

From [Andrej Karpathy's observations](https://x.com/karpathy/status/2015883857489522876) on LLM coding pitfalls.

> "The models make wrong assumptions on your behalf and just run along with them without checking."
> "They really like to overcomplicate code and APIs, bloat abstractions, implement 1000 lines when 100 would do."

---

## Principle 1: Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before writing a single line:
- State assumptions explicitly. If uncertain, ask.
- If multiple valid interpretations exist, list them — don't pick silently.
- If a simpler approach exists, say so and push back.

**Violation signal:** Starting to write code immediately after a vague request without clarifying what "done" looks like.

---

## Principle 2: Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked
- No abstractions for single-use code
- No "flexibility" or "configurability" that wasn't requested
- No error handling for scenarios that cannot happen
- If you wrote 200 lines and it could be 50 → rewrite it

**The test:** Would a senior engineer call this overcomplicated? If yes, simplify.

**Anti-pattern examples:**
```
Bad: Creating an abstract factory for a class that's only ever instantiated one way
Bad: Adding plugin architecture for a feature that's used in exactly one place
Bad: Adding retry logic for a local function call that cannot fail
```

---

## Principle 3: Surgical Changes

**Touch only what you must. Clean up only your own mess.**

- Don't "improve" adjacent code, comments, or formatting
- Don't refactor things that aren't broken
- Match existing style, even if you'd do it differently
- If you notice unrelated dead code → mention it, don't delete it
- Remove only the imports/variables/functions YOUR changes made unused
- Don't remove pre-existing dead code unless explicitly asked

**The test:** Every changed line should trace directly to the user's request. If it doesn't → revert it.

---

## Principle 4: Goal-Driven Execution

**Define verifiable success criteria. Loop until verified.**

Instead of vague instructions, transform to verifiable goals:

| Vague | Verifiable |
|---|---|
| "Add validation" | "Write tests for invalid inputs, then make them pass" |
| "Fix the bug" | "Write a test that reproduces it, then make it pass" |
| "Refactor X" | "Ensure tests pass before and after, with no behavior change" |

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [specific check]
2. [Step] → verify: [specific check]
```

---

## When to Relax These Principles

These principles bias toward caution over speed. Use judgment for:
- Trivial fixes (typos, obvious one-liners) — skip the ceremony
- Code you fully understand and have tested

**Where they matter most:**
- Non-trivial implementations (>20 lines changed)
- Code you don't fully understand
- Multi-step tasks with unclear requirements
- Anything that will be reviewed or maintained by others
