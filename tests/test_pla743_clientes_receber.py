import unittest
from datetime import date

from database import Base, SessionLocal, engine
from models import (CentroCusto, Cidade, Cliente, Conta, Documento, Empresa, PlanoDeContas,
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

    def test_rotina_receber_replica_titulos_parcelas_baixas_e_anexos(self):
        lista = self.client.get("/financeiro/receber/titulos")
        novo = self.client.get("/financeiro/receber/titulos/novo")
        self.assertEqual(lista.status_code, 200)
        self.assertEqual(novo.status_code, 200)
        html = novo.get_data(as_text=True)
        self.assertIn("Parcelas", html)
        self.assertIn("Anexos", html)
        self.assertIn("Cliente", html)
        self.assertIn("Contas a Receber", html)
        self.assertNotIn("clientees", html)
        regras = {r.endpoint for r in app.url_map.iter_rules() if r.endpoint.startswith("receber.")}
        for endpoint in ("receber.editar_parcelas_titulo", "receber.baixar_titulo",
                         "receber.listar_baixas_titulo", "receber.excluir_baixa",
                         "receber.download_anexo_titulo"):
            self.assertIn(endpoint, regras)

    def test_jornada_titulo_parcelado_baixa_parcial_estorno_e_plano_de_entrada(self):
        session = SessionLocal()
        cliente = Cliente(nome="Cliente Jornada")
        empresa = Empresa(codigo="10", nome="Empresa Jornada", tipo_empresa="MATRIZ")
        centro = CentroCusto(codigo="10.01", nome="Operação", empresa=empresa)
        documento = Documento(tipo_doc="REC", nome_doc="Receita")
        plano_entrada = PlanoDeContas(cod_estrutural="1.01", nome_conta="Receita", tipo="analitica")
        plano_saida = PlanoDeContas(cod_estrutural="2.01", nome_conta="Despesa", tipo="analitica")
        conta = Conta(descricao="Banco Jornada", empresa=empresa, tipo="corrente")
        session.add_all([cliente, empresa, centro, documento, plano_entrada, plano_saida, conta])
        session.commit()
        ids = {
            "cliente": cliente.id_cliente, "empresa": empresa.id_empresa,
            "centro": centro.id_centro_custo, "documento": documento.id_doc,
            "entrada": plano_entrada.id_plano, "saida": plano_saida.id_plano,
            "conta": conta.id_conta,
        }
        session.close()

        dados = {
            "id_doc": ids["documento"], "nr_documento": "REC-100",
            "id_cliente": ids["cliente"], "id_empresa": ids["empresa"],
            "id_centro_custo": ids["centro"], "id_plano": ids["entrada"],
            "valor": "300,00", "emissao": "2026-09-01",
            "vencimento": "2026-10-10", "quantidade_parcelas": "2",
        }
        resposta = self.client.post("/financeiro/receber/titulos/novo", data=dados, follow_redirects=True)
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("2 parcelas salvas com sucesso", resposta.get_data(as_text=True))

        session = SessionLocal()
        titulo = session.query(Recebivel).filter_by(nr_documento="REC-100").one()
        self.assertEqual(len(titulo.parcelas), 2)
        self.assertEqual([float(p.valor) for p in titulo.parcelas], [150.0, 150.0])
        id_recebivel = titulo.id_recebivel
        id_parcela = titulo.parcelas[0].id_parcela
        session.close()

        baixa = self.client.post(f"/financeiro/receber/titulos/{id_recebivel}/baixar", data={
            "data": "2026-10-10", "id_conta": ids["conta"],
            "id_parcela": id_parcela, "valor_recebido": "100,00",
        }, follow_redirects=True)
        self.assertIn("Baixa registrada com sucesso", baixa.get_data(as_text=True))
        session = SessionLocal()
        recebimento = session.query(Recebimento).one()
        self.assertEqual(float(recebimento.valor_recebido), 100.0)
        id_recebimento = recebimento.id_recebimento
        session.close()

        estorno = self.client.post(
            f"/financeiro/receber/titulos/{id_recebivel}/baixas/{id_recebimento}/excluir",
            follow_redirects=True,
        )
        self.assertIn("Baixa estornada com sucesso", estorno.get_data(as_text=True))
        session = SessionLocal()
        self.assertTrue(session.get(Recebimento, id_recebimento).deleted)
        self.assertEqual(session.get(Recebivel, id_recebivel).saldo_aberto, 300.0)
        session.close()

        dados["nr_documento"] = "REC-SAIDA"
        dados["id_plano"] = ids["saida"]
        rejeicao = self.client.post("/financeiro/receber/titulos/novo", data=dados)
        self.assertIn("plano financeiro de entrada", rejeicao.get_data(as_text=True))
        session = SessionLocal()
        self.assertEqual(session.query(Recebivel).filter_by(nr_documento="REC-SAIDA").count(), 0)
        session.close()


if __name__ == "__main__":
    unittest.main()
