import os
import tempfile
import unittest
from datetime import date
from pathlib import Path


TEST_INSTANCE = tempfile.TemporaryDirectory(prefix="psfinance-pla743-openfinance-")
os.environ["PSFINANCE_INSTANCE_PATH"] = TEST_INSTANCE.name
os.environ["PSFINANCE_DATABASE_URL"] = f"sqlite:///{Path(TEST_INSTANCE.name) / 'teste.db'}"

from database import Base, SessionLocal, engine  # noqa: E402
from financeiro.openfinance_service import (  # noqa: E402
    OpenFinanceProcessamentoErro,
    processar_transacao,
    registrar_transacoes,
)
from models import (  # noqa: E402
    CentroCusto, Conta, Documento, Empresa, MovimentacaoConta,
    OpenFinanceConexao, OpenFinanceConta, OpenFinanceTransacao, PlanoDeContas,
)


class OpenFinanceTest(unittest.TestCase):
    def setUp(self):
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        session = SessionLocal()
        empresa = Empresa(codigo="2", nome="PS", tipo_empresa="MATRIZ")
        centro = CentroCusto(empresa=empresa, codigo="200", nome="Administrativo")
        conta = Conta(empresa=empresa, descricao="C6 Bank PS", tipo="corrente")
        conexao = OpenFinanceConexao(nome="C6 Bank", ambiente="sandbox")
        conta_of = OpenFinanceConta(
            conexao=conexao, conta=conta, centro_custo=centro,
            external_id="acc-1", tipo="conta_corrente", nome="C6 Bank PS",
        )
        session.add_all([
            empresa, centro, conta, conexao, conta_of,
            Documento(tipo_doc="AV", nome_doc="Aviso"),
            PlanoDeContas(cod_estrutural="1.1", nome_conta="Receita", tipo="analitica"),
            PlanoDeContas(cod_estrutural="2.1", nome_conta="Despesa", tipo="analitica"),
        ])
        session.commit()
        self.conta_of_id = conta_of.id_openfinance_conta
        session.close()

    def _importar(self, natureza="saida", external_id="tx-1"):
        session = SessionLocal()
        conta_of = session.get(OpenFinanceConta, self.conta_of_id)
        criadas = registrar_transacoes(session, conta_of, [{
            "external_id": external_id, "data": date(2026, 9, 30),
            "descricao": "Compra", "valor": "123.45", "natureza": natureza,
        }])
        session.commit()
        transacao_id = criadas[0].id_transacao if criadas else None
        session.close()
        return transacao_id

    def test_importacao_e_idempotente(self):
        self._importar()
        session = SessionLocal()
        conta_of = session.get(OpenFinanceConta, self.conta_of_id)
        repetidas = registrar_transacoes(session, conta_of, [{
            "external_id": "tx-1", "data": date(2026, 9, 30),
            "descricao": "Compra", "valor": "123.45", "natureza": "saida",
        }])
        self.assertEqual(repetidas, [])
        self.assertEqual(session.query(OpenFinanceTransacao).count(), 1)
        session.close()

    def test_saida_processada_vira_movimentacao_conciliavel(self):
        transacao_id = self._importar()
        session = SessionLocal()
        plano = session.query(PlanoDeContas).filter_by(cod_estrutural="2.1").one()
        transacao = session.get(OpenFinanceTransacao, transacao_id)
        movimento = processar_transacao(session, transacao, plano.id_plano)
        session.commit()
        self.assertEqual(movimento.tipo, "S")
        self.assertEqual(movimento.id_conta_origem, transacao.openfinance_conta.id_conta)
        self.assertFalse(movimento.conciliado)
        self.assertEqual(transacao.status, "processada")
        session.close()

    def test_entrada_processada_na_conta_de_destino(self):
        transacao_id = self._importar(natureza="entrada")
        session = SessionLocal()
        plano = session.query(PlanoDeContas).filter_by(cod_estrutural="1.1").one()
        transacao = session.get(OpenFinanceTransacao, transacao_id)
        movimento = processar_transacao(session, transacao, plano.id_plano)
        self.assertEqual(movimento.tipo, "E")
        self.assertEqual(movimento.id_conta_destino, transacao.openfinance_conta.id_conta)
        session.close()

    def test_rejeita_plano_do_grupo_incorreto(self):
        transacao_id = self._importar(natureza="saida")
        session = SessionLocal()
        plano = session.query(PlanoDeContas).filter_by(cod_estrutural="1.1").one()
        with self.assertRaises(OpenFinanceProcessamentoErro):
            processar_transacao(session, session.get(OpenFinanceTransacao, transacao_id), plano.id_plano)
        self.assertEqual(session.query(MovimentacaoConta).count(), 0)
        session.close()

    def test_nao_processa_duas_vezes(self):
        transacao_id = self._importar()
        session = SessionLocal()
        plano = session.query(PlanoDeContas).filter_by(cod_estrutural="2.1").one()
        transacao = session.get(OpenFinanceTransacao, transacao_id)
        processar_transacao(session, transacao, plano.id_plano)
        with self.assertRaises(OpenFinanceProcessamentoErro):
            processar_transacao(session, transacao, plano.id_plano)
        session.close()


if __name__ == "__main__":
    unittest.main()
