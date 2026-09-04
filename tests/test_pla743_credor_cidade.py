import unittest
from datetime import date

from database import Base, SessionLocal, engine
from models import CentroCusto, Cidade, Credor, Documento, Empresa, PlanoDeContas, Titulo
from src.app import app


class CredorCidadeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config.update(TESTING=True)

    def setUp(self):
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        session = SessionLocal()
        self.cidade = Cidade(nome="Porto Alegre")
        session.add_all([self.cidade, Cidade(nome="Canoas")])
        session.commit()
        self.id_cidade = self.cidade.id_cidade
        session.close()

    def test_busca_cidade_por_codigo_e_parte_do_nome(self):
        client = app.test_client()
        por_codigo = client.get(f"/financeiro/cidades/busca?q={self.id_cidade}").get_json()["cidades"]
        por_nome = client.get("/financeiro/cidades/busca?q=alegre").get_json()["cidades"]
        self.assertEqual(por_codigo, [{"id": self.id_cidade, "nome": "Porto Alegre"}])
        self.assertEqual(por_nome, por_codigo)

    def test_formulario_permite_editar_limpar_e_resolver_cidade(self):
        html = app.test_client().get("/financeiro/credores/novo").get_data(as_text=True)
        self.assertIn('id="cidade_nome"', html)
        self.assertNotIn('id="cidade_nome" class="form-control" value="" placeholder="Nome da cidade" readonly', html)
        self.assertIn('id="limpar_cidade"', html)
        self.assertIn("resolver(codigo.value,'codigo')", html)
        self.assertIn("resolver(nome.value,'nome')", html)
        self.assertIn("revisaoConsulta!==revisao", html)
        self.assertIn("Selecione uma cidade válida ou limpe o campo.", html)

    def test_cadastro_popup_tem_layout_proprio_sem_menu_e_header(self):
        client = app.test_client()
        popup = client.get("/financeiro/cidades/nova?origem=credor").get_data(as_text=True)
        pagina = client.get("/financeiro/cidades/nova").get_data(as_text=True)
        self.assertIn('class="popup-page"', popup)
        self.assertIn('class="popup-shell"', popup)
        self.assertNotIn('class="app-shell', popup)
        self.assertNotIn('class="sidebar"', popup)
        self.assertIn('class="app-shell', pagina)

    def test_cadastro_popup_salva_retorna_e_fecha(self):
        response = app.test_client().post(
            "/financeiro/cidades/nova",
            data={"origem": "credor", "nome": "São Leopoldo"},
        )
        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("psfinance:cidade-criada", html)
        self.assertIn('"nome": "S\\u00e3o Leopoldo"', html)
        self.assertIn("window.close()", html)
        session = SessionLocal()
        self.assertIsNotNone(session.query(Cidade).filter_by(nome="São Leopoldo", deleted=False).one_or_none())
        session.close()

    def test_busca_cidade_nao_usa_botao_limpar_nativo_sobreposto(self):
        html = app.test_client().get("/financeiro/credores/novo").get_data(as_text=True)
        self.assertIn('type="text" id="busca_cidade"', html)
        self.assertNotIn('type="search" id="busca_cidade"', html)
        self.assertIn("document.body.appendChild(modal)", html)

    def test_credor_persiste_novos_campos_e_cidade(self):
        response = app.test_client().post("/financeiro/credores/novo", data={
            "nome": "Fornecedor completo", "cnpj": "12.345.678/0001-90", "endereco": "Rua Um, 10",
            "bairro": "Centro", "cep": "90000-000", "id_cidade": str(self.id_cidade),
            "whats": "51999999999", "fone": "5133333333", "email": "financeiro@example.com",
        })
        self.assertEqual(response.status_code, 302)
        session = SessionLocal()
        credor = session.query(Credor).filter_by(nome="Fornecedor completo").one()
        self.assertEqual(credor.id_cidade, self.id_cidade)
        self.assertEqual(credor.cnpj, "12.345.678/0001-90")
        self.assertEqual(credor.email, "financeiro@example.com")
        session.close()

    def test_exclusao_credor_bloqueia_com_titulo_e_libera_sem_titulo(self):
        session = SessionLocal()
        empresa = Empresa(codigo="1", nome="Empresa", tipo_empresa="MATRIZ")
        centro = CentroCusto(empresa=empresa, codigo="1", nome="Centro")
        documento = Documento(tipo_doc="NF", nome_doc="Nota")
        plano = PlanoDeContas(cod_estrutural="2.1", nome_conta="Despesa", tipo="analitica")
        usado, livre = Credor(nome="Usado"), Credor(nome="Livre")
        session.add_all([empresa, centro, documento, plano, usado, livre])
        session.flush()
        session.add(Titulo(id_doc=documento.id_doc, nr_documento="1", id_credor=usado.id_credor,
                           id_empresa=empresa.id_empresa, id_centro_custo=centro.id_centro_custo,
                           id_plano=plano.id_plano, valor=10, emissao=date.today(), vencimento=date.today()))
        session.commit()
        usados = usado.id_credor, livre.id_credor
        session.close()
        client = app.test_client()
        client.post(f"/financeiro/credores/{usados[0]}/excluir")
        client.post(f"/financeiro/credores/{usados[1]}/excluir")
        session = SessionLocal()
        self.assertFalse(session.get(Credor, usados[0]).deleted)
        self.assertTrue(session.get(Credor, usados[1]).deleted)
        session.close()


if __name__ == "__main__":
    unittest.main()
