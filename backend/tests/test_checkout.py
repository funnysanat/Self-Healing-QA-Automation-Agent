from playwright.sync_api import sync_playwright

def run_test(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        
        # Click the proceed payment button
        page.click('#proceed-payment', timeout=3000)
        
        # Verify success message
        message = page.locator('#message')
        message.wait_for(state="visible", timeout=3000)
        assert "Payment Successful!" in message.text_content()
        
        browser.close()
        return True

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        run_test(sys.argv[1])
    else:
        run_test("http://localhost:8000/v1.html")