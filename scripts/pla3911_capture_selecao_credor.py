import os
from pathlib import Path

from playwright.sync_api import sync_playwright


BASE_URL = os.getenv(
    "PSFINANCE_STAGING_URL",
    "http://vps69143.publiccloud.com.br/staging/psfinance",
).rstrip("/")
OUTPUT_DIR = Path("docs/evidencias/PLA-3911")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.goto(f"{BASE_URL}/financeiro/titulos/novo", wait_until="networkidle")

        credores = page.evaluate(
            "async () => (await (await fetch('./../credores/busca')).json()).credores"
        )
        if not credores:
            raise AssertionError("Staging não possui credor ativo para validar a seleção")
        unico = next(
            (
                credor
                for credor in credores
                if sum(credor["nome"].lower() in item["nome"].lower() for item in credores) == 1
            ),
            credores[0],
        )

        campo = page.locator("#credor_nome")
        campo.fill(unico["nome"])
        campo.press("Tab")
        page.wait_for_function(
            "id => document.querySelector('#id_credor').value === String(id)",
            arg=unico["id"],
        )
        if campo.input_value() != unico["nome"]:
            raise AssertionError("Resultado único não foi selecionado automaticamente")

        campo.fill("PLA-3911-CREDOR-INEXISTENTE")
        campo.press("Tab")
        page.locator("#modal_busca_credor.show").wait_for()
        page.get_by_text("Nenhum credor encontrado", exact=False).wait_for()
        page.screenshot(path=OUTPUT_DIR / "credor-zero-resultados-desktop.png", full_page=True)
        page.get_by_role("button", name="Cancelar").last.click()

        page.locator("#abrir_busca_credor").click()
        page.locator("#busca_credor").fill("")
        page.locator("#atualizar_credores").click()
        page.locator("#resultado_busca_credor button").first.wait_for()
        if page.locator("#resultado_busca_credor button").count() < 2:
            raise AssertionError("Staging não possui múltiplos credores para validar a escolha")
        page.screenshot(path=OUTPUT_DIR / "credor-multiplos-resultados-desktop.png", full_page=True)

        with page.expect_popup() as popup_info:
            page.locator("#novo_credor_janela").click()
        popup = popup_info.value
        popup.wait_for_load_state("networkidle")
        if popup.locator(".popup-shell").count() != 1:
            raise AssertionError("Cadastro de credor não abriu no layout auxiliar")
        if popup.locator(".app-shell, .sidebar, .topbar").count():
            raise AssertionError("Popup de credor exibiu navegação do sistema")
        popup.screenshot(path=OUTPUT_DIR / "popup-credor-desktop.png", full_page=True)
        page.locator("#novo_credor_janela").click()
        page.wait_for_timeout(300)
        if len(page.context.pages) != 2:
            raise AssertionError("O cadastro de credor abriu mais de uma janela")
        popup.close()

        mobile = browser.new_page(viewport={"width": 390, "height": 844})
        mobile.goto(f"{BASE_URL}/financeiro/titulos/novo", wait_until="networkidle")
        mobile.locator("#abrir_busca_credor").click()
        mobile.locator("#resultado_busca_credor button").first.wait_for()
        mobile.screenshot(path=OUTPUT_DIR / "selecao-credor-mobile.png", full_page=True)

        print(
            f"unico={unico['nome']}; multiplos={len(credores)}; "
            "zero=ok; janela_unica=ok; popup_auxiliar=ok; desktop=ok; mobile=ok"
        )
        browser.close()


if __name__ == "__main__":
    main()
