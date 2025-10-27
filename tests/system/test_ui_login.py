def test_ui_login_admin(browser):
    # 1. Go to login page
    browser.get(browser.base_url + "/login.html")

    # 2. Fill form
    # Update these selectors to match your HTML form fields!
    browser.find_element("id", "username").clear()
    browser.find_element("id", "username").send_keys("admin")

    browser.find_element("id", "password").clear()
    browser.find_element("id", "password").send_keys("admin123")

    browser.find_element("id", "login-btn").click()

    # 3. Assert dashboard shows logged-in admin
    # Change this to whatever element shows success in your UI.
    heading_text = browser.find_element("id", "dashboard-heading").text.lower()
    assert "welcome" in heading_text
    assert "admin" in heading_text
