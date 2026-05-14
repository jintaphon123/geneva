# Description Optimization Guide

The `description` field in SKILL.md frontmatter is the primary mechanism that determines whether Claude invokes a skill. Optimize it after the skill content is stable — not before.

Offer to run this after creating or significantly improving a skill.

---

## How Skill Triggering Works

Skills appear in Claude's `available_skills` list with their name + description, and Claude decides whether to consult a skill based on that description.

**Critical insight:** Claude only consults skills for tasks it can't easily handle on its own. Simple, one-step queries like "read this PDF" may not trigger a skill even if the description matches perfectly — Claude can handle them directly. Complex, multi-step, or specialized queries reliably trigger skills when the description matches.

This means eval queries must be substantive enough that Claude would actually benefit from consulting a skill. Simple queries are poor test cases regardless of description quality.

Current tendency: Claude **undertriggers** — it doesn't use skills when they'd be useful. To combat this, make descriptions slightly "pushy": instead of "How to build a simple fast dashboard", write "How to build a simple fast dashboard. Make sure to use this skill whenever the user mentions dashboards, data visualization, or wants to display any kind of company data, even if they don't explicitly ask for a 'dashboard.'"

---

## Step 1: Generate Trigger Eval Queries

Create 20 eval queries — a mix of should-trigger and should-not-trigger. Save as JSON:

```json
[
  {"query": "the user prompt", "should_trigger": true},
  {"query": "another prompt", "should_trigger": false}
]
```

**Quality bar for queries — bad vs good:**

Bad: `"Format this data"`, `"Extract text from PDF"`, `"Create a chart"`

Good: `"ok so my boss just sent me this xlsx file (its in my downloads, called something like 'Q4 sales final FINAL v2.xlsx') and she wants me to add a column that shows the profit margin as a percentage. The revenue is in column C and costs are in column D i think"`

Queries must be realistic and detailed — include file paths, personal context, column names, company names, URLs, a little backstory. Some in lowercase or with abbreviations or casual speech. Mix lengths. Focus on edge cases rather than clear-cut examples.

**For should-trigger queries (8-10):** Cover different phrasings of the same intent — some formal, some casual. Include cases where the user doesn't name the skill explicitly but clearly needs it. Include uncommon use cases and cases where this skill competes with another but should win.

**For should-not-trigger queries (8-10):** Focus on near-misses — queries that share keywords or concepts with the skill but actually need something different. Adjacent domains, ambiguous phrasing where a naive keyword match would trigger but shouldn't, queries that touch what the skill does but in a context where another tool is more appropriate.

The most valuable negative tests are the genuinely tricky ones. "Write a fibonacci function" as a negative test for a PDF skill is too easy — it tests nothing.

---

## Step 2: Review With User

Present the eval set using the HTML template:

1. Read `assets/eval_review.html`
2. Replace placeholders:
   - `__EVAL_DATA_PLACEHOLDER__` → the JSON array of eval items (no quotes — it's a JS variable assignment)
   - `__SKILL_NAME_PLACEHOLDER__` → the skill's name
   - `__SKILL_DESCRIPTION_PLACEHOLDER__` → the skill's current description
3. Write to `/tmp/eval_review_<skill-name>.html` and open: `open /tmp/eval_review_<skill-name>.html`
4. The user can edit queries, toggle should-trigger, add/remove entries, then click "Export Eval Set"
5. File downloads to `~/Downloads/eval_set.json` — check Downloads for the most recent version (e.g., `eval_set (1).json`)

This step matters — bad eval queries lead to bad descriptions. Don't skip it.

---

## Step 3: Run the Optimization Loop

Tell the user: "This will take some time — I'll run the optimization loop in the background and check on it periodically."

Save the eval set to the workspace, then run from the skill-builder directory:

```bash
python -m scripts.run_loop \
  --eval-set <path-to-trigger-eval.json> \
  --skill-path <path-to-skill> \
  --model <model-id-powering-this-session> \
  --max-iterations 5 \
  --verbose
```

Use the model ID from your system prompt (the one powering the current session) so the triggering test matches what the user actually experiences.

While it runs, periodically tail the output to give the user updates on which iteration it's on and what the scores look like.

**What this does automatically:**
- Splits the eval set into 60% train and 40% held-out test
- Evaluates the current description (running each query 3 times for reliability)
- Calls Claude to propose improvements based on what failed
- Re-evaluates each new description on both train and test
- Iterates up to 5 times
- Selects winner by test score (not train score) to avoid overfitting
- Returns JSON with `best_description`

---

## Step 4: Apply the Result

Take `best_description` from the JSON output and update the skill's SKILL.md frontmatter. Show the user the before/after and report the scores.

```yaml
---
name: skill-name
description: <best_description goes here>
---
```
