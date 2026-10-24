# QA Scanner Functional Bug Lab

A small, deterministic local website with **20 real functional bugs** and **healthy
counterparts**, used as a known-answer target for QA Scanner (issue #626). It answers one
question: *when a site has a real navigation, form, click, toggle or calculation bug, does the
scanner find it and flag it as a bug?*

The site is "Acme Outfitters", an ordinary-looking store in plain HTML and vanilla JavaScript,
served by a standard-library Python server. No build step, login, database, external API,
randomness or timers.

## v2: built for the default scanner budget

The first scan of v1 (scan `1cad9859`, 2026-10-05) found 0/10. Two of the reasons were about the
lab rather than the scanner. v2 removes both, so the next scan's misses point at the scanner:

- **Coverage.** v1 had 21 pages and the scanner stops at `MAX_PAGES=10`, so only 3 bug pages were
  reached. v2 has **10 routes in total**: each category's two bugs and its healthy control share
  one page.
- **Ambiguous targets.** Every control has a unique accessible name ("Add Trail Bottle to
  wishlist", "Remove Blue Mug", "Email for newsletter"), so a selector cannot land on the healthy
  twin.

Every expected result is visible on the page: a counter next to the wishlist buttons, a status
line under each switch, the confirmation or error text spelled out under each form, the arithmetic
rule under each calculator. NAV-001 has a **correct `href`** and a wrong client-side route, so an
oracle built from the `href` expects the right page and then sees the wrong one load.

## Ground rules

- Every bug is a real behavioral defect a developer could ship: a router-table typo, an
  off-by-one, `parseInt` on a decimal, a SKU typo. No served page names or hints at a bug.
- `expected_bugs.json` and this README live **outside `site/`** and are never served.
- No scanner-specific hooks: no `data-bug` attributes, no test ids for the scanner.
- Toggles use `<button role="switch" aria-checked>` and accordion `<button aria-expanded
  aria-controls>` with `role="region"` panels.

## Layout

```text
qa-bug-lab/
├── README.md            this file
├── expected_bugs.json   ground truth: bugs, healthy controls, routes, scoring rules (not served)
├── server.py            static server + POST /api/contact, /api/subscribe (stdlib only)
├── verify_lab.py        Playwright self-check: bugs reproduce, healthy controls work, reachability
└── site/
    ├── index.html, 404.html, favicon.svg, assets/
    ├── navigation/  forms/  buttons/  toggles/  calculators/
    └── pricing/  careers/  returns/
```

## Run the site

```bash
cd qa-bug-lab
python3 server.py                  # http://127.0.0.1:8765/
python3 server.py --host 0.0.0.0   # reachable from Docker containers / other machines
```

### Deploying

The forms need the two API endpoints below, so host it where Python runs (Render, Railway, Fly,
a VM), not on a static host such as GitHub Pages. Start command: `python3 server.py`, with
`HOST=0.0.0.0` set; `PORT` is read from the environment (default 8765). No dependencies.

| Endpoint | Body | 200 | 400 |
|---|---|---|---|
| `POST /api/contact` | `{name, email, message}` | `{"ok": true}` | `{"ok": false, "error": "..."}` |
| `POST /api/subscribe` | `{email}` | `{"ok": true}` | `{"ok": false, "error": "Please enter a valid email address."}` |

## Routes (10)

| Route | Contents |
|---|---|
| `/` | links to the 5 feature pages |
| `/navigation/` | NAV-001, NAV-002, healthy links Careers and Returns |
| `/forms/` | FORM-001, FORM-002, healthy back-in-stock form |
| `/buttons/` | CLICK-001, CLICK-002, CART-001 to CART-004, healthy wishlist button, healthy basket product and saved-for-later list |
| `/toggles/` | TOGGLE-001, TOGGLE-002, healthy switch and accordion |
| `/calculators/` | CALC-001 to CALC-008, healthy checkout calculator, healthy shipping, cart review and invoice |
| `/pricing/`, `/careers/`, `/returns/` | destination pages |
| `/shipping-policy/` | intentionally missing (HTTP 404), target of NAV-002 |

## Bugs

| ID | Route | User action | Expected visible result | Actual result |
|---|---|---|---|---|
| NAV-001 | `/navigation/` | Click Store menu "Pricing" | Pricing page (`/pricing/`) | Careers page (`/careers/`) |
| NAV-002 | `/navigation/` | Click "Shipping policy" | Shipping policy page, HTTP 200 | HTTP 404 "Page not found" |
| FORM-001 | `/forms/` | Fill Contact support validly, click "Send message" | "Thanks, Ada Lovelace. Your message has been sent." | Nothing at all |
| FORM-002 | `/forms/` | "not-an-email" in "Email for newsletter", click "Subscribe" | "Please enter a valid email address." | "You're subscribed. ..." (server said 400) |
| CLICK-001 | `/buttons/` | Click "Add Trail Bottle to wishlist" | Saved to wishlist 0 → 1 | Stays 0 |
| CLICK-002 | `/buttons/` | Click "Remove Blue Mug" | Blue Mug removed | Red Pen removed |
| CART-001 | `/buttons/` | Click 'Add Trail Stove to basket' once | 'Items in basket' 0 → 1 | Shows 2 (one row, $45.00) |
| CART-002 | `/buttons/` | Click 'Add Rain Poncho to basket' | 'Rain Poncho $22.00' row | 'Camp Stool $19.00' row |
| CART-003 | `/buttons/` | Click 'Add Head Lamp to basket' once | One row, count 1, total $20.00 | Two rows, count 2, total $40.00 |
| CART-004 | `/buttons/` | Add Camp Mug twice, click 'Empty basket' | Count 0 | List empty, total $0.00, count still 2 |
| TOGGLE-001 | `/toggles/` | Click "Email notifications" switch | OFF → ON, "are on." | Stays OFF |
| TOGGLE-002 | `/toggles/` | Click "How long does shipping take?" | Answer shown | Stays collapsed |
| CALC-001 | `/calculators/` | Read Bulk order total | $24.00 + $14.00 + $20.00 = **$58.00** | **$35.50** |
| CALC-002 | `/calculators/` | Read Sales tax (200.00 at 8.25%) | **$16.50** / $216.50 | **$16.00** / $216.00 |
| CALC-003 | `/calculators/` | Apply SAVE10 to the default checkout | Tax **$2.78**, total **$36.53** | Tax $3.09 (before discount), total $36.84 |
| CALC-004 | `/calculators/` | Order subtotal 50.00 | Shipping **$0.00** (free from $50.00) | $5.00 |
| CALC-005 | `/calculators/` | Gift box quantity 2 → 5 | Total **$34.00** | Total stays $16.00 |
| CALC-006 | `/calculators/` | Remove Pen from the cart review ($24.50) | Total **$20.00** | $23.00 |
| CALC-007 | `/calculators/` | Payment received 100.00 on INV-204 | Amount due **$362.00** | $462.00 |
| CALC-008 | `/calculators/` | Small order 0.10 at 5% | Tax **$0.01** (half cent rounds up) | $0.00 |

Steps, root causes, severities and healthy counterparts are in `expected_bugs.json`.

## Healthy controls (false-positive probes)

| Route | Control | Behavior |
|---|---|---|
| `/navigation/` | Store menu "Careers", Help "Returns" | open the named page, HTTP 200 |
| `/forms/` | Back-in-stock "Notify me" | valid → confirmation + cleared; invalid → error |
| `/buttons/` | "Add Summit Jacket to wishlist", Saved for later "Remove …" | count +1; removes exactly that item |
| `/toggles/` | "Text message alerts", Account questions | flips OFF/ON; opens and closes |
| `/calculators/` | Checkout | $37.50 / $3.09 / $40.59 |
| `/calculators/` | Shipping 49.99 / 60.00, cart review (remove Mug), invoice with no payment | $5.00 / free; $12.50; $462.00 due |

## Verify the lab

```bash
"../ai-qa-scanner/.venv/bin/python" verify_lab.py --start-server
"../ai-qa-scanner/.venv/bin/python" verify_lab.py --base-url http://127.0.0.1:8765
```

It drives Chromium as a user would and exits with 0 only if every bug reproduces, every healthy
control works, every route is reachable from `/` within the 10-page budget, and no page throws a
JS error. A bug that stops reproducing fails its check.

## Scoring a QA Scanner run

Two bugs share each feature route, so match scanner output (`qa_bugs`, `qa_findings`,
`qa_test_cases`) on **route + control name**. For each bug, record detected / misclassified /
missed (definitions in `expected_bugs.json` → `scoring`). Any bug on a healthy control or a
destination page is a false positive. Also record `FAILURE_TRIAGE_MODE`: with the default `off`,
failing tests file no bugs.
