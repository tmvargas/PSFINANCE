import os
import tempfile
import unittest
from pathlib import Path


TEST_INSTANCE = tempfile.TemporaryDirectory(prefix="psfinance-pla2409-")
os.environ["PSFINANCE_INSTANCE_PATH"] = TEST_INSTANCE.name
os.environ["PSFINANCE_DATABASE_URL"] = f"sqlite:///{Path(TEST_INSTANCE.name) / 'teste.db'}"
os.environ["PSFINANCE_STAGING_BASE_PATH"] = "/staging/psfinance"

from database import Base, SessionLocal, engine  # noqa: E402
from models import (  # noqa: E402
    CentroCusto,
    Credor,
    Documento,
    Empresa,
    PlanoDeContas,
    Titulo,
    TituloParcela,
)
from src.app import app  # noqa: E402


class LimiteParcelasTituloTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config.update(TESTING=True)

    def setUp(self):
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        session = SessionLocal()
        empresa = Empresa(codigo="1", nome="Empresa teste", tipo_empresa="MATRIZ")
        centro = CentroCusto(empresa=empresa, codigo="100", nome="Centro teste")
        credor = Credor(nome="Credor teste")
        documento = Documento(tipo_doc="NF", nome_doc="Nota fiscal")
        plano = PlanoDeContas(
            cod_estrutural="2.1", nome_conta="Fornecedor", tipo="analitica"
        )
        session.add_all([empresa, centro, credor, documento, plano])
        session.commit()
        self.ids = {
            "id_empresa": empresa.id_empresa,
            "id_centro_custo": centro.id_centro_custo,
            "id_credor": credor.id_credor,
            "id_doc": documento.id_doc,
            "id_plano": plano.id_plano,
        }
        session.close()

    def _dados_titulo(self, quantidade):
        return {
            **{chave: str(valor) for chave, valor in self.ids.items()},
            "nr_documento": f"PLA-2409-{quantidade}",
            "valor": "999,00",
            "emissao": "2026-08-13",
            "vencimento": "2026-08-31",
            "quantidade_parcelas": str(quantidade),
        }

    def test_formulario_expoe_limite_999(self):
        response = app.test_client().get("/financeiro/titulos/novo")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'max="999"', response.data)
        self.assertIn(b"Math.min(999,", response.data)

    def test_aceita_999_parcelas(self):
        response = app.test_client().post(
            "/financeiro/titulos/novo", data=self._dados_titulo(999)
        )

        self.assertEqual(response.status_code, 302)
        session = SessionLocal()
        titulo = session.query(Titulo).filter_by(nr_documento="PLA-2409-999").one()
        parcelas = (
            session.query(TituloParcela)
            .filter_by(id_titulo=titulo.id_titulo, deleted=False)
            .order_by(TituloParcela.numero_parcela)
            .all()
        )
        self.assertEqual(len(parcelas), 999)
        self.assertEqual(parcelas[0].numero_parcela, 1)
        self.assertEqual(parcelas[-1].numero_parcela, 999)
        self.assertEqual(sum(float(parcela.valor) for parcela in parcelas), 999.0)
        session.close()

    def test_rejeita_1000_parcelas(self):
        response = app.test_client().post(
            "/financeiro/titulos/novo",
            data=self._dados_titulo(1000),
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Quantidade de parcelas deve estar entre 1 e 999.", response.data)
        session = SessionLocal()
        self.assertEqual(session.query(Titulo).count(), 0)
        self.assertEqual(session.query(TituloParcela).count(), 0)
        session.close()


if __name__ == "__main__":
    unittest.main()
