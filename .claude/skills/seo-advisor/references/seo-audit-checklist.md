# SEO Audit Checklist — 30-Point Framework

Technical + On-Page audit. Run against any site or priority page.
Score each item: ✅ Pass / ⚠️ Needs fix / ❌ Critical issue

---

## Section 1: Technical SEO (Foundation — fix first)

### Crawling & Indexing
- [ ] `robots.txt` — accessible at `/robots.txt`, correct syntax
- [ ] AI bots NOT blocked: GPTBot, PerplexityBot, ClaudeBot, Google-Extended
- [ ] `sitemap.xml` — exists, submitted to Google Search Console, < 50k URLs
- [ ] Sitemap contains only canonical, indexable URLs (no noindex pages)
- [ ] No "noindex" on pages that should rank

### Site Speed & Core Web Vitals (test at PageSpeed Insights)
- [ ] LCP (Largest Contentful Paint) < 2.5 seconds
- [ ] CLS (Cumulative Layout Shift) < 0.1
- [ ] INP (Interaction to Next Paint) < 200ms
- [ ] Page size < 3MB total (images compressed, JS bundled)

### Security & Protocol
- [ ] HTTPS across entire site (no mixed content warnings)
- [ ] No security certificate errors
- [ ] HSTS header present

### Mobile
- [ ] Passes Google Mobile-Friendly Test
- [ ] Responsive design (no horizontal scrolling)
- [ ] Touch targets ≥ 48px

### Redirects & Canonicals
- [ ] No redirect chains (301→301→301 = bad; 301→200 = good)
- [ ] No redirect loops
- [ ] Canonical tags present on all pages, pointing to correct URL
- [ ] www vs non-www redirects to one consistent version
- [ ] HTTP → HTTPS redirect working

---

## Section 2: On-Page SEO (Priority pages)

### Title & Meta
- [ ] Title tag: 50-60 characters, target keyword near the start, unique per page
- [ ] Meta description: 150-160 characters, includes keyword, compelling (drives clicks)
- [ ] Open Graph tags: title, description, image (for social sharing)

### Heading Structure
- [ ] One H1 per page (includes target keyword)
- [ ] H2/H3 hierarchy is logical (no skipping levels)
- [ ] Related/latent keywords in at least 2 H2s
- [ ] Target keyword in first 100 words of body text

### Content Signals
- [ ] No thin content pages (< 300 words for non-intentionally-short pages)
- [ ] Keyword cannibalization check: no 2 pages targeting the same primary keyword
- [ ] Images have descriptive alt text (keyword where natural, not stuffed)
- [ ] Internal links: 2-4 per piece, using descriptive anchor text (not "click here")
- [ ] External links: cite credible sources where claims are made

### AI Citation Readiness
- [ ] Definition block for main concept in first 300 words
- [ ] Numbered steps for any process content
- [ ] FAQ section with direct Q&A pairs
- [ ] Statistics cited with source name + year
- [ ] Schema markup present (FAQPage / HowTo / Article)

---

## Section 3: Site-Level Issues

### Duplicate Content
- [ ] No near-duplicate pages targeting same keyword (consolidate or canonical)
- [ ] Pagination handled correctly (rel="next/prev" or canonical to page 1)
- [ ] Print-friendly versions canonicalized if they exist

### Site Architecture
- [ ] Key content within 3 clicks from homepage
- [ ] No orphan pages (pages with zero internal links)
- [ ] URL structure: clean, descriptive, < 5 segments (no `/p=123?id=456&sort=asc`)

---

## Priority Action Framework

After completing the checklist, group findings:

| Priority | Criteria | Examples |
|---|---|---|
| **Critical** | Blocks indexation or ranking | noindex on key pages, AI bots blocked, redirect loops |
| **High impact** | Directly affects ranking | Core Web Vitals fail, missing H1, thin content |
| **Quick wins** | Easy fix, immediate benefit | Alt text, meta descriptions, internal links |
| **Long-term** | Requires planning | Content gap fill, site architecture redesign |

---

## Tools Reference

| Tool | Cost | Use For |
|---|---|---|
| Google Search Console | Free | Coverage, Core Web Vitals, keyword data |
| PageSpeed Insights | Free | Core Web Vitals per page |
| Google Rich Results Test | Free | Schema markup validation |
| Screaming Frog | Free (< 500 URLs) | Full site crawl |
| Ahrefs / Semrush | Paid | Backlinks, keyword tracking, competitor analysis |
