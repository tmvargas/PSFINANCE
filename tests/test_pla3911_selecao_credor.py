from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SelecaoCredorSiengeTest(unittest.TestCase):
    def test_titulo_usa_campo_textual_e_id_oculto_sem_combobox(self):
        template = (ROOT / "templates" / "titulo_form.html").read_text(encoding="utf-8")

        self.assertIn('id="credor_nome"', template)
        self.assertIn('type="hidden" name="id_credor" id="id_credor"', template)
        self.assertNotIn('<select name="id_credor"', template)
        self.assertIn('id="abrir_busca_credor"', template)

    def test_tab_trata_zero_um_e_multiplos_resultados(self):
        template = (ROOT / "templates" / "titulo_form.html").read_text(encoding="utf-8")

        self.assertIn('nameInput.addEventListener("blur"', template)
        self.assertIn("options.autoSelect && credores.length === 1", template)
        self.assertIn("render(credores)", template)
        self.assertIn("options.showModal", template)
        self.assertIn("Nenhum credor encontrado", template)

    def test_cadastro_reutiliza_janela_e_devolve_credor_criado(self):
        titulo = (ROOT / "templates" / "titulo_form.html").read_text(encoding="utf-8")
        credor = (ROOT / "templates" / "credor_form.html").read_text(encoding="utf-8")
        rota = (ROOT / "financeiro" / "routes_credor.py").read_text(encoding="utf-8")

        self.assertIn('if (cadastroWindow && !cadastroWindow.closed)', titulo)
        self.assertIn('"psfinanceCadastroCredor"', titulo)
        self.assertIn('event.data?.type !== "psfinance:credor-criado"', titulo)
        self.assertIn('type: "psfinance:credor-criado"', credor)
        self.assertIn("window.close()", credor)
        self.assertIn(
            'url_for("financeiro.novo_credor", origem=origem, criado=id_credor)', rota
        )


if __name__ == "__main__":
    unittest.main()
