import os
import tempfile
import unittest
from datetime import date
from pathlib import Path


TEST_INSTANCE = tempfile.TemporaryDirectory(prefix="psfinance-pla2407-")
os.environ["PSFINANCE_INSTANCE_PATH"] = TEST_INSTANCE.name
os.environ["PSFINANCE_DATABASE_URL"] = f"sqlite:///{Path(TEST_INSTANCE.name) / 'teste.db'}"
os.environ["PSFINANCE_STAGING_BASE_PATH"] = "/staging/psfinance"

from database import Base, SessionLocal, engine  # noqa: E402
from models import (  # noqa: E402
    Baixa,
    CentroCusto,
    Conta,
    Credor,
    Documento,
    Empresa,
    PlanoDeContas,
    Titulo,
    TituloParcela,
)
from src.app import app  # noqa: E402


class ExclusaoParcelaComBaixaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config.update(TESTING=True)

    def setUp(self):
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        session = SessionLocal()

        empresa = Empresa(codigo="1", nome="Empresa teste", tipo_empresa="MATRIZ")
        centro = CentroCusto(empresa=empresa, codigo="100", nome="Centro teste")
        conta = Conta(empresa=empresa, descricao="Conta teste", tipo="corrente")
        credor = Credor(nome="Credor teste")
        documento = Documento(tipo_doc="NF", nome_doc="Nota fiscal")
        plano = PlanoDeContas(
            cod_estrutural="2.1", nome_conta="Fornecedor", tipo="analitica"
        )
        titulo = Titulo(
            documento=documento,
            nr_documento="PLA-2407",
            credor=credor,
            empresa=empresa,
            centro_custo=centro,
            plano=plano,
            valor=200,
            emissao=date(2026, 8, 1),
            vencimento=date(2026, 8, 10),
        )
        parcela_com_baixa = TituloParcela(
            titulo=titulo,
            numero_parcela=1,
            vencimento=date(2026, 8, 10),
            valor=100,
        )
        parcela_sem_baixa = TituloParcela(
            titulo=titulo,
            numero_parcela=2,
            vencimento=date(2026, 9, 10),
            valor=100,
        )
        baixa = Baixa(
            titulo=titulo,
            parcela=parcela_com_baixa,
            conta=conta,
            data=date(2026, 8, 5),
            valor_baixa=50,
        )
        session.add_all([titulo, parcela_com_baixa, parcela_sem_baixa, baixa])
        session.commit()
        self.titulo_id = titulo.id_titulo
        self.parcela_com_baixa_id = parcela_com_baixa.id_parcela
        self.parcela_sem_baixa_id = parcela_sem_baixa.id_parcela
        session.close()

    def _dados_post(self, excluir_id):
        return {
            "parcela_id": [
                str(self.parcela_com_baixa_id),
                str(self.parcela_sem_baixa_id),
            ],
            "numero_parcela": ["1", "2"],
            "vencimento_parcela": ["2026-08-10", "2026-09-10"],
            "valor_parcela": ["100,00", "100,00"],
            "excluir_parcela": str(excluir_id),
        }

    def test_bloqueia_exclusao_no_backend_mesmo_com_post_manipulado(self):
        response = app.test_client().post(
            f"/financeiro/titulos/{self.titulo_id}/parcelas",
            data=self._dados_post(self.parcela_com_baixa_id),
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"possui baixa", response.data)
        session = SessionLocal()
        parcela = session.get(TituloParcela, self.parcela_com_baixa_id)
        self.assertFalse(parcela.deleted)
        session.close()

    def test_interface_desabilita_lixeira_apenas_da_parcela_com_baixa(self):
        response = app.test_client().get(
            f"/financeiro/titulos/{self.titulo_id}/parcelas"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Parcela com baixa n\xc3\xa3o pode ser exclu\xc3\xadda", response.data)
        self.assertIn(b"Possui baixa", response.data)
        html = response.get_data(as_text=True)
        inicio_botao = html.index('aria-label="Excluir parcela 1"')
        fim_botao = html.index("</button>", inicio_botao)
        self.assertIn("disabled", html[inicio_botao:fim_botao])

        inicio_botao_livre = html.index('aria-label="Excluir parcela 2"')
        fim_botao_livre = html.index("</button>", inicio_botao_livre)
        self.assertNotIn("disabled", html[inicio_botao_livre:fim_botao_livre])

    def test_preserva_exclusao_de_parcela_sem_baixa(self):
        response = app.test_client().post(
            f"/financeiro/titulos/{self.titulo_id}/parcelas",
            data=self._dados_post(self.parcela_sem_baixa_id),
        )

        self.assertEqual(response.status_code, 302)
        session = SessionLocal()
        parcela = session.get(TituloParcela, self.parcela_sem_baixa_id)
        self.assertTrue(parcela.deleted)
        session.close()


if __name__ == "__main__":
    unittest.main()
