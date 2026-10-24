#!/usr/bin/env python3
"""Verify the QA Scanner Functional Bug Lab with a real browser.

Checks, through user-level interaction only (no page internals):
  * every bug in expected_bugs.json reproduces exactly as documented,
  * every healthy control behaves correctly,
  * every page is reachable from the homepage (and only the intended route 404s),
  * no page throws an unexpected JavaScript error.

Usage:
  python verify_lab.py --start-server          # spawn server.py on a free port, verify, stop it
  python verify_lab.py --base-url http://127.0.0.1:8765

Requires Python Playwright with Chromium (the ai-qa-scanner virtualenv has both).
"""

from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import time
import urllib.request
from collections import deque
from collections.abc import Callable
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from urllib.parse import urljoin, urlparse

from playwright.sync_api import Page, expect, sync_playwright

LAB_DIR = Path(__file__).resolve().parent
EXPECTED = json.loads((LAB_DIR / "expected_bugs.json").read_text(encoding="utf-8"))
QUIET_MS = 800  # how long "nothing happened" is observed after an action


def money(value: Decimal) -> str:
    return f"${value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}"


def cents_round(value: Decimal) -> Decimal:
    return (value * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP) / 100


def path_of(page: Page) -> str:
    return urlparse(page.url).path


def h1(page: Page) -> str:
    return page.locator("h1").inner_text().strip()


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


class Lab:
    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base = base_url.rstrip("/")

    def open(self, route: str) -> None:
        response = self.page.goto(self.base + route, wait_until="load")
        check(response is not None and response.status == 200, f"{route} did not load with HTTP 200")

    def text(self, selector: str) -> str:
        return self.page.locator(selector).inner_text().strip()

    def list_items(self, list_id: str) -> list[str]:
        return [t.strip() for t in self.page.locator(f"#{list_id} li span").all_inner_texts()]

    def basket_rows(self) -> list[str]:
        return [" ".join(t.split()) for t in self.page.locator("#basket-list li").all_inner_texts()]

    def table_expectation(self, table_id: str) -> tuple[list[str], Decimal]:
        """Expected line totals and their sum, computed from the visible prices and quantities."""
        lines, total = [], Decimal("0")
        for row in self.page.locator(f"#{table_id} tbody tr").all():
            unit = Decimal(row.locator("td").first.inner_text().strip().lstrip("$"))
            qty = Decimal(row.locator("input").input_value() or "0")
            lines.append(money(unit * qty))
            total += unit * qty
        return lines, total

    def table_lines(self, table_id: str) -> list[str]:
        return [t.strip() for t in self.page.locator(f"#{table_id} tbody tr output").all_inner_texts()]

    def click_link(self, region: str, name: str) -> int | None:
        with self.page.expect_navigation() as nav:
            self.page.get_by_role("navigation", name=region).get_by_role("link", name=name, exact=True).click()
        return nav.value.status if nav.value else None


# ---------------------------------------------------------------------------- bug checks


def nav_001(lab: Lab) -> str:
    lab.open("/navigation/")
    link = lab.page.get_by_role("navigation", name="Store menu").get_by_role("link", name="Pricing")
    check(link.get_attribute("href") == "/pricing/", "Pricing href is no longer /pricing/")
    status = lab.click_link("Store menu", "Pricing")
    check(status == 200, f"HTTP {status}")
    check(path_of(lab.page) == "/careers/", f"Pricing opened {path_of(lab.page)}")
    check(h1(lab.page) == "Careers", f"heading was {h1(lab.page)!r}")
    lab.open("/pricing/")
    check(h1(lab.page) == "Pricing", "the Pricing page itself is missing")
    return "click 'Pricing' (href /pricing/, page exists) -> landed on /careers/ heading 'Careers'"


