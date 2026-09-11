import unittest
from datetime import date

from database import Base, SessionLocal, engine
from financeiro.routes_titulos import _previsoes_cartao_credito, _proximo_vencimento_cartao
from models import Conta, Documento, Empresa, MovimentacaoConta
from src.app import app


class CartaoCreditoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config.update(TESTING=True)

    def setUp(self):
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        session = SessionLocal()
        empresa = Empresa(codigo="1", nome="Empresa", tipo_empresa="MATRIZ")
        documento = Documento(tipo_doc="CT", nome_doc="Cartão")
        self.cartao = Conta(
            empresa=empresa,
            descricao="Cartão corporativo",
            tipo="cartao_credito",
            dia_vencimento_cartao=10,
        )
        self.banco = Conta(empresa=empresa, descricao="Banco", tipo="corrente")
        session.add_all([empresa, documento, self.cartao, self.banco])
        session.flush()
        session.add_all([
            MovimentacaoConta(
                data=date(2026, 9, 1), tipo="S", documento=documento,
                nr_documento="COMPRA", valor=300, conta_origem=self.cartao, empresa=empresa,
            ),
            MovimentacaoConta(
                data=date(2026, 9, 5), tipo="T", documento=documento,
                nr_documento="PAG-PARCIAL", valor=100,
                conta_origem=self.banco, conta_destino=self.cartao, empresa=empresa,
            ),
        ])
        session.commit()
        self.id_empresa = empresa.id_empresa
        self.id_cartao = self.cartao.id_conta
        self.id_banco = self.banco.id_conta
        self.id_documento = documento.id_doc
        session.close()

    def _previsoes(self, hoje, inicio, fim, **filtros):
        session = SessionLocal()
        result = _previsoes_cartao_credito(
            session, hoje, inicio, fim, filtros.get("id_empresa"),
            filtros.get("id_credor"), filtros.get("emissao"),
            filtros.get("busca", ""), filtros.get("situacao", "todas"),
        )
        session.close()
        return result

    def test_proximo_vencimento_e_ultimo_dia_do_mes(self):
        self.assertEqual(_proximo_vencimento_cartao(date(2026, 9, 10), 10), date(2026, 9, 10))
        self.assertEqual(_proximo_vencimento_cartao(date(2026, 9, 11), 10), date(2026, 10, 10))
        self.assertEqual(_proximo_vencimento_cartao(date(2027, 2, 1), 31), date(2027, 2, 28))

    def test_transferencia_parcial_mantem_previsao_no_proximo_vencimento(self):
        previsoes = self._previsoes(
            date(2026, 9, 11), date(2026, 10, 1), date(2026, 11, 1),
        )
        self.assertEqual(len(previsoes), 1)
        self.assertEqual(previsoes[0]["id"], f"cartao-{self.id_cartao}")
        self.assertEqual(previsoes[0]["vencimento"], "10/10/2026")
        self.assertEqual(previsoes[0]["nao_pago_mes"], 200.0)

    def test_transferencia_total_remove_previsao(self):
        session = SessionLocal()
        session.add(MovimentacaoConta(
            data=date(2026, 9, 6), tipo="T", id_doc=self.id_documento,
            nr_documento="PAG-RESTANTE", valor=200,
            id_conta_origem=self.id_banco, id_conta_destino=self.id_cartao,
            id_empresa=self.id_empresa,
        ))
        session.commit()
        session.close()
        self.assertEqual(
            self._previsoes(date(2026, 9, 11), date(2026, 10, 1), date(2026, 11, 1)),
            [],
        )

    def test_filtros_incompativeis_ocultam_previsao(self):
        periodo = (date(2026, 10, 1), date(2026, 11, 1))
        self.assertEqual(self._previsoes(date(2026, 9, 11), *periodo, situacao="baixada"), [])
        self.assertEqual(self._previsoes(date(2026, 9, 11), *periodo, id_credor=1), [])
        self.assertEqual(self._previsoes(date(2026, 9, 11), *periodo, busca="inexistente"), [])
        self.assertEqual(len(self._previsoes(date(2026, 9, 11), *periodo, busca="corporativo")), 1)

    def test_formulario_exige_vencimento_somente_para_cartao(self):
        client = app.test_client()
        invalido = client.post("/financeiro/contas/nova", data={
            "descricao": "Cartão inválido", "id_empresa": self.id_empresa,
            "tipo": "cartao_credito", "dia_vencimento_cartao": "",
        })
        self.assertIn("Informe o dia de vencimento", invalido.get_data(as_text=True))
        comum = client.post("/financeiro/contas/nova", data={
            "descricao": "Caixa novo", "id_empresa": self.id_empresa,
            "tipo": "caixa", "dia_vencimento_cartao": "10",
        })
        self.assertEqual(comum.status_code, 302)
        session = SessionLocal()
        self.assertIsNone(session.query(Conta).filter_by(descricao="Caixa novo").one().dia_vencimento_cartao)
        session.close()

    def test_consulta_titulos_renderiza_previsao_e_link_para_extrato(self):
        response = app.test_client().get(
            f"/financeiro/titulos?mes=9&ano=2026&id_empresa={self.id_empresa}&situacao=em_aberto"
        )
        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Previsão de cartão", html)
        self.assertIn("Cartão corporativo", html)
        self.assertIn("10/09/2026", html)
        self.assertIn("200.00", html)
        self.assertIn(f"id_conta={self.id_cartao}", html)


if __name__ == "__main__":
    unittest.main()
