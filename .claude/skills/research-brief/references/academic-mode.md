# Academic Paper Mode

Activate when the input is a peer-reviewed paper, conference proceeding, thesis, or academic preprint.

Detection signals: DOI present, "Abstract" section, "et al." citations, journal name, "p-value", "n=", methodology section.

---

## IMRAD Extraction Template

Pull these 5 sections explicitly from the paper before synthesizing.

### 1. Introduction
- What problem does the paper address?
- Why does it matter? What gap in the literature does it fill?
- What is the research question or hypothesis?

### 2. Methods
- Study design (RCT, observational, survey, meta-analysis, case study, etc.)
- Sample: who/what was studied, how many (n=), how selected
- Data collection: how was data gathered?
- Analysis approach: statistical method, model, framework used
- Reproducibility: are steps clear enough to replicate?

### 3. Results
- Key numbers and patterns (exact figures, not paraphrases)
- Statistical significance where reported (p-values, confidence intervals, effect size)
- Primary outcome vs. secondary outcomes

### 4. Analysis (Discussion)
- What do the results mean?
- How do results compare to prior work?
- Alternative explanations the authors considered

### 5. Discussion (Implications + Limitations)
- Practical implications for the domain
- Study limitations (sample size, generalizability, confounds)
- Future work suggested by authors
- Conflicts of interest disclosed?

---

## Quality Signals vs. Red Flags

| Green (Trust) | Red (Scrutinize) |
|---|---|
| Peer-reviewed venue | Predatory journal (check Beall's List) |
| Clear methodology, reproducible steps | No methodology section |
| Statistical significance reported | Claims without supporting data |
| Limitations openly acknowledged | Funded by entity benefiting from specific results |
| Conflicts of interest disclosed | Single small sample, no comparison group |

---

## Comparative Synthesis (2–5 Papers)

Use when comparing multiple papers on the same question.

### Comparison Matrix

| Dimension | Paper 1 | Paper 2 | Paper 3 |
|---|---|---|---|
| Central thesis | | | |
| Study design | | | |
| Sample size & scope | | | |
| Key finding | | | |
| Credibility | High/Med/Low | | |
| Year published | | | |

### Synthesis Steps

1. **Convergent findings** — where papers agree (stronger signal — treat as established)
2. **Divergent findings** — where papers disagree (flag for further investigation)
3. **Gaps** — what no paper addresses (known unknown)
4. **Weight of evidence** — which position has strongest methodological support

---

## Citation Formats Quick Reference

### APA 7 (default for product research, business, social sciences)

**Journal article:**
Author, A. A., & Author, B. B. (Year). Title of article. *Title of Periodical*, *volume*(issue), pages. https://doi.org/xxxxx

**Book:**
Author, A. A. (Year). *Title of work: Subtitle*. Publisher.

**Web page:**
Author, A. A. (Year, Month Day). *Title of page*. Site Name. URL

**In-text:** (Smith & Jones, 2023) | Smith and Jones (2023) found... | 3+ authors: (Patel et al., 2022)

---

### IEEE (engineering, computer science, technical research)

**Journal:** [1] J. Smith and K. Jones, "Title of article," *J. Abbrev.*, vol. X, no. Y, pp. Z–Z, Month Year, doi: 10.xxxx.

**Conference:** [2] A. Patel et al., "Title," in *Proc. Conf. Name*, Year, pp. XX–XX.

**In-text:** As shown in [1]... | Multiple: [1], [3], [5]–[7]

---

### Chicago (humanities, history)

**Footnote:** 1. First Last, *Title* (Place: Publisher, Year), page.

**Bibliography:** Last, First. *Title*. Place: Publisher, Year.

---

### Harvard (UK/Australian academic)

**Format:** Author, A.A. (Year) *Title*. Place: Publisher. | Author (Year) 'Article title', *Journal*, Vol(Issue), pp. X–Y.

**In-text:** (Smith and Jones, 2023) | Smith and Jones (2023) argue that...

---

### MLA 9 (arts, humanities)

**Format:** Last, First. *Title*. Publisher, Year. | Last, First. "Article Title." *Journal*, vol. X, no. Y, Year, pp. Z–Z.

**In-text:** (Smith and Jones 45) | Smith and Jones argue "quote" (45).

---

### Format Decision Guide

| Context | Use |
|---|---|
| Product research, business, social sciences | APA 7 |
| Engineering, computer science, technical | IEEE |
| Humanities, history | Chicago or MLA |
| UK/Australian academic | Harvard |

---

## Integration with Research Brief Phases

When academic mode is detected:
- **Phase 1 (Research Scout):** Focus searches on citation databases (Google Scholar, Semantic Scholar, PubMed if relevant). Note publication venue quality.
- **Phase 3 (Synthesis Journalist):** Apply IMRAD extraction above. Use confidence labels: Verified (peer-reviewed, replicated), Reported (single study), Speculative (author inference, not data).
- **Phase 4 (Quality Editor):** Check that citations are formatted correctly if output requires them. Flag any papers showing red flags.