def nav_002(lab: Lab) -> str:
    lab.open("/navigation/")
    status = lab.click_link("Help topics", "Shipping policy")
    check(status == 404, f"Shipping policy answered HTTP {status}")
    check(path_of(lab.page) == "/shipping-policy/", f"opened {path_of(lab.page)}")
    check(h1(lab.page) == "Page not found", f"heading was {h1(lab.page)!r}")
    check("Shipping policy" not in lab.page.content(), "404 page mentions 'Shipping policy'")
    return "click 'Shipping policy' -> /shipping-policy/ HTTP 404 'Page not found'"


def form_001(lab: Lab) -> str:
    lab.open("/forms/")
    api_calls: list[str] = []
    lab.page.on("request", lambda r: api_calls.append(r.url) if "/api/" in r.url else None)
    lab.page.get_by_label("Name").fill("Ada Lovelace")
    lab.page.get_by_label("Email address").fill("ada@example.com")
    lab.page.get_by_label("Message").fill("Where is my order?")
    before = lab.page.url
    lab.page.get_by_role("button", name="Send message").click()
    lab.page.wait_for_timeout(QUIET_MS)
    check(not api_calls, f"unexpected API calls {api_calls}")
    check(lab.text("#contact-result") == "", "a result message appeared")
    check(lab.page.url == before, "URL changed")
    check(lab.page.get_by_label("Name").input_value() == "Ada Lovelace", "fields were cleared")
    return "valid submit -> no confirmation, no request, fields kept (expected 'Thanks, Ada Lovelace. ...')"


def form_002(lab: Lab) -> str:
    lab.open("/forms/")
    lab.page.get_by_label("Email for newsletter").fill("not-an-email")
    with lab.page.expect_response("**/api/subscribe") as response_info:
        lab.page.get_by_role("button", name="Subscribe").click()
    status = response_info.value.status
    check(status == 400, f"server answered {status}, expected the server to reject the address")
    result = lab.page.locator("#newsletter-result")
    expect(result).to_have_text("You're subscribed. Updates will go to not-an-email.")
    check("success" in (result.get_attribute("class") or ""), "message is not styled as success")
    return "invalid 'not-an-email' -> server 400 but page shows \"You're subscribed\" (expected validation error)"


def click_001(lab: Lab) -> str:
    lab.open("/buttons/")
    lab.page.get_by_role("button", name="Add Trail Bottle to wishlist").click()
    lab.page.wait_for_timeout(QUIET_MS)
    check(lab.text("#wishlist-count") == "0", f"wishlist count became {lab.text('#wishlist-count')}")
    return "click 'Add Trail Bottle to wishlist' -> count stays 0 (expected 1)"


def click_002(lab: Lab) -> str:
    lab.open("/buttons/")
    lab.page.get_by_role("button", name="Remove Blue Mug").click()
    expect(lab.page.locator("#cart-count")).to_have_text("2")
    items = lab.list_items("cart-list")
    check(items == ["Blue Mug", "Green Notebook"], f"cart became {items}")
    lab.page.get_by_role("button", name="Remove Green Notebook").click()
    lab.page.wait_for_timeout(QUIET_MS)
    check(lab.list_items("cart-list") == ["Blue Mug", "Green Notebook"], "removing the last item removed something")
    return "click 'Remove Blue Mug' -> Red Pen removed, Blue Mug still in cart; last item can't be removed"


def cart_001(lab: Lab) -> str:
    lab.open("/buttons/")
    lab.page.get_by_role("button", name="Add Trail Stove to basket").click()
    expect(lab.page.locator("#basket-total")).to_have_text("$45.00")
    check(lab.basket_rows() == ["Trail Stove $45.00"], f"basket rows {lab.basket_rows()}")
    check(lab.text("#basket-count") == "2", f"basket count became {lab.text('#basket-count')}")
    return "click 'Add Trail Stove to basket' once -> one row, $45.00, but 'Items in basket' shows 2 (expected 1)"


def cart_002(lab: Lab) -> str:
    lab.open("/buttons/")
    lab.page.get_by_role("button", name="Add Rain Poncho to basket").click()
    expect(lab.page.locator("#basket-count")).to_have_text("1")
    check(lab.basket_rows() == ["Camp Stool $19.00"], f"basket rows {lab.basket_rows()}")
    check(lab.text("#basket-total") == "$19.00", f"basket total {lab.text('#basket-total')}")
    return "click 'Add Rain Poncho to basket' -> basket gets 'Camp Stool $19.00' (expected Rain Poncho $22.00)"


