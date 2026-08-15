import os
import tempfile
import unittest
from datetime import date
from pathlib import Path


TEST_INSTANCE = tempfile.TemporaryDirectory(prefix="psfinance-pla2453-")
os.environ["PSFINANCE_INSTANCE_PATH"] = TEST_INSTANCE.name
os.environ["PSFINANCE_DATABASE_URL"] = f"sqlite:///{Path(TEST_INSTANCE.name) / 'teste.db'}"
os.environ["PSFINANCE_STAGING_BASE_PATH"] = "/staging/psfinance"

from database import Base, SessionLocal, engine  # noqa: E402
from models import (  # noqa: E402
    Baixa,
    Conta,
    Credor,
    Documento,
    Empresa,
    MovimentacaoConta,
    PlanoDeContas,
    Titulo,
)
from src.app import app  # noqa: E402


class FiltroEmpresaAnaliseExtratoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config.update(TESTING=True)

    def setUp(self):
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        session = SessionLocal()

        empresa_a = Empresa(codigo="A", nome="Empresa Alfa", tipo_empresa="EMPRESA")
        empresa_b = Empresa(codigo="B", nome="Empresa Beta", tipo_empresa="EMPRESA")
        conta_a = Conta(empresa=empresa_a, descricao="Conta Alfa", tipo="corrente", saldo_inicial=10)
        conta_b = Conta(empresa=empresa_b, descricao="Conta Beta", tipo="corrente", saldo_inicial=20)
        documento = Documento(tipo_doc="NF", nome_doc="Nota fiscal")
        credor = Credor(nome="Credor teste")
        receita = PlanoDeContas(cod_estrutural="1.01", nome_conta="Receita teste", tipo="analitica")
        despesa = PlanoDeContas(cod_estrutural="2.01", nome_conta="Despesa teste", tipo="analitica")
        mov_a = MovimentacaoConta(
            data=date(2026, 8, 5), tipo="E", documento=documento, nr_documento="A1",
            valor=100, conta_destino=conta_a, empresa=empresa_a, plano=receita,
        )
        mov_b = MovimentacaoConta(
            data=date(2026, 8, 5), tipo="E", documento=documento, nr_documento="B1",
            valor=900, conta_destino=conta_b, empresa=empresa_b, plano=receita,
        )
        titulo_a = Titulo(
            documento=documento, nr_documento="TA", credor=credor, empresa=empresa_a,
            plano=despesa, valor=30, emissao=date(2026, 8, 1), vencimento=date(2026, 8, 10),
        )
        titulo_b = Titulo(
            documento=documento, nr_documento="TB", credor=credor, empresa=empresa_b,
            plano=despesa, valor=70, emissao=date(2026, 8, 1), vencimento=date(2026, 8, 10),
        )
        baixa_a = Baixa(titulo=titulo_a, conta=conta_a, data=date(2026, 8, 8), valor_baixa=30)
        baixa_b = Baixa(titulo=titulo_b, conta=conta_b, data=date(2026, 8, 8), valor_baixa=70)
        session.add_all([mov_a, mov_b, baixa_a, baixa_b])
        session.commit()
        self.empresa_a_id = empresa_a.id_empresa
        self.empresa_b_id = empresa_b.id_empresa
        self.conta_a_id = conta_a.id_conta
        self.conta_b_id = conta_b.id_conta
        session.close()

    def test_analise_filtra_movimentacoes_e_baixas_por_empresa(self):
        response = app.test_client().get(
            f"/financeiro/analise?mes=8&ano=2026&id_empresa={self.empresa_a_id}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"R$ 100.00", response.data)
        self.assertIn(b"R$ 30.00", response.data)
        self.assertNotIn(b"R$ 900.00", response.data)
        self.assertNotIn(b"R$ 1000.00", response.data)

    def test_analise_sem_empresa_preserva_visao_consolidada(self):
        response = app.test_client().get("/financeiro/analise?mes=8&ano=2026")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"R$ 1000.00", response.data)
        self.assertIn(b"R$ 100.00", response.data)

    def test_extrato_lista_so_contas_da_empresa_e_rejeita_conta_cruzada(self):
        client = app.test_client()
        response = client.get(f"/financeiro/extrato?id_empresa={self.empresa_a_id}")
        self.assertIn(b"Conta Alfa", response.data)
        self.assertNotIn(b"Conta Beta", response.data)

        response_cruzada = client.get(
            f"/financeiro/extrato?id_empresa={self.empresa_a_id}&id_conta={self.conta_b_id}"
        )
        self.assertEqual(response_cruzada.status_code, 200)
        self.assertIn(b"Selecione uma conta", response_cruzada.data)
        self.assertNotIn(b"Saldo inicial", response_cruzada.data)

    def test_extrato_empresa_selecionada_mantem_conta_valida(self):
        response = app.test_client().get(
            f"/financeiro/extrato?id_empresa={self.empresa_a_id}&id_conta={self.conta_a_id}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Conta Alfa", response.data)
        self.assertIn(b"Saldo inicial", response.data)

    def test_extrato_recarrega_contas_ao_trocar_empresa_e_limpa_conta_anterior(self):
        response = app.test_client().get(
            f"/financeiro/extrato?id_empresa={self.empresa_a_id}&id_conta={self.conta_a_id}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'id="id_empresa_extrato"', response.data)
        self.assertIn(b'id="id_conta_extrato"', response.data)
        self.assertIn(b'conta.value = ""', response.data)
        self.assertIn(b'empresa.form.submit()', response.data)

    def test_preferencia_e_compartilhada_e_todas_limpa_a_sessao(self):
        client = app.test_client()
        client.get(f"/financeiro/analise?mes=8&ano=2026&id_empresa={self.empresa_a_id}")

        response_extrato = client.get("/financeiro/extrato")
        self.assertIn(b'value="1" selected', response_extrato.data)
        self.assertIn(b"Conta Alfa", response_extrato.data)
        self.assertNotIn(b"Conta Beta", response_extrato.data)

        client.get("/financeiro/extrato?id_empresa=")
        response_sem_preferencia = client.get("/financeiro/extrato")
        self.assertNotIn(b'value="1" selected', response_sem_preferencia.data)
        self.assertIn(b"Conta Alfa", response_sem_preferencia.data)
        self.assertIn(b"Conta Beta", response_sem_preferencia.data)

    def test_empresa_invalida_limpa_preferencia_memorizada(self):
        client = app.test_client()
        client.get(f"/financeiro/analise?id_empresa={self.empresa_a_id}")
        response = client.get("/financeiro/analise?id_empresa=999999")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'value="1" selected', response.data)
        with client.session_transaction() as session_storage:
            self.assertNotIn("titulos_filtro_id_empresa", session_storage)


if __name__ == "__main__":
    unittest.main()
