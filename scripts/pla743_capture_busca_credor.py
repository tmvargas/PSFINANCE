import os
from pathlib import Path

from playwright.sync_api import sync_playwright


BASE_URL = os.getenv(
    "PSFINANCE_STAGING_URL",
    "http://vps69143.publiccloud.com.br/staging/psfinance",
).rstrip("/")
OUTPUT_DIR = Path("docs/evidencias/PLA-743")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for name, viewport in (
            ("desktop", {"width": 1440, "height": 1000}),
            ("mobile", {"width": 390, "height": 844}),
        ):
            page = browser.new_page(viewport=viewport)
            page.goto(f"{BASE_URL}/financeiro/titulos/novo", wait_until="networkidle")
            page.locator("#abrir_busca_credor").click()
            page.locator("#resultado_busca_credor button").first.wait_for()
            initial_count = page.locator("#resultado_busca_credor button").count()
            page.locator("#busca_credor").fill("Vivo")
            page.locator("#resultado_busca_credor button").first.wait_for()
            page.wait_for_timeout(400)
            page.screenshot(path=OUTPUT_DIR / f"busca-credor-{name}.png", full_page=True)
            page.locator("#resultado_busca_credor button").first.click()
            selected = page.locator("#id_credor option:checked").inner_text().strip()
            if selected != "Vivo":
                raise AssertionError(f"Credor selecionado inesperado: {selected}")
            print(f"{name}: credores={initial_count}; selecionado={selected}")
            page.close()
        browser.close()


if __name__ == "__main__":
    main()