def cart_003(lab: Lab) -> str:
    lab.open("/buttons/")
    lab.page.get_by_role("button", name="Add Head Lamp to basket").click()
    expect(lab.page.locator("#basket-count")).to_have_text("2")
    check(lab.basket_rows() == ["Head Lamp $20.00", "Head Lamp $20.00"], f"basket rows {lab.basket_rows()}")
    check(lab.text("#basket-total") == "$40.00", f"basket total {lab.text('#basket-total')}")
    return "click 'Add Head Lamp to basket' once -> two Head Lamp rows, count 2, total $40.00 (expected 1 row, 1, $20.00)"


def cart_004(lab: Lab) -> str:
    lab.open("/buttons/")
    mug = lab.page.get_by_role("button", name="Add Camp Mug to basket")
    mug.click()
    mug.click()
    expect(lab.page.locator("#basket-count")).to_have_text("2")
    lab.page.get_by_role("button", name="Empty basket").click()
    expect(lab.page.locator("#basket-total")).to_have_text("$0.00")
    check(lab.basket_rows() == [], "basket rows remain")
    check(lab.text("#basket-count") == "2", f"basket count became {lab.text('#basket-count')}")
    return "'Empty basket' -> list empty and total $0.00, but 'Items in basket' still shows 2 (expected 0)"


def toggle_001(lab: Lab) -> str:
    lab.open("/toggles/")
    switch = lab.page.get_by_role("switch", name="Email notifications")
    switch.click()
    lab.page.wait_for_timeout(QUIET_MS)
    check(switch.get_attribute("aria-checked") == "false", f"aria-checked became {switch.get_attribute('aria-checked')}")
    check(lab.text("#email-status") == "Email notifications are off.", f"status became {lab.text('#email-status')!r}")
    return "click 'Email notifications' switch -> stays OFF (aria-checked=false, 'are off.')"


