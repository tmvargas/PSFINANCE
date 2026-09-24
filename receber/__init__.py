from flask import Blueprint

bp_receber = Blueprint("receber", __name__)

from . import routes_titulos
