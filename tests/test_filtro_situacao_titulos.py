import unittest

from financeiro.routes_titulos import (
    _normalizar_situacao_titulo,
    _titulo_atende_situacao,
)


class FiltroSituacaoTitulosTest(unittest.TestCase):
    def test_normaliza_filtro_ausente_ou_invalido_para_todas(self):
        self.assertEqual(_normalizar_situacao_titulo(None), "todas")
        self.assertEqual(_normalizar_situacao_titulo("invalida"), "todas")

    def test_todas_inclui_titulos_baixados_e_em_aberto(self):
        self.assertTrue(_titulo_atende_situacao(0.0, "todas"))
        self.assertTrue(_titulo_atende_situacao(80.0, "todas"))

    def test_baixada_inclui_somente_titulo_sem_saldo_no_mes(self):
        self.assertTrue(_titulo_atende_situacao(0.0, "baixada"))
        self.assertFalse(_titulo_atende_situacao(0.01, "baixada"))

    def test_em_aberto_inclui_somente_titulo_com_saldo_no_mes(self):
        self.assertFalse(_titulo_atende_situacao(0.0, "em_aberto"))
        self.assertTrue(_titulo_atende_situacao(0.01, "em_aberto"))


if __name__ == "__main__":
    unittest.main()
