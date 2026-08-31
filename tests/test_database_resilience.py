import os
import unittest
from unittest.mock import patch

from database import engine_options


class DatabaseResilienceTest(unittest.TestCase):
    def test_postgresql_recebe_limites_para_nao_prender_workers(self):
        with patch.dict(os.environ, {}, clear=True):
            options = engine_options("postgresql://usuario:senha@127.0.0.1/banco")

        self.assertEqual(options["pool_recycle"], 300)
        self.assertEqual(options["pool_timeout"], 5)
        self.assertEqual(options["connect_args"]["connect_timeout"], 5)
        self.assertIn("statement_timeout=10000", options["connect_args"]["options"])
        self.assertIn("lock_timeout=3000", options["connect_args"]["options"])

    def test_sqlite_nao_recebe_opcoes_exclusivas_do_postgresql(self):
        options = engine_options("sqlite:///:memory:")

        self.assertTrue(options["pool_pre_ping"])
        self.assertNotIn("connect_args", options)
        self.assertNotIn("pool_timeout", options)

    def test_valores_invalidos_voltam_aos_limites_seguros(self):
        environment = {
            "PSFINANCE_DB_CONNECT_TIMEOUT": "invalido",
            "PSFINANCE_DB_STATEMENT_TIMEOUT_MS": "0",
            "PSFINANCE_DB_LOCK_TIMEOUT_MS": "-1",
        }
        with patch.dict(os.environ, environment, clear=True):
            options = engine_options("postgresql+psycopg2://usuario:senha@localhost/banco")

        self.assertEqual(options["connect_args"]["connect_timeout"], 5)
        self.assertIn("statement_timeout=10000", options["connect_args"]["options"])
        self.assertIn("lock_timeout=3000", options["connect_args"]["options"])


if __name__ == "__main__":
    unittest.main()
