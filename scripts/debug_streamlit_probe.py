from playwright.sync_api import sync_playwright

URLS = [
    "https://ai-music-practice-coach-6szqxqxqrqxdmryyewk8sq.streamlit.app?suite_workspace=ariel",
    "https://daniel-ai-command-center-ion4vh2cvo7bgdnkuktrb3.streamlit.app?suite_workspace=ariel",
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1600, "height": 1200})
    for url in URLS:
        print("URL", url)
        page.goto(url, timeout=180000)
        try:
            page.wait_for_selector('[data-testid="stApp"]', timeout=120000)
            print("  stApp: found")
        except Exception as exc:
            print("  stApp wait failed:", exc)
        page.wait_for_timeout(15000)
        html = page.content()
        body = page.inner_text("body")
        print("  html_len", len(html), "body_len", len(body))
        needles = [
            "Active workspace",
            "Account & workspace",
            "Ariel",
            "Daniel Cohen",
            "Recent Activity",
            "suite_workspace",
            "stSidebar",
            "encountered an error",
        ]
        for needle in needles:
            print(f"  {needle}: html={needle in html} body={needle in body}")
    browser.close()
