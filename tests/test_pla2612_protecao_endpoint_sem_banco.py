import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ProtecaoExclusaoBaixaSemBancoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = (ROOT / "financeiro" / "routes_titulos.py").read_text(encoding="utf-8")
        module = ast.parse(source)
        cls.funcao = next(
            node
            for node in module.body
            if isinstance(node, ast.FunctionDef) and node.name == "excluir_baixa"
        )
        cls.codigo = ast.unparse(cls.funcao)

    def test_consulta_exige_baixa_titulo_e_registro_ativo(self):
        self.assertIn("Baixa.id_baixa == id_baixa", self.codigo)
        self.assertIn("Baixa.id_titulo == id_titulo", self.codigo)
        self.assertIn("Baixa.deleted.is_(False)", self.codigo)

    def test_requisicao_manipulada_sai_antes_de_qualquer_commit(self):
        guarda_inexistente = next(
            node
            for node in self.funcao.body
            if isinstance(node, ast.If)
            and isinstance(node.test, ast.UnaryOp)
            and isinstance(node.test.op, ast.Not)
        )
        self.assertTrue(any(isinstance(node, ast.Return) for node in guarda_inexistente.body))
        self.assertFalse(
            any(
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "commit"
                for node in ast.walk(guarda_inexistente)
            )
        )

    def test_baixa_conciliada_sai_antes_da_exclusao_logica(self):
        guarda_conciliada = next(
            node
            for node in self.funcao.body
            if isinstance(node, ast.If) and "conciliado" in ast.unparse(node.test)
        )
        indice_guarda = self.funcao.body.index(guarda_conciliada)
        indice_exclusao = next(
            i
            for i, node in enumerate(self.funcao.body)
            if isinstance(node, ast.Assign)
            and any(ast.unparse(alvo) == "bx.deleted" for alvo in node.targets)
        )
        self.assertLess(indice_guarda, indice_exclusao)
        self.assertTrue(any(isinstance(node, ast.Return) for node in guarda_conciliada.body))

    def test_exclusao_e_logica_e_possui_um_unico_commit(self):
        self.assertIn("bx.deleted = True", self.codigo)
        commits = [
            node
            for node in ast.walk(self.funcao)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "commit"
        ]
        self.assertEqual(len(commits), 1)

    def test_consumidores_de_saldo_ignoram_baixa_excluida(self):
        arquivos_funcoes = {
            "financeiro/routes_titulos.py": {
                "_baixas_periodo_por_parcela",
                "_saldos_titulos_ativos",
                "_titulo_saldo_aberto",
                "_saldo_parcela",
            },
            "financeiro/routes_contas.py": {
                "analise_resultados",
                "extrato_conta",
            },
        }

        for caminho, nomes in arquivos_funcoes.items():
            module = ast.parse((ROOT / caminho).read_text(encoding="utf-8"))
            funcoes = {
                node.name: ast.unparse(node)
                for node in module.body
                if isinstance(node, ast.FunctionDef) and node.name in nomes
            }
            self.assertEqual(set(funcoes), nomes, caminho)
            for nome, codigo in funcoes.items():
                with self.subTest(funcao=nome):
                    self.assertIn("Baixa.deleted.is_(False)", codigo)


if __name__ == "__main__":
    unittest.main()
