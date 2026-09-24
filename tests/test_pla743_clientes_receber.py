import unittest
from datetime import date

from database import Base, SessionLocal, engine
from models import (Cidade, Cliente, Conta, Documento, Empresa, PlanoDeContas,
                    Recebimento, Recebivel, RecebivelParcela)
from src.app import app


class ClientesReceberTest(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        Base.metadata.drop_all(engine); Base.metadata.create_all(engine)
        session = SessionLocal(); cidade = Cidade(nome="Curitiba"); session.add(cidade); session.commit()
        self.id_cidade = cidade.id_cidade; session.close(); self.client = app.test_client()

    def test_crud_busca_e_popup_cliente(self):
        resposta = self.client.post("/financeiro/clientes/novo", data={
            "nome": "Cliente Alfa", "cpf_cnpj": "12.345.678/0001-90",
            "id_cidade": self.id_cidade, "email": "financeiro@alfa.test",
        }, follow_redirects=True)
        self.assertIn("Cliente cadastrado com sucesso", resposta.get_data(as_text=True))
        session = SessionLocal(); cliente = session.query(Cliente).one(); cliente_id = cliente.id_cliente; session.close()
        busca = self.client.get(f"/financeiro/clientes/busca?q={cliente_id}").get_json()
        self.assertEqual(busca["clientes"], [{"id": cliente_id, "nome": "Cliente Alfa"}])
        resposta = self.client.post(f"/financeiro/clientes/{cliente_id}/editar", data={
            "nome": "Cliente Beta", "id_cidade": self.id_cidade, "fone": "41999990000",
        }, follow_redirects=True)
        self.assertIn("Cliente atualizado com sucesso", resposta.get_data(as_text=True))
        session = SessionLocal(); self.assertEqual(session.get(Cliente, cliente_id).nome, "Cliente Beta"); session.close()
        popup = self.client.get(f"/financeiro/clientes/novo?origem=recebivel&criado={cliente_id}")
        self.assertIn("psfinance:cliente-criado", popup.get_data(as_text=True))

    def test_rejeita_nome_vazio_e_cidade_inexistente(self):
        resposta = self.client.post("/financeiro/clientes/novo", data={"nome": "", "id_cidade": "999"})
        html = resposta.get_data(as_text=True)
        self.assertIn("Nome do cliente é obrigatório", html)
        self.assertIn("Cidade selecionada não existe", html)
        session = SessionLocal(); self.assertEqual(session.query(Cliente).count(), 0); session.close()

    def test_cidade_zero_e_normalizada_e_formulario_repete_padrao_credor(self):
        resposta = self.client.post("/financeiro/clientes/novo", data={
            "nome": "Cliente sem cidade", "id_cidade": "0",
        }, follow_redirects=True)
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Cliente cadastrado com sucesso", resposta.get_data(as_text=True))
        session = SessionLocal(); self.assertIsNone(session.query(Cliente).one().id_cidade); session.close()
        formulario = self.client.get("/financeiro/clientes/novo").get_data(as_text=True)
        for evidencia in (
            'id="cidade_codigo"', 'id="cidade_nome"', 'id="abrir_busca_cidade"',
            'id="limpar_cidade"', 'id="modal_busca_cidade"', 'id="nova_cidade_popup"',
        ):
            self.assertIn(evidencia, formulario)

    def test_dominio_recebivel_calcula_saldo_por_parcela_e_recebimento(self):
        session = SessionLocal()
        cliente = Cliente(nome="Cliente")
        empresa = Empresa(codigo="1", nome="Empresa", tipo_empresa="MATRIZ")
        documento = Documento(tipo_doc="REC", nome_doc="Recebível")
        plano = PlanoDeContas(cod_estrutural="1.01", nome_conta="Receitas", tipo="analitica")
        conta = Conta(descricao="Banco", empresa=empresa, tipo="corrente")
        recebivel = Recebivel(documento=documento, nr_documento="R-1", cliente=cliente,
            empresa=empresa, plano=plano, valor=300, emissao=date(2026, 9, 1),
            vencimento=date(2026, 10, 10))
        recebivel.parcelas = [
            RecebivelParcela(numero_parcela=1, vencimento=date(2026, 10, 10), valor=150),
            RecebivelParcela(numero_parcela=2, vencimento=date(2026, 11, 10), valor=150),
        ]
        session.add_all([recebivel, conta]); session.flush()
        session.add(Recebimento(data=date(2026, 10, 10), conta=conta, recebivel=recebivel,
            parcela=recebivel.parcelas[0], valor_recebido=100))
        session.commit(); session.refresh(recebivel)
        self.assertEqual(len(recebivel.parcelas), 2)
        self.assertEqual(recebivel.total_recebido, 100.0)
        self.assertEqual(recebivel.saldo_aberto, 200.0)
        session.close()


if __name__ == "__main__":
    unittest.main()
