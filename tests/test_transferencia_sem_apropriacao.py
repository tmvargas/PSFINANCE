import os
import tempfile
import unittest
from datetime import date
from pathlib import Path


TEST_INSTANCE = tempfile.TemporaryDirectory(prefix="psfinance-pla2581-")
os.environ["PSFINANCE_INSTANCE_PATH"] = TEST_INSTANCE.name
os.environ["PSFINANCE_DATABASE_URL"] = f"sqlite:///{Path(TEST_INSTANCE.name) / 'teste.db'}"

from database import Base, SessionLocal, engine  # noqa: E402
from models import (  # noqa: E402
    CentroCusto,
    Conta,
    Documento,
    Empresa,
    MovimentacaoConta,
    PlanoDeContas,
)
from src.app import app  # noqa: E402


class TransferenciaSemApropriacaoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config.update(TESTING=True)

    def setUp(self):
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        session = SessionLocal()
        empresa = Empresa(codigo="1", nome="Empresa teste", tipo_empresa="MATRIZ")
        centro = CentroCusto(empresa=empresa, codigo="100", nome="Centro teste")
        origem = Conta(descricao="Origem", empresa=empresa, tipo="corrente")
        destino = Conta(descricao="Destino", empresa=empresa, tipo="corrente")
        documento = Documento(tipo_doc="AV", nome_doc="Aviso")
        plano = PlanoDeContas(
            cod_estrutural="1.1", nome_conta="Receita", tipo="analitica"
        )
        plano_saida = PlanoDeContas(
            cod_estrutural="2.1", nome_conta="Despesa", tipo="analitica"
        )
        outra_empresa = Empresa(
            codigo="2", nome="Outra empresa", tipo_empresa="MATRIZ"
        )
        conta_outra_empresa = Conta(
            descricao="Conta externa", empresa=outra_empresa, tipo="corrente"
        )
        session.add_all(
            [
                empresa,
                centro,
                origem,
                destino,
                documento,
                plano,
                plano_saida,
                outra_empresa,
                conta_outra_empresa,
            ]
        )
        session.commit()
        self.ids = {
            "id_empresa": empresa.id_empresa,
            "id_centro_custo": centro.id_centro_custo,
            "id_conta_origem": origem.id_conta,
            "id_conta_destino": destino.id_conta,
            "id_plano": plano.id_plano,
            "id_plano_saida": plano_saida.id_plano,
            "id_conta_outra_empresa": conta_outra_empresa.id_conta,
        }
        session.close()

    def _dados_transferencia(self):
        return {
            "tipo": "T",
            "data": date.today().isoformat(),
            "documento": "AV",
            "nr_documento": "PLA-2581",
            "descricao": "Transferência sem apropriação",
            "valor": "100,00",
            **{chave: str(valor) for chave, valor in self.ids.items()},
        }

    def test_criacao_ignora_centro_custo_e_plano_enviados(self):
        response = app.test_client().post(
            "/financeiro/movimentacoes/nova", data=self._dados_transferencia()
        )

        self.assertEqual(response.status_code, 302)
        session = SessionLocal()
        movimento = session.query(MovimentacaoConta).one()
        self.assertEqual(movimento.tipo, "T")
        self.assertIsNone(movimento.id_centro_custo)
        self.assertIsNone(movimento.id_plano)
        session.close()

    def test_transferencia_cria_um_unico_movimento_com_origem_e_destino(self):
        response = app.test_client().post(
            "/financeiro/movimentacoes/nova", data=self._dados_transferencia()
        )

        self.assertEqual(response.status_code, 302)
        session = SessionLocal()
        movimentos = session.query(MovimentacaoConta).all()
        self.assertEqual(len(movimentos), 1)
        self.assertEqual(movimentos[0].id_conta_origem, self.ids["id_conta_origem"])
        self.assertEqual(movimentos[0].id_conta_destino, self.ids["id_conta_destino"])
        session.close()

    def test_transferencia_rejeita_origem_igual_ao_destino(self):
        dados = self._dados_transferencia()
        dados["id_conta_destino"] = dados["id_conta_origem"]

        response = app.test_client().post(
            "/financeiro/movimentacoes/nova", data=dados
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Conta de origem e destino n\xc3\xa3o podem ser a mesma", response.data)
        session = SessionLocal()
        self.assertEqual(session.query(MovimentacaoConta).count(), 0)
        session.close()

    def test_transferencia_rejeita_conta_de_outra_empresa(self):
        dados = self._dados_transferencia()
        dados["id_conta_destino"] = str(self.ids["id_conta_outra_empresa"])

        response = app.test_client().post(
            "/financeiro/movimentacoes/nova", data=dados
        )

        self.assertEqual(response.status_code, 200)
        session = SessionLocal()
        self.assertEqual(session.query(MovimentacaoConta).count(), 0)
        session.close()

    def test_entrada_e_saida_continuam_exigindo_centro_e_plano(self):
        base = self._dados_transferencia()
        base["id_conta"] = str(self.ids["id_conta_origem"])
        base["id_centro_custo"] = ""
        base["id_plano"] = ""

        for tipo in ("E", "S"):
            with self.subTest(tipo=tipo):
                dados = {**base, "tipo": tipo}
                response = app.test_client().post(
                    "/financeiro/movimentacoes/nova", data=dados
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn(b"Centro de custo \xc3\xa9 obrigat\xc3\xb3rio", response.data)
                self.assertIn(b"Selecione o plano financeiro", response.data)

        session = SessionLocal()
        self.assertEqual(session.query(MovimentacaoConta).count(), 0)
        session.close()

    def test_edicao_remove_apropriacoes_antigas_da_transferencia(self):
        session = SessionLocal()
        movimento = MovimentacaoConta(
            tipo="T",
            data=date.today(),
            id_doc=session.query(Documento).one().id_doc,
            nr_documento="LEGADO",
            valor=100,
            id_empresa=self.ids["id_empresa"],
            id_centro_custo=self.ids["id_centro_custo"],
            id_plano=self.ids["id_plano"],
            id_conta_origem=self.ids["id_conta_origem"],
            id_conta_destino=self.ids["id_conta_destino"],
        )
        session.add(movimento)
        session.commit()
        movimento_id = movimento.id_movimentacao
        session.close()

        response = app.test_client().post(
            f"/financeiro/movimentacoes/{movimento_id}/editar",
            data=self._dados_transferencia(),
        )

        self.assertEqual(response.status_code, 302)
        session = SessionLocal()
        movimento = session.get(MovimentacaoConta, movimento_id)
        self.assertIsNone(movimento.id_centro_custo)
        self.assertIsNone(movimento.id_plano)
        session.close()

    def test_formularios_controlam_centro_de_custo_por_tipo(self):
        novo = app.test_client().get("/financeiro/movimentacoes/nova")

        self.assertEqual(novo.status_code, 200)
        self.assertIn(b'id="col_centro_custo"', novo.data)
        self.assertIn(b'centroCusto.removeAttribute("required")', novo.data)
        self.assertIn(b'centroCusto.setAttribute("required", "required")', novo.data)


if __name__ == "__main__":
    unittest.main()
