import re
import unittest
from pathlib import Path


SQL_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts/sql/PLA-2612_prevalidacao_postgresql_isolado.sql"
)


class PrevalidacaoSqlPla2612Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL_PATH.read_text(encoding="utf-8")

    def test_permanece_read_only_e_interrompe_no_primeiro_erro(self):
        self.assertIn(r"\set ON_ERROR_STOP on", self.sql)
        self.assertIn("BEGIN TRANSACTION READ ONLY", self.sql)
        self.assertNotRegex(
            self.sql,
            re.compile(r"^\s*(INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|TRUNCATE)\b", re.I | re.M),
        )

    def test_schema_e_nulabilidade_possuem_gate_fail_closed(self):
        self.assertIn("schema/nulabilidade divergente", self.sql)
        self.assertIn("f.coluna IS NULL OR f.tipo <> e.tipo OR f.nullable <> e.nullable", self.sql)
        self.assertIn("RAISE EXCEPTION", self.sql)
        self.assertIn("SCHEMA_NULABILIDADE_OK", self.sql)

    def test_locks_e_concorrencia_possuem_gate_fail_closed(self):
        self.assertIn("a.xact_start IS NOT NULL OR a.wait_event IS NOT NULL", self.sql)
        self.assertIn("AND NOT l.granted", self.sql)
        self.assertIn("concorrencia/lock inesperado", self.sql)
        self.assertIn("LOCKS_OK", self.sql)

    def test_limite_sintetico_e_obrigatorio_e_menor_que_vinte(self):
        self.assertIn("pla2612.synthetic_records", self.sql)
        self.assertIn("quantidade < 1 OR quantidade >= 20", self.sql)
        self.assertIn("limite sintetico excedido", self.sql)
        self.assertIn("LIMITE_SINTETICO_OK", self.sql)


if __name__ == "__main__":
    unittest.main()
