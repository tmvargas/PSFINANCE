import unittest

from database import Base, SessionLocal, engine
from models import Cidade, Cliente
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


if __name__ == "__main__":
    unittest.main()
