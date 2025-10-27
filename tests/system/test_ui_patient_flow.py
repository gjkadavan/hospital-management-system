def test_ui_patient_registration_flow(browser):
    # Step 1: Login as staff/front desk
    browser.get(browser.base_url + "/login.html")

    browser.find_element("id", "username").send_keys("reception")
    browser.find_element("id", "password").send_keys("staff123")
    browser.find_element("id", "login-btn").click()

    # Step 2: Go to "new patient" page
    browser.get(browser.base_url + "/patients_new.html")

    # Step 3: Fill patient registration form
    browser.find_element("id", "first_name").send_keys("Test")
    browser.find_element("id", "last_name").send_keys("Patient")
    browser.find_element("id", "dob").send_keys("1990-01-01")
    browser.find_element("id", "phone").send_keys("555-1234")
    browser.find_element("id", "medical_history").send_keys("No known allergies")
    browser.find_element("id", "submit-btn").click()

    # Step 4: Confirm success
    success_text = browser.find_element("id", "patient-success").text.lower()
    assert "created" in success_text or "added" in success_text
