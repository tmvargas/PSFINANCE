import os
import tempfile
import time
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

    def test_formulario_oferece_busca_e_cadastro_de_credor_sem_sair(self):
        response = app.test_client().get("/financeiro/titulos/novo")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'id="abrir_busca_credor"', response.data)
        self.assertIn(b'id="modal_busca_credor"', response.data)
        self.assertIn(b'id="novo_credor_janela"', response.data)
        self.assertIn(b'window.open(url, "psfinanceCadastroCredor"', response.data)

    def test_busca_credor_filtra_nome_e_ignora_excluidos(self):
        session = SessionLocal()
        session.add_all(
            [
                Credor(nome="Alfa Serviços"),
                Credor(nome="Alfa Excluído", deleted=True),
                Credor(nome="Beta Materiais"),
            ]
        )
        session.commit()
        session.close()

        response = app.test_client().get("/financeiro/credores/busca?q=alfa")

        self.assertEqual(response.status_code, 200)
        nomes = [item["nome"] for item in response.get_json()["credores"]]
        self.assertEqual(nomes, ["Alfa Serviços"])

    def _criar_e_validar_quantidade(self, quantidade):
        response = app.test_client().post(
            "/financeiro/titulos/novo", data=self._dados_titulo(quantidade)
        )

        self.assertEqual(response.status_code, 302)
        session = SessionLocal()
        titulo = session.query(Titulo).filter_by(
            nr_documento=f"PLA-2409-{quantidade}"
        ).one()
        parcelas = (
            session.query(TituloParcela)
            .filter_by(id_titulo=titulo.id_titulo, deleted=False)
            .order_by(TituloParcela.numero_parcela)
            .all()
        )
        self.assertEqual(len(parcelas), quantidade)
        self.assertEqual(parcelas[0].numero_parcela, 1)
        self.assertEqual(parcelas[-1].numero_parcela, quantidade)
        self.assertEqual(sum(float(parcela.valor) for parcela in parcelas), 999.0)
        session.close()
        return titulo.id_titulo

    def test_preserva_limite_anterior_de_120_parcelas(self):
        self._criar_e_validar_quantidade(120)

    def test_aceita_caso_real_de_180_parcelas(self):
        self._criar_e_validar_quantidade(180)

    def test_aceita_999_parcelas(self):
        inicio = time.perf_counter()
        self._criar_e_validar_quantidade(999)
        duracao = time.perf_counter() - inicio

        self.assertLess(duracao, 10.0)
        print(f"DESEMPENHO_PLA_2409_999={duracao:.3f}s")

    def test_copia_preserva_quantidade_e_permanece_editavel(self):
        titulo_original_id = self._criar_e_validar_quantidade(180)
        client = app.test_client()

        copia_form = client.get(f"/financeiro/titulos/{titulo_original_id}/copiar")
        self.assertEqual(copia_form.status_code, 200)
        self.assertIn(b'value="180"', copia_form.data)
        self.assertNotIn(b'name="quantidade_parcelas" disabled', copia_form.data)

        dados_copia = self._dados_titulo(180)
        dados_copia["nr_documento"] = "PLA-2409-COPIA-180"
        copia_response = client.post(
            f"/financeiro/titulos/{titulo_original_id}/copiar", data=dados_copia
        )
        self.assertEqual(copia_response.status_code, 302)

        session = SessionLocal()
        copia = session.query(Titulo).filter_by(
            nr_documento="PLA-2409-COPIA-180"
        ).one()
        quantidade_copia = session.query(TituloParcela).filter_by(
            id_titulo=copia.id_titulo, deleted=False
        ).count()
        self.assertEqual(quantidade_copia, 180)
        session.close()

    def test_edicao_preserva_as_180_parcelas_existentes(self):
        titulo_id = self._criar_e_validar_quantidade(180)
        client = app.test_client()

        edicao_form = client.get(f"/financeiro/titulos/{titulo_id}/editar")
        self.assertEqual(edicao_form.status_code, 200)
        self.assertIn(b'value="180"', edicao_form.data)
        self.assertIn(b'name="quantidade_parcelas"', edicao_form.data)
        self.assertIn(b'disabled', edicao_form.data)

        dados_edicao = self._dados_titulo(1)
        dados_edicao["nr_documento"] = "PLA-2409-EDITADO-180"
        dados_edicao["valor"] = "1099,00"
        response = client.post(
            f"/financeiro/titulos/{titulo_id}/editar", data=dados_edicao
        )
        self.assertEqual(response.status_code, 302)

        session = SessionLocal()
        titulo = session.get(Titulo, titulo_id)
        quantidade = session.query(TituloParcela).filter_by(
            id_titulo=titulo_id, deleted=False
        ).count()
        self.assertEqual(titulo.nr_documento, "PLA-2409-EDITADO-180")
        self.assertEqual(quantidade, 180)
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
