import unittest

from financeiro.routes_titulos import (
    _calcular_saldo_titulo,
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

    def test_baixada_inclui_somente_titulo_sem_saldo(self):
        self.assertTrue(_titulo_atende_situacao(0.0, "baixada"))
        self.assertFalse(_titulo_atende_situacao(0.01, "baixada"))

    def test_em_aberto_inclui_somente_titulo_com_saldo(self):
        self.assertFalse(_titulo_atende_situacao(0.0, "em_aberto"))
        self.assertTrue(_titulo_atende_situacao(0.01, "em_aberto"))

    def test_matriz_de_saldos_ativos(self):
        casos = (
            ("simples em aberto", 100, 0, 100),
            ("baixa parcial", 100, 40, 60),
            ("multiplas baixas", 100, 25 + 75, 0),
            ("parcelado parcialmente baixado", 300, 200, 100),
            ("integralmente quitado", 300, 300, 0),
            ("sobrepagamento protegido", 100, 120, 0),
        )
        for nome, total_ativo, baixado_ativo, saldo_esperado in casos:
            with self.subTest(nome=nome):
                saldo = _calcular_saldo_titulo(total_ativo, baixado_ativo)
                self.assertEqual(saldo, saldo_esperado)
                self.assertEqual(
                    _titulo_atende_situacao(saldo, "baixada"),
                    saldo_esperado == 0,
                )

    def test_exclusoes_sao_representadas_fora_dos_totais_ativos(self):
        saldo_sem_baixa_excluida = _calcular_saldo_titulo(100, 40)
        saldo_sem_parcela_excluida = _calcular_saldo_titulo(100, 100)

        self.assertEqual(saldo_sem_baixa_excluida, 60)
        self.assertEqual(saldo_sem_parcela_excluida, 0)


if __name__ == "__main__":
    unittest.main()
