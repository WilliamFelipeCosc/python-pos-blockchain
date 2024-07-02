from flask import Flask, request, redirect, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dataclasses import dataclass
from datetime import datetime, timedelta
import requests

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

@dataclass
class Cliente(db.Model):
    id: int
    nome: str
    senha: int
    qtdMoeda: int
    is_active: bool  # Nova coluna para soft delete

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(20), unique=False, nullable=False)
    senha = db.Column(db.String(20), unique=False, nullable=False)
    qtdMoeda = db.Column(db.Integer, unique=False, nullable=False)
    is_active = db.Column(db.Boolean, unique=False, nullable=False, default=True)  # Inicialmente ativo

@dataclass
class Seletor(db.Model):
    id: int
    nome: str
    ip: str
    chave: str

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(20), unique=False, nullable=False)
    ip = db.Column(db.String(15), unique=False, nullable=False)
    chave = db.Column(db.String(50), unique=False, nullable=False)

@dataclass
class Transacao(db.Model):
    id: int
    remetente: int
    recebedor: int
    valor: int
    horario: datetime
    status: int

    id = db.Column(db.Integer, primary_key=True)
    remetente = db.Column(db.Integer, unique=False, nullable=False)
    recebedor = db.Column(db.Integer, unique=False, nullable=False)
    valor = db.Column(db.Integer, unique=False, nullable=False)
    horario = db.Column(db.DateTime, unique=False, nullable=False)
    status = db.Column(db.Integer, unique=False, nullable=False)

with app.app_context():
    db.create_all()

@app.route("/")
def index():
    return jsonify(['API sem interface do banco!'])

@app.route('/cliente', methods=['GET'])
def ListarCliente():
    if request.method == 'GET':
        clientes = Cliente.query.filter_by(is_active=True).all()  # Filtra apenas clientes ativos
        return jsonify(clientes)

@app.route('/cliente/<string:nome>/<string:senha>/<int:qtdMoeda>', methods=['POST'])
def InserirCliente(nome, senha, qtdMoeda):
    if request.method == 'POST' and nome != '' and senha != '' and qtdMoeda != '':
        objeto = Cliente(nome=nome, senha=senha, qtdMoeda=qtdMoeda)
        db.session.add(objeto)
        db.session.commit()
        return jsonify(objeto)
    else:
        return jsonify(['Method Not Allowed'])

@app.route('/cliente/<int:id>', methods=['GET'])
def UmCliente(id):
    if request.method == 'GET':
        objeto = Cliente.query.get(id)
        if objeto.is_active:  # Verifica se o cliente está ativo
            return jsonify(objeto)
        else:
            return jsonify(['Cliente não encontrado']), 404
    else:
        return jsonify(['Method Not Allowed'])

@app.route('/cliente/<int:id>/<int:qtdMoedas>', methods=["POST"])
def EditarCliente(id, qtdMoedas):
    if request.method == 'POST':
        try:
            cliente = Cliente.query.filter_by(id=id, is_active=True).first()  # Filtra apenas clientes ativos
            cliente.qtdMoeda = qtdMoedas
            db.session.commit()
            return jsonify(['Alteração feita com sucesso'])
        except Exception as e:
            data = {
                "message": "Atualização não realizada"
            }
            return jsonify(data)
    else:
        return jsonify(['Method Not Allowed'])

@app.route('/cliente/<int:id>', methods=['DELETE'])
def ApagarCliente(id):
    if request.method == 'DELETE':
        try:
            cliente = Cliente.query.filter_by(id=id).first()
            cliente.is_active = False  # Marca o cliente como inativo em vez de deletar
            db.session.commit()
            data = {
                "message": "Cliente marcado como inativo com sucesso"
            }
            return jsonify(data)
        except Exception as e:
            data = {
                "message": "Não foi possível marcar o cliente como inativo"
            }
            return jsonify(data)
    else:
        return jsonify(['Method Not Allowed'])

@app.route('/seletor', methods=['GET'])
def ListarSeletor():
    if request.method == 'GET':
        produtos = Seletor.query.all()
        return jsonify(produtos)

@app.route('/seletor/<string:nome>/<string:ip>/<string:chave>', methods=['POST'])
def InserirSeletor(nome, ip, chave):
    if request.method == 'POST' and nome != '' and ip != '' and chave != '':
        objeto = Seletor(nome=nome, ip=ip, chave=chave)
        db.session.add(objeto)
        db.session.commit()
        return jsonify(objeto)
    else:
        return jsonify(['Method Not Allowed'])

