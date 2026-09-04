import os
from pathlib import Path

from playwright.sync_api import sync_playwright


BASE_URL = os.getenv("PSFINANCE_STAGING_URL", "http://127.0.0.1:5199/staging/psfinance").rstrip("/")
OUTPUT_DIR = Path("docs/evidencias/PLA-743-credor-cidade")


def validar(page, viewport_name):
    page.goto(f"{BASE_URL}/financeiro/credores/novo", wait_until="networkidle")
    cidades = page.evaluate("async url => (await (await fetch(url)).json()).cidades", f"{BASE_URL}/financeiro/cidades/busca?q=")
    if not cidades:
        raise AssertionError("A validação precisa de ao menos uma cidade ativa.")
    cidade = cidades[0]

    page.locator("#cidade_codigo").fill(str(cidade["id"]))
    page.locator("#cidade_codigo").press("Tab")
    page.wait_for_function("value => document.querySelector('#id_cidade').value === String(value)", arg=cidade["id"])
    assert page.locator("#cidade_nome").input_value() == cidade["nome"]

    page.locator("#cidade_nome").fill(cidade["nome"])
    page.locator("#cidade_nome").press("Tab")
    page.wait_for_function("value => document.querySelector('#cidade_nome').value === value", arg=cidade["nome"])
    assert page.locator("#cidade_codigo").input_value() == str(cidade["id"])

    page.locator("#limpar_cidade").click()
    assert page.locator("#id_cidade").input_value() == ""
    assert page.locator("#cidade_codigo").input_value() == ""
    assert page.locator("#cidade_nome").input_value() == ""

    page.locator("#cidade_nome").fill("cidade-inexistente-pla743")
    page.locator("#cidade_nome").press("Tab")
    page.locator("#modal_busca_cidade.show").wait_for()
    assert page.locator("#resultado_busca_cidade button").count() == 0
    assert page.locator("#mensagem_busca_cidade").inner_text() == "Nenhuma cidade encontrada."
    page.screenshot(path=OUTPUT_DIR / f"cidade-editavel-{viewport_name}.png", full_page=True)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for name, viewport in (("desktop", {"width": 1440, "height": 1000}), ("mobile", {"width": 390, "height": 844})):
            page = browser.new_page(viewport=viewport)
            validar(page, name)
            print(f"{name}: código, nome, troca, limpeza e busca sem resultado validados")
            page.close()
        browser.close()


if __name__ == "__main__":
    main()
