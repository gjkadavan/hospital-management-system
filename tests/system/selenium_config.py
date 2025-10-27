import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

@pytest.fixture(scope="function")
def browser():
    """
    Launch a headless Chrome browser for UI/system tests.
    Assumes the Flask app is already running locally on http://localhost:5000.
    """
    chrome_opts = Options()
    chrome_opts.add_argument("--headless=new")
    chrome_opts.add_argument("--no-sandbox")
    chrome_opts.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_opts)

    driver.base_url = "http://localhost:5000"
    yield driver
    driver.quit()
