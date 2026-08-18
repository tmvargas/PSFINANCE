import unittest
from types import SimpleNamespace

from financeiro.routes_titulos import (
    _calcular_saldo_titulo,
    _filtrar_titulos_por_situacao,
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

    def test_matriz_combina_periodo_empresa_e_situacao_sem_reintroduzir_registros(self):
        # O controller entrega a este passo apenas os títulos do período/empresa.
        # Os IDs 3 e 4 representam registros que aqueles filtros já eliminaram.
        titulos_periodo_empresa = [
            SimpleNamespace(id_titulo=1, valor=100),
            SimpleNamespace(id_titulo=2, valor=250),
        ]
        saldos_globais = {1: 60, 2: 0, 3: 0, 4: 90}

        casos = (
            ("todas", [1, 2]),
            ("em_aberto", [1]),
            ("baixada", [2]),
        )
        for situacao, ids_esperados in casos:
            with self.subTest(situacao=situacao):
                resultado = _filtrar_titulos_por_situacao(
                    titulos_periodo_empresa,
                    saldos_globais,
                    situacao,
                )
                self.assertEqual(
                    [titulo.id_titulo for titulo in resultado],
                    ids_esperados,
                )

    def test_situacao_mensal_nao_usa_saldo_futuro_do_titulo_parcelado(self):
        titulos_agosto_empresa_1 = [
            SimpleNamespace(id_titulo=11, valor=120),
            SimpleNamespace(id_titulo=12, valor=300),
        ]
        valores_agosto = {11: 30, 12: 100}
        baixas_das_parcelas_de_agosto = {11: 30, 12: 40}
        saldos_agosto = {
            titulo.id_titulo: _calcular_saldo_titulo(
                valores_agosto[titulo.id_titulo],
                baixas_das_parcelas_de_agosto[titulo.id_titulo],
            )
            for titulo in titulos_agosto_empresa_1
        }

        todas = _filtrar_titulos_por_situacao(
            titulos_agosto_empresa_1, saldos_agosto, "todas"
        )
        abertas = _filtrar_titulos_por_situacao(
            titulos_agosto_empresa_1, saldos_agosto, "em_aberto"
        )
        baixadas = _filtrar_titulos_por_situacao(
            titulos_agosto_empresa_1, saldos_agosto, "baixada"
        )

        self.assertEqual([titulo.id_titulo for titulo in todas], [11, 12])
        self.assertEqual([titulo.id_titulo for titulo in abertas], [12])
        self.assertEqual([titulo.id_titulo for titulo in baixadas], [11])
        self.assertEqual(
            {titulo.id_titulo for titulo in todas},
            {titulo.id_titulo for titulo in abertas}
            | {titulo.id_titulo for titulo in baixadas},
        )
        self.assertFalse(
            {titulo.id_titulo for titulo in abertas}
            & {titulo.id_titulo for titulo in baixadas}
        )

    def test_filtro_de_situacao_trata_saldo_ausente_sem_falhar(self):
        titulo_legado = SimpleNamespace(id_titulo=10, valor=80)

        self.assertEqual(
            _filtrar_titulos_por_situacao([titulo_legado], {}, "em_aberto"),
            [titulo_legado],
        )
        self.assertEqual(
            _filtrar_titulos_por_situacao([titulo_legado], {}, "baixada"),
            [],
        )


if __name__ == "__main__":
    unittest.main()
