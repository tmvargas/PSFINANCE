import unittest
from datetime import date

from financeiro.routes_titulos import (
    _normalizar_busca_titulo,
    _resolver_periodo_vencimento,
    _termo_like_literal,
)


class FiltrosConsultaTitulosTest(unittest.TestCase):
    def setUp(self):
        self.hoje = date(2026, 8, 24)

    def test_modo_padrao_preserva_mes_e_ano(self):
        periodo = _resolver_periodo_vencimento({"mes": "7", "ano": "2026"}, self.hoje)
        self.assertEqual(periodo["modo"], "mes")
        self.assertEqual(periodo["data_ini"], date(2026, 7, 1))
        self.assertEqual(periodo["data_fim"], date(2026, 8, 1))

    def test_periodo_tem_limites_inclusivos(self):
        periodo = _resolver_periodo_vencimento(
            {
                "modo_vencimento": "periodo",
                "vencimento_inicial": "2026-08-10",
                "vencimento_final": "2026-08-20",
            },
            self.hoje,
        )
        self.assertEqual(periodo["modo"], "periodo")
        self.assertEqual(periodo["data_ini"], date(2026, 8, 10))
        self.assertEqual(periodo["data_fim"], date(2026, 8, 21))

    def test_periodo_incompleto_ou_invertido_volta_ao_mes_atual(self):
        casos = (
            {"modo_vencimento": "periodo", "vencimento_inicial": "2026-08-10"},
            {
                "modo_vencimento": "periodo",
                "vencimento_inicial": "2026-08-20",
                "vencimento_final": "2026-08-10",
            },
        )
        for args in casos:
            with self.subTest(args=args):
                periodo = _resolver_periodo_vencimento(args, self.hoje)
                self.assertEqual(periodo["modo"], "mes")
                self.assertEqual(periodo["data_ini"], date(2026, 8, 1))
                self.assertEqual(periodo["data_fim"], date(2026, 9, 1))

    def test_busca_remove_espacos_e_limita_tamanho(self):
        self.assertEqual(_normalizar_busca_titulo("  NF   123  "), "NF 123")
        self.assertEqual(len(_normalizar_busca_titulo("x" * 120)), 80)

    def test_busca_trata_curingas_sql_como_texto_literal(self):
        self.assertEqual(_termo_like_literal(r"NF_100%\\A"), r"NF\_100\%\\\\A")


if __name__ == "__main__":
    unittest.main()
