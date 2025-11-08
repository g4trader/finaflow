import os
import sys
import time
from contextlib import suppress

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

PROD_URL = "https://finaflow.vercel.app/login"
USERNAME = os.getenv("FINAFLOW_E2E_USER", "admin")
PASSWORD = os.getenv("FINAFLOW_E2E_PASSWORD", "Admin@123")

RESULT = {
    "login_page": False,
    "login_success": False,
    "business_unit_selected": False,
    "dashboard_loaded": False,
    "errors": [],
}


class StepError(RuntimeError):
    pass


def wait_for_any(wait: WebDriverWait, locators, condition=EC.visibility_of_element_located):
    last_exc = None
    for locator in locators:
        try:
            return wait.until(condition(locator))
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
    if last_exc:
        raise last_exc
    raise TimeoutException("No locator matched")


def main():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,900")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 30)

    try:
        driver.get(PROD_URL)
        wait.until(lambda d: "login" in d.current_url)
        RESULT["login_page"] = True

        username_input = wait_for_any(
            wait,
            [
                (By.NAME, "username"),
                (By.ID, "username"),
                (By.CSS_SELECTOR, "input[type='email']"),
                (By.CSS_SELECTOR, "input[placeholder*='email']"),
                (By.CSS_SELECTOR, "input[placeholder*='Usuário']"),
            ],
        )

        password_input = wait_for_any(
            wait,
            [
                (By.NAME, "password"),
                (By.ID, "password"),
                (By.CSS_SELECTOR, "input[type='password']"),
            ],
        )

        username_input.clear()
        username_input.send_keys(USERNAME)
        password_input.clear()
        password_input.send_keys(PASSWORD)

        login_button = wait_for_any(
            wait,
            [
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.XPATH, "//button[contains(., 'Entrar')]")
            ],
            condition=EC.element_to_be_clickable,
        )
        login_button.click()

        wait.until(EC.any_of(
            EC.url_contains("select-business-unit"),
            EC.presence_of_element_located((By.XPATH, "//h1[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'unidade')]")),
        ))
        RESULT["login_success"] = True

        # Selecionar BU
        with suppress(Exception):
            bu_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Matriz')]")))
        if 'bu_button' not in locals():
            # fallback para primeira opção disponível
            bu_button = wait_for_any(
                wait,
                [
                    (By.CSS_SELECTOR, "button[class*='business']"),
                    (By.XPATH, "(//button)[1]")
                ],
                condition=EC.element_to_be_clickable,
            )
        bu_button.click()
        RESULT["business_unit_selected"] = True

        wait.until(EC.any_of(
            EC.url_contains("dashboard"),
            EC.presence_of_element_located((By.XPATH, "//h1[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'dashboard')]"))
        ))
        RESULT["dashboard_loaded"] = True

        # tirando screenshot final
        time.sleep(2)
        driver.save_screenshot("tests/e2e_prod_screenshot.png")

    except TimeoutException as exc:  # noqa: PERF203
        RESULT["errors"].append(f"Timeout: {exc}")
    except Exception as exc:  # noqa: BLE001
        RESULT["errors"].append(str(exc))
    finally:
        with suppress(Exception):
            logs = driver.get_log("browser")
            with open("tests/e2e_prod_browser.log", "w", encoding="utf-8") as fp:
                for entry in logs:
                    fp.write(f"{entry['level']} {entry['timestamp']}: {entry['message']}\n")
        with suppress(Exception):
            driver.save_screenshot("tests/e2e_prod_last_state.png")
        with suppress(Exception):
            with open("tests/e2e_prod_last_dom.html", "w", encoding="utf-8") as fp:
                fp.write(driver.page_source)
        driver.quit()

    success = all([
        RESULT["login_page"],
        RESULT["login_success"],
        RESULT["business_unit_selected"],
        RESULT["dashboard_loaded"],
        not RESULT["errors"],
    ])

    print("=== E2E Production Test Result ===")
    for key, value in RESULT.items():
        if key != "errors":
            print(f"{key}: {value}")
    if RESULT["errors"]:
        print("Errors:")
        for err in RESULT["errors"]:
            print(f" - {err}")

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
