import os
from pathlib import Path

from playwright.sync_api import sync_playwright


BASE_URL = os.getenv("PSFINANCE_STAGING_URL", "http://127.0.0.1:5199/staging/psfinance").rstrip("/")
OUTPUT_DIR = Path("docs/evidencias/PLA-743-credor-cidade")


def validar(page, viewport_name):
    page.goto(f"{BASE_URL}/financeiro/credores/novo", wait_until="networkidle")

    page.locator("#cidade_codigo").fill("1")
    page.locator("#cidade_codigo").press("Tab")
    page.wait_for_function("document.querySelector('#id_cidade').value === '1'")
    assert page.locator("#cidade_nome").input_value() == "Porto Alegre"

    page.locator("#cidade_nome").fill("can")
    page.locator("#cidade_nome").press("Tab")
    page.wait_for_function("document.querySelector('#cidade_nome').value === 'Canoas'")
    assert page.locator("#cidade_codigo").input_value() == "2"

    page.locator("#limpar_cidade").click()
    assert page.locator("#id_cidade").input_value() == ""
    assert page.locator("#cidade_codigo").input_value() == ""
    assert page.locator("#cidade_nome").input_value() == ""

    page.locator("#cidade_nome").fill("a")
    page.locator("#cidade_nome").press("Tab")
    page.locator("#modal_busca_cidade.show").wait_for()
    assert page.locator("#resultado_busca_cidade button").count() == 2
    page.screenshot(path=OUTPUT_DIR / f"cidade-editavel-{viewport_name}.png", full_page=True)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for name, viewport in (("desktop", {"width": 1440, "height": 1000}), ("mobile", {"width": 390, "height": 844})):
            page = browser.new_page(viewport=viewport)
            validar(page, name)
            print(f"{name}: código, nome, troca, limpeza e múltiplos validados")
            page.close()
        browser.close()


if __name__ == "__main__":
    main()
