# financeiro/__init__.py
from flask import Blueprint

bp_financeiro = Blueprint("financeiro", __name__)

# Importa as rotas ao carregar o Blueprint
from . import (
    routes_centro_custo,
    routes_contas,
    routes_credor,
    routes_empresa,
    routes_home,
    routes_plano,
    routes_titulos,
)
