import unittest
from types import SimpleNamespace

from financeiro.routes_titulos import (
    _calcular_saldo_titulo,
    _normalizar_situacao_titulo,
    _saldos_titulos_ativos,
    _titulo_atende_situacao,
)


class ConsultaLeituraFake:
    def __init__(self, resultados):
        self._resultados = iter(resultados)

    def query(self, *_args):
        return QueryLeituraFake(next(self._resultados))


class QueryLeituraFake:
    def __init__(self, resultado):
        self._resultado = resultado

    def filter(self, *_args):
        return self

    def distinct(self):
        return self

    def group_by(self, *_args):
        return self

    def join(self, *_args):
        return self

    def all(self):
        return self._resultado


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

    def test_consultas_agregadas_ignoram_baixa_e_parcela_excluidas(self):
        titulos = [
            SimpleNamespace(id_titulo=1, valor=100),
            SimpleNamespace(id_titulo=2, valor=250),
            SimpleNamespace(id_titulo=3, valor=80),
        ]
        session = ConsultaLeituraFake(
            [
                [(1,), (2,)],  # títulos 1 e 2 possuem parcelas, inclusive excluídas
                [(1, 100)],  # somente a parcela ativa do título 1
                [(1, 40)],  # somente a baixa ativa vinculada à parcela ativa
                [],  # nenhuma baixa legada ativa
            ]
        )

        saldos = _saldos_titulos_ativos(session, titulos)

        self.assertEqual(saldos[1], 60)  # baixa excluída não reduz o saldo
        self.assertEqual(saldos[2], 0)  # todas as parcelas excluídas
        self.assertEqual(saldos[3], 80)  # título simples, sem parcelas

    def test_consultas_agregadas_somam_multiplas_baixas_ativas_e_legadas(self):
        titulos = [SimpleNamespace(id_titulo=4, valor=300)]
        session = ConsultaLeituraFake(
            [
                [(4,)],
                [(4, 300)],
                [(4, 175)],
                [(4, 25)],
            ]
        )

        self.assertEqual(_saldos_titulos_ativos(session, titulos)[4], 100)


if __name__ == "__main__":
    unittest.main()
