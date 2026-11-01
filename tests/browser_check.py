"""Optional browser checks against a seeded local server; records a simulated donation.

Run with a disposable seeded database, as documented in README.md.
Requires Playwright plus Chromium, separate from the app dependencies.
"""

from playwright.sync_api import sync_playwright
from pathlib import Path
import json
import os

base_url = os.environ.get("CHARIGO_BASE_URL", "http://127.0.0.1:5000").rstrip("/")
output = Path(__file__).resolve().parents[1] / "artifacts"
output.mkdir(exist_ok=True)
out = str(output) + "/"

with sync_playwright() as p:
    browser_path = os.environ.get("CHROMIUM_BINARY", "/usr/bin/chromium")
    b = p.chromium.launch(executable_path=browser_path, args=["--no-sandbox"])
    page = b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=1)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(base_url + "/")
    page.screenshot(path=out + "welcome-mobile.png", full_page=True)
    page.goto(base_url + "/home")
    page.screenshot(path=out + "home-mobile.png", full_page=True)
    page.set_viewport_size({"width": 1366, "height": 900})
    page.screenshot(path=out + "home-desktop.png", full_page=True)
    page.goto(base_url + "/login")
    page.get_by_label("Email address").fill("goer@example.com")
    page.get_by_label("Password", exact=True).fill("ChariGo123!")
    page.get_by_role("button", name="Log In", exact=True).click()
    page.wait_for_url("**/home")
    pages = [
        "/home",
        "/causes",
        "/fundraisers/1",
        "/organizations/1",
        "/fundraisers/1/donate",
        "/opportunities/1",
        "/profile",
        "/profile/edit",
        "/history/donations",
        "/history/volunteering",
    ]
    results = []
    for width in [320, 375, 390, 430, 768, 1024, 1366, 1920]:
        page.set_viewport_size({"width": width, "height": 900})
        for url in pages:
            response = page.goto(base_url + url)
            page.wait_for_load_state("networkidle")
            overflow = page.evaluate(
                "document.documentElement.scrollWidth > innerWidth"
            )
            broken = page.locator("img").evaluate_all(
                "(imgs) => imgs.filter(i => !i.complete || i.naturalWidth === 0).map(i => i.src)"
            )
            results.append(
                {
                    "width": width,
                    "page": url,
                    "status": response.status,
                    "overflow": overflow,
                    "broken_images": broken,
                }
            )
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(base_url + "/fundraisers/1/donate")
    page.get_by_text("₱500", exact=True).click()
    assert page.locator("#donation-amount").input_value() == "500"
    page.get_by_label("Amount in Philippine pesos").fill("123.45")
    page.get_by_role("button", name="Continue to review").click()
    page.wait_for_url("**/donation/review")
    assert page.get_by_text("₱123.45", exact=True).count() == 2
    page.get_by_role("button", name="Confirm Donation", exact=True).click()
    page.wait_for_url("**/donations/*")
    assert page.get_by_role("heading", name="Thank You!", exact=True).is_visible()
    page.screenshot(path=out + "donation-receipt-mobile.png", full_page=True)
    page.goto(base_url + "/profile")
    page.get_by_role("button", name="Log out", exact=True).click()
    assert page.locator("dialog[open]").count() == 1
    page.get_by_role("button", name="Cancel", exact=True).click()
    assert page.url.endswith("/profile")
    page.get_by_role("button", name="Log out", exact=True).click()
    page.get_by_role("button", name="Confirm", exact=True).click()
    page.wait_for_url("**/login")
    for email, urls in [
        (
            "organization@example.com",
            [
                "/organization",
                "/organization/profile",
                "/organization/fundraisers",
                "/organization/fundraisers/new",
                "/organization/fundraisers/1",
                "/organization/fundraisers/1/applications",
                "/organization/applications/5",
            ],
        ),
        (
            "admin@example.com",
            [
                "/admin",
                "/admin/users",
                "/admin/users/1",
                "/admin/organizations",
                "/admin/organizations/3",
                "/admin/opportunities",
                "/admin/opportunities/volunteer/1",
                "/admin/records",
            ],
        ),
    ]:
        page.get_by_label("Email address").fill(email)
        page.get_by_label("Password", exact=True).fill("ChariGo123!")
        page.get_by_role("button", name="Log In", exact=True).click()
        page.wait_for_load_state("networkidle")
        for width in [320, 375, 390, 430, 768, 1024, 1366, 1920]:
            page.set_viewport_size({"width": width, "height": 900})
            for url in urls:
                r = page.goto(base_url + url)
                page.wait_for_load_state("networkidle")
                results.append(
                    {
                        "width": width,
                        "page": url,
                        "status": r.status,
                        "overflow": page.evaluate(
                            "document.documentElement.scrollWidth > innerWidth"
                        ),
                        "broken_images": page.locator("img").evaluate_all(
                            "(imgs) => imgs.filter(i => !i.complete || i.naturalWidth === 0).map(i => i.src)"
                        ),
                    }
                )
        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(base_url + urls[0])
        page.screenshot(
            path=out
            + ("organization" if "organization" in email else "admin")
            + "-mobile.png",
            full_page=True,
        )
        page.goto(base_url + "/profile")
        page.get_by_role("button", name="Log out", exact=True).click()
        page.get_by_role("button", name="Confirm", exact=True).click()
        page.wait_for_url("**/login")
    json.dump(
        {"page_checks": results, "js_errors": errors},
        open(out + "browser-results.json", "w"),
        indent=2,
    )
    failures = [
        r for r in results if r["overflow"] or r["status"] != 200 or r["broken_images"]
    ]
    print("Page checks:", len(results), "Failures:", failures)
    print("JavaScript errors:", errors)
    assert not failures and not errors
    b.close()