@app.route('/seletor/<int:id>', methods=['GET'])
def UmSeletor(id):
    if request.method == 'GET':
        produto = Seletor.query.get(id)
        return jsonify(produto)
    else:
        return jsonify(['Method Not Allowed'])

@app.route('/seletor/<int:id>/<string:nome>/<string:ip>/<string:chave>', methods=["POST"])
def EditarSeletor(id, nome, ip, chave):
    if request.method == 'POST':
        try:
            validador = Seletor.query.filter_by(id=id).first()
            validador.nome = nome
            validador.ip = ip
            validador.chave = chave
            db.session.commit()
            return jsonify(validador)
        except Exception as e:
            data = {
                "message": "Atualização não realizada"
            }
            return jsonify(data)
    else:
        return jsonify(['Method Not Allowed'])

@app.route('/seletor/<int:id>', methods=['DELETE'])
def ApagarSeletor(id):
    if request.method == 'DELETE':
        objeto = Seletor.query.get(id)
        db.session.delete(objeto)
        db.session.commit()

        data = {
            "message": "Validador Deletado com Sucesso"
        }

        return jsonify(data)
    else:
        return jsonify(['Method Not Allowed'])

@app.route('/hora', methods=['GET'])
def horario():
    if request.method == 'GET':
        objeto = datetime.now()
        return jsonify(objeto)

@app.route('/transacoes', methods=['GET'])
def ListarTransacoes():
    if request.method == 'GET':
        transacoes = Transacao.query.all()
        return jsonify(transacoes)

@app.route('/transacoes/<int:rem>/<int:reb>/<int:valor>', methods=['POST'])
def CriaTransacao(rem, reb, valor):
    if request.method == 'POST':
        remetente = Cliente.query.filter_by(id=rem, is_active=True).first()
        recebedor = Cliente.query.filter_by(id=reb, is_active=True).first()
        if not remetente or not recebedor:
            return jsonify(['Cliente não encontrado']), 404

        # Verificação de saldo
        if remetente.qtdMoeda < valor:
            return jsonify(['Saldo insuficiente']), 400

        # Verificação de horário
        transacoes_remetente = Transacao.query.filter_by(remetente=rem).order_by(Transacao.horario.desc()).first()
        if transacoes_remetente and transacoes_remetente.horario >= datetime.now():
            return jsonify(['Horário de transação inválido']), 400

        # Limite de transações por minuto
        um_minuto_atras = datetime.now() - timedelta(minutes=1)
        transacoes_no_ultimo_minuto = Transacao.query.filter(Transacao.remetente == rem, Transacao.horario > um_minuto_atras).count()
        if transacoes_no_ultimo_minuto > 100:
            return jsonify(['Limite de transações excedido']), 429

        # Criação da transação
        objeto = Transacao(remetente=rem, recebedor=reb, valor=valor, status=0, horario=datetime.now())
        db.session.add(objeto)
        db.session.commit()

        seletores = Seletor.query.all()
        for seletor in seletores:
            # Verificação da chave única do seletor
            if seletor.chave != "chave_unica_recebida_do_validador":  # Substituir pela lógica real
                objeto.status = 2  # Não aprovada (erro)
                db.session.commit()
                return jsonify(['Chave do seletor inválida']), 400

            # Implementar a lógica de chamada à API do seletor
            url = f"http://{seletor.ip}/transacoes/"
            requests.post(url, json=objeto)

        objeto.status = 1  # Concluída com Sucesso
        db.session.commit()
        return jsonify(objeto)
    else:
        return jsonify(['Method Not Allowed'])

@app.route('/transacoes/<int:id>', methods=['GET'])
def UmaTransacao(id):
    if request.method == 'GET':
        objeto = Transacao.query.get(id)
        return jsonify(objeto)
    else:
        return jsonify(['Method Not Allowed'])

@app.route('/transacoes/<int:id>/<int:status>', methods=["POST"])
def EditaTransacao(id, status):
    if request.method == 'POST':
        try:
            objeto = Transacao.query.filter_by(id=id).first()
            objeto.status = status
            db.session.commit()
            return jsonify(objeto)
        except Exception as e:
            data = {
                "message": "Transação não atualizada"
            }
            return jsonify(data)
    else:
        return jsonify(['Method Not Allowed'])

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(host='0.0.0.0',port=5000, debug=True)