def toggle_002(lab: Lab) -> str:
    lab.open("/toggles/")
    for question in ("How long does shipping take?", "How much does shipping cost?"):
        trigger = lab.page.get_by_role("button", name=question)
        trigger.click()
        lab.page.wait_for_timeout(QUIET_MS // 2)
        panel = lab.page.locator(f"#{trigger.get_attribute('aria-controls')}")
        check(trigger.get_attribute("aria-expanded") == "false", f"{question!r} expanded")
        check(panel.is_hidden(), f"{question!r} answer became visible")
    return "click either shipping question -> stays collapsed, answer hidden"


def calc_001(lab: Lab) -> str:
    lab.open("/calculators/")
    lines, expected = lab.table_expectation("bulk-table")
    check(lab.table_lines("bulk-table") == lines, f"line totals {lab.table_lines('bulk-table')} != {lines}")
    shown = lab.text("#bulk-total")
    check(shown == "$35.50" and shown != money(expected), f"order total shows {shown}")
    lab.page.get_by_label("Water bottle quantity").fill("3")
    _, expected_after = lab.table_expectation("bulk-table")
    check(lab.text("#bulk-total") == "$35.50", f"total after change {lab.text('#bulk-total')}")
    return (f"Order total {shown} (expected {money(expected)}); Water bottle qty 3 -> still $35.50 "
            f"(expected {money(expected_after)})")


def calc_002(lab: Lab) -> str:
    lab.open("/calculators/")
    price = Decimal(lab.page.get_by_label("Price ($)").input_value())
    rate = Decimal(lab.page.get_by_label("Tax rate (%)").input_value())
    expected_tax = cents_round(price * rate / 100)
    tax, total = lab.text("#tax-amount"), lab.text("#tax-total")
    check(tax == "$16.00" and total == "$216.00", f"shown tax {tax}, total {total}")
    check(tax != money(expected_tax), "tax is correct")
    lab.page.get_by_label("Tax rate (%)").fill("7")
    check(lab.text("#tax-amount") == "$14.00", f"7% tax shows {lab.text('#tax-amount')}")
    return (f"{price} at {rate}% -> tax {tax}, total {total} (expected {money(expected_tax)}, "
            f"{money(price + expected_tax)})")


def calc_003(lab: Lab) -> str:
    lab.open("/calculators/")
    check(lab.text("#promo-total") == "$40.59", f"total with no code {lab.text('#promo-total')}")
    lab.page.get_by_label("Promo code").fill("SAVE10")
    lab.page.get_by_role("button", name="Apply code").click()
    discount, tax, total = (lab.text(f"#promo-{part}") for part in ("discount", "tax", "total"))
    expected_tax = cents_round(Decimal("33.75") * Decimal("8.25") / 100)
    expected_total = Decimal("33.75") + expected_tax
    check(discount == "$3.75", f"discount shows {discount}")
    check(tax == "$3.09", f"sales tax shows {tax}")
    check(total == "$36.84", f"total shows {total}")
    return (f"SAVE10 -> discount {discount}, tax {tax}, total {total} "
            f"(expected tax {money(expected_tax)}, total {money(expected_total)})")


def calc_004(lab: Lab) -> str:
    lab.open("/calculators/")
    lab.page.get_by_label("Order subtotal ($)").fill("50.00")
    fee = lab.text("#ship-fee")
    check(fee == "$5.00", f"subtotal 50.00 shows shipping {fee}")
    return f"Order subtotal 50.00 -> shipping {fee} (expected $0.00: $50.00 or more ships free)"


def calc_005(lab: Lab) -> str:
    lab.open("/calculators/")
    check(lab.text("#gift-total") == "$16.00", f"total at load {lab.text('#gift-total')}")
    lab.page.get_by_label("Gift box quantity").fill("5")
    line, total = lab.text("#gift-line"), lab.text("#gift-total")
    check(line == "$30.00", f"gift boxes after quantity 5 shows {line}")
    check(total == "$16.00", f"total after quantity 5 shows {total}")
    return f"Gift box quantity 2 -> 5: gift boxes {line}, total {total} (expected $34.00)"


def calc_006(lab: Lab) -> str:
    lab.open("/calculators/")
    check(lab.text("#review-total") == "$24.50", f"cart total at load {lab.text('#review-total')}")
    lab.page.get_by_role("button", name="Remove Pen from cart").click()
    total = lab.text("#review-total")
    check(total == "$23.00", f"cart total after removing Pen shows {total}")
    return f"Cart total $24.50; remove Pen (line $4.50) -> {total} (expected $20.00)"


def calc_007(lab: Lab) -> str:
    lab.open("/calculators/")
    lab.page.get_by_label("Payment received ($)").fill("100.00")
    total, due = lab.text("#invoice-total"), lab.text("#invoice-due")
    check(total == "$462.00", f"invoice total shows {total}")
    check(due == "$462.00", f"amount due after a $100.00 payment shows {due}")
    return f"Total {total}; payment 100.00 -> amount due {due} (expected $362.00)"


def calc_008(lab: Lab) -> str:
    lab.open("/calculators/")
    amount = Decimal(lab.page.get_by_label("Small order amount ($)").input_value())
    rate = Decimal(lab.page.get_by_label("Small order rate (%)").input_value())
    expected = cents_round(amount * rate / 100)
    shown = lab.text("#small-tax")
    check(shown == "$0.00" and shown != money(expected), f"small order tax shows {shown}")
    return f"{amount} at {rate}% -> tax {shown} (expected {money(expected)}: half a cent rounds up)"


# ------------------------------------------------------------------------ healthy checks


def healthy_nav(lab: Lab) -> str:
    for region, name, route in (("Store menu", "Careers", "/careers/"), ("Help topics", "Returns", "/returns/")):
        lab.open("/navigation/")
        status = lab.click_link(region, name)
        check(status == 200, f"{name} answered HTTP {status}")
        check(path_of(lab.page) == route and h1(lab.page) == name, f"{name} opened {path_of(lab.page)}")
    return "Store menu 'Careers' -> /careers/, Help 'Returns' -> /returns/ (HTTP 200, matching heading)"


def _submit(lab: Lab, button: str, endpoint: str) -> int:
    with lab.page.expect_response(f"**{endpoint}") as response_info:
        lab.page.get_by_role("button", name=button).click()
    return response_info.value.status


def healthy_form(lab: Lab) -> str:
    lab.open("/forms/")
    field = lab.page.get_by_label("Email for stock alert")
    result = lab.page.locator("#stock-result")
    field.fill("ada@example.com")
    check(_submit(lab, "Notify me", "/api/subscribe") == 200, "valid address not accepted")
    expect(result).to_have_text("Alert set. We'll email ada@example.com when the Summit Tent is back.")
    check(field.input_value() == "", "form not cleared")
    field.fill("not-an-email")
    check(_submit(lab, "Notify me", "/api/subscribe") == 400, "invalid address accepted")
    expect(result).to_have_text("Please enter a valid email address.")
    return "stock alert: valid -> 200 + confirmation + cleared; invalid -> 400 + 'Please enter a valid email address.'"


def healthy_button(lab: Lab) -> str:
    lab.open("/buttons/")
    add = lab.page.get_by_role("button", name="Add Summit Jacket to wishlist")
    add.click()
    expect(lab.page.locator("#wishlist-count")).to_have_text("1")
    add.click()
    expect(lab.page.locator("#wishlist-count")).to_have_text("2")
    lab.page.get_by_role("button", name="Remove Camp Stool").click()
    expect(lab.page.locator("#later-count")).to_have_text("2")
    check(lab.list_items("later-list") == ["Head Lamp", "Rain Poncho"], f"later {lab.list_items('later-list')}")
    lab.page.get_by_role("button", name="Remove Rain Poncho").click()
    check(lab.list_items("later-list") == ["Head Lamp"], f"later {lab.list_items('later-list')}")
    return "'Add Summit Jacket' -> 1, 2; saved-for-later 'Remove X' removes exactly X"


def healthy_basket(lab: Lab) -> str:
    lab.open("/buttons/")
    mug = lab.page.get_by_role("button", name="Add Camp Mug to basket")
    mug.click()
    expect(lab.page.locator("#basket-count")).to_have_text("1")
    expect(lab.page.locator("#basket-total")).to_have_text("$12.00")
    mug.click()
    expect(lab.page.locator("#basket-count")).to_have_text("2")
    expect(lab.page.locator("#basket-total")).to_have_text("$24.00")
    check(lab.basket_rows() == ["Camp Mug $12.00", "Camp Mug $12.00"], f"rows {lab.basket_rows()}")
    return "'Add Camp Mug to basket' -> count 1, 2; two rows; total $12.00, $24.00"


def healthy_toggle(lab: Lab) -> str:
    lab.open("/toggles/")
    switch = lab.page.get_by_role("switch", name="Text message alerts")
    switch.click()
    expect(switch).to_have_attribute("aria-checked", "true")
    expect(lab.page.locator("#sms-status")).to_have_text("Text message alerts are on.")
    switch.click()
    expect(switch).to_have_attribute("aria-checked", "false")
    expect(lab.page.locator("#sms-status")).to_have_text("Text message alerts are off.")
    for question in ("How do I change my email address?", "Can I pause alerts while travelling?"):
        trigger = lab.page.get_by_role("button", name=question)
        panel = lab.page.locator(f"#{trigger.get_attribute('aria-controls')}")
        trigger.click()
        expect(trigger).to_have_attribute("aria-expanded", "true")
        expect(panel).to_be_visible()
        trigger.click()
        expect(panel).to_be_hidden()
    return "SMS switch OFF->ON->OFF with status; both account questions open and close"


def healthy_calc(lab: Lab) -> str:
    lab.open("/calculators/")
    results = []
    for qty in (None, "1"):
        if qty is not None:
            lab.page.get_by_label("Notebook quantity").fill(qty)
        lines, subtotal = lab.table_expectation("checkout-table")
        tax = cents_round(subtotal * Decimal("8.25") / 100)
        expected = [money(subtotal), money(tax), money(subtotal + tax)]
        check(lab.table_lines("checkout-table") == lines, "checkout line totals wrong")
        for selector, want in zip(("#checkout-subtotal", "#checkout-tax", "#checkout-total"), expected, strict=True):
            expect(lab.page.locator(selector)).to_have_text(want)
        results.append("/".join(expected))
    return f"checkout subtotal/tax/total correct: {results[0]}; Notebook qty 1 -> {results[1]}"


def healthy_shipping(lab: Lab) -> str:
    lab.open("/calculators/")
    lab.page.get_by_label("Order subtotal ($)").fill("49.99")
    below = lab.text("#ship-fee")
    check(below == "$5.00", f"subtotal 49.99 shows shipping {below}")
    lab.page.get_by_label("Order subtotal ($)").fill("60.00")
    above = lab.text("#ship-fee")
    check(above == "$0.00", f"subtotal 60.00 shows shipping {above}")
    return f"subtotal 49.99 -> {below}; 60.00 -> {above} (free)"


def healthy_review(lab: Lab) -> str:
    lab.open("/calculators/")
    lab.page.get_by_role("button", name="Remove Mug from cart").click()
    total = lab.text("#review-total")
    check(total == "$12.50", f"cart total after removing Mug shows {total}")
    return f"Cart total $24.50 -> {total} after removing the Mug"


def healthy_invoice(lab: Lab) -> str:
    lab.open("/calculators/")
    lab.page.get_by_label("Payment received ($)").fill("0")
    subtotal, tax, total, due = (lab.text(f"#invoice-{part}") for part in ("subtotal", "tax", "total", "due"))
    check((subtotal, tax, total) == ("$420.00", "$42.00", "$462.00"), f"invoice shows {subtotal}/{tax}/{total}")
    check(due == "$462.00", f"amount due with no payment shows {due}")
    return f"subtotal/tax/total {subtotal}/{tax}/{total}; with no payment, amount due {due}"


CHECKS: list[tuple[str, str, Callable[[Lab], str]]] = [
    ("bug", "NAV-001", nav_001), ("bug", "NAV-002", nav_002),
    ("bug", "FORM-001", form_001), ("bug", "FORM-002", form_002),
    ("bug", "CLICK-001", click_001), ("bug", "CLICK-002", click_002),
    ("bug", "CART-001", cart_001), ("bug", "CART-002", cart_002),
    ("bug", "CART-003", cart_003), ("bug", "CART-004", cart_004),
    ("bug", "TOGGLE-001", toggle_001), ("bug", "TOGGLE-002", toggle_002),
    ("bug", "CALC-001", calc_001), ("bug", "CALC-002", calc_002),
    ("bug", "CALC-003", calc_003), ("bug", "CALC-004", calc_004),
    ("bug", "CALC-005", calc_005), ("bug", "CALC-006", calc_006),
    ("bug", "CALC-007", calc_007), ("bug", "CALC-008", calc_008),
    ("healthy", "HEALTHY-NAV", healthy_nav), ("healthy", "HEALTHY-FORM", healthy_form),
    ("healthy", "HEALTHY-BUTTON", healthy_button), ("healthy", "HEALTHY-BASKET", healthy_basket), ("healthy", "HEALTHY-TOGGLE", healthy_toggle),
    ("healthy", "HEALTHY-CALC", healthy_calc), ("healthy", "HEALTHY-SHIPPING", healthy_shipping),
    ("healthy", "HEALTHY-REVIEW", healthy_review), ("healthy", "HEALTHY-INVOICE", healthy_invoice),
]


# -------------------------------------------------------------------------- reachability


def crawl(page: Page, base_url: str) -> dict[str, tuple[int, int]]:
    """Breadth-first crawl of same-origin links from '/'. Returns {path: (status, depth)}."""
    origin = urlparse(base_url).netloc
    seen: dict[str, tuple[int, int]] = {}
    queue = deque([("/", 0)])
    while queue:
        route, depth = queue.popleft()
        if route in seen:
            continue
        response = page.goto(base_url.rstrip("/") + route, wait_until="load")
        status = response.status if response else 0
        seen[route] = (status, depth)
        if status != 200:
            continue
        for href in page.eval_on_selector_all("a[href]", "els => els.map(e => e.getAttribute('href'))"):
            target = urlparse(urljoin(page.url, href))
            if target.netloc == origin and target.path not in seen:
                queue.append((target.path, depth + 1))
    return seen


def check_reachability(page: Page, base_url: str) -> tuple[bool, str]:
    seen = crawl(page, base_url)
    routes = EXPECTED["routes"]
    wanted = [routes["home"], *routes["feature_pages"], *routes["destination_pages"]]
    problems = [f"{r} not reached with 200 ({seen.get(r)})" for r in wanted if seen.get(r, (0,))[0] != 200]
    for missing in routes["intentionally_missing"]:
        if seen.get(missing, (0,))[0] != 404:
            problems.append(f"{missing} expected 404, got {seen.get(missing)}")
    unexpected = [r for r, (s, _) in seen.items() if r not in wanted and r not in routes["intentionally_missing"]]
    if unexpected:
        problems.append(f"unexpected routes {unexpected}")
    if len(seen) > EXPECTED["page_budget"]:
        problems.append(f"{len(seen)} routes exceed the {EXPECTED['page_budget']}-page crawl budget")
    max_depth = max(d for s, d in seen.values() if s == 200)
    detail = (f"{len(seen)} routes total, {sum(1 for s, _ in seen.values() if s == 200)} pages HTTP 200, "
              f"{len(routes['intentionally_missing'])} intended 404, max click depth {max_depth}")
    return (not problems, "; ".join(problems) or detail)


# ------------------------------------------------------------------------------- runner


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_for(url: str, timeout_s: float = 10.0) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError(f"server at {url} did not start")


def run(base_url: str) -> bool:
    all_ok = True
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        js_errors: list[str] = []
        for kind, check_id, fn in CHECKS:
            page = browser.new_page()
            page.on("pageerror", lambda exc, cid=check_id: js_errors.append(f"{cid}: {exc}"))
            try:
                detail, ok = fn(Lab(page, base_url)), True
            except Exception as exc:  # noqa: BLE001 - report every failure, keep going
                detail, ok = f"{type(exc).__name__}: {exc}", False
            finally:
                page.close()
            all_ok &= ok
            label = "REPRODUCED" if kind == "bug" and ok else "WORKS" if ok else "FAIL"
            print(f"{label:<10} {check_id:<17} {detail}")
        page = browser.new_page()
        page.on("pageerror", lambda exc: js_errors.append(f"crawl: {exc}"))
        reach_ok, reach_detail = check_reachability(page, base_url)
        page.close()
        browser.close()
    all_ok &= reach_ok
    print(f"{'OK' if reach_ok else 'FAIL':<10} {'REACHABILITY':<17} {reach_detail}")
    print(f"{'OK' if not js_errors else 'FAIL':<10} {'NO-JS-ERRORS':<17} {js_errors or 'no uncaught page errors'}")
    return all_ok and not js_errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-url", default=EXPECTED["default_base_url"])
    parser.add_argument("--start-server", action="store_true", help="Start server.py on a free port for this run.")
    args = parser.parse_args()

    server = None
    base_url = args.base_url
    if args.start_server:
        port = free_port()
        base_url = f"http://127.0.0.1:{port}"
        server = subprocess.Popen([sys.executable, str(LAB_DIR / "server.py"), "--port", str(port)])
    try:
        wait_for(base_url + "/")
        ok = run(base_url)
    finally:
        if server is not None:
            server.terminate()
            server.wait(timeout=5)
    print("\nRESULT:", "ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
