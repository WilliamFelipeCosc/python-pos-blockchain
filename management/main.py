from uuid import uuid4
from flask import Flask, request, redirect, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dataclasses import dataclass
from datetime import datetime, timedelta
import requests
import random

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

@dataclass
class Client(db.Model):
    id: str
    name: str
    password: str
    balance: float
    is_active: bool  # Nova coluna para soft delete
    bans: int

    id = db.Column(db.String(32), primary_key=True)
    name = db.Column(db.String(20), unique=False, nullable=False)
    password = db.Column(db.String(20), unique=False, nullable=False)
    balance = db.Column(db.Float, unique=False, nullable=False)
    is_active = db.Column(db.Boolean, unique=False, nullable=False, default=True)  # Inicialmente ativo
    bans = db.Column(db.Integer, unique=False, nullable=False, default=0)  # Inicialmente ativo

@dataclass
class Selector(db.Model):
    id: str
    name: str
    ip: str

    id = db.Column(db.String(32), primary_key=True)
    name = db.Column(db.String(20), unique=False, nullable=False)
    ip = db.Column(db.String(15), unique=False, nullable=False)

@dataclass
class Transaction(db.Model):
    id: str
    sender: str
    receiver: str
    value: float
    createdAt: datetime
    status: int

    id = db.Column(db.String(32), primary_key=True)
    sender = db.Column(db.String(32), unique=False, nullable=False)
    receiver = db.Column(db.String(32), unique=False, nullable=False)
    value = db.Column(db.Float, unique=False, nullable=False)
    createdAt = db.Column(db.DateTime, unique=False, nullable=False)
    status = db.Column(db.Integer, unique=False, nullable=False)

with app.app_context():
    db.create_all()

@app.route("/")
def index():
    return jsonify(['API sem interface do banco!'])

@app.route('/client', methods=['GET'])
def ListClients():
    if request.method == 'GET':
        clients = Client.query.filter_by(is_active=True).all()  # Filtra apenas clientes ativos
        return jsonify(clients)

@app.route('/client', methods=['POST'])
def AddClient():
    if request.method != 'POST': 
        return jsonify(['Method Not Allowed'])

    data = request.get_json()
    if not data['name'] or not data['password'] or not data['balance']:
        return jsonify(['Method Not Allowed'])

    # Verify if client exists.
    existing_client = Client.query.filter_by(name=data['name']).first()
    if existing_client:
        return jsonify(['Client already exists']), 409

    client_obj = Client(id=str(uuid4()), name=data['name'], password=data['password'], balance=data['balance'])
    db.session.add(client_obj)

    # Create in table selector if not exists
    selector_obj = Selector(id=str(uuid4()), name=data['name'], ip='127.0.0.1') #IP Exemple.
    db.session.add(selector_obj)

    # Register on Selector Service (Validator)
    try:
        response = requests.post('http://seletor_service/clients', json={'id': client_obj.id, 'name': client_obj.name, 'balance': client_obj.balance})
        if response.status_code != 200:
            return jsonify(['Failed to register with selector service']), 500
    except requests.exceptions.RequestException as e:
        return jsonify([str(e)]), 500


    db.session.commit()
    return jsonify(client_obj)
       

@app.route('/client/<int:id>', methods=['GET'])
def GetClientById(id):
    if request.method != 'GET':
        return jsonify(['Method Not Allowed'])
    
    client_obj = Client.query.get(id)
    if client_obj.is_active:  # Verifica se o cliente está ativo
        return jsonify(client_obj)
    else:
        return jsonify(['Cliente não encontrado']), 404
   
        

@app.route('/client', methods=["PUT"])
def EditClient():
    if request.method != 'PUT':
        return jsonify(['Method Not Allowed'])

    data = request.get_json()
    try:
        client = Client.query.filter_by(id=data['id'], is_active=True).first()  # Filtra apenas clientes ativos
        client.balance = data['balance']
        db.session.commit()

        return jsonify(['Alteração feita com sucesso'])
    except Exception as e:
        data = {
            "message": "Atualização não realizada"
        }
        return jsonify(data)

# TODO: Patch para banir cliente      

@app.route('/client', methods=['DELETE'])
def ApagarCliente():
    if request.method != 'DELETE':
        return jsonify(['Method Not Allowed'])

    data = request.get_json()
    try:
        client = Client.query.filter_by(id=data['id']).first()
        client.is_active = False  # Marca o cliente como inativo em vez de deletar
        db.session.commit()
        data = {
            "message": "Cliente deletado com sucesso"
        }
        return jsonify(data)
    except Exception as e:
        data = {
            "message": "Não foi possível deletar o cliente"
        }
        return jsonify(data)
 
        

@app.route('/selector', methods=['GET'])
def ListSeletors():
    if request.method == 'GET':
        selectors = Selector.query.all()
        return jsonify(selectors)

@app.route('/selector', methods=['POST'])
def AddSelector():
    if request.method != 'POST':
        return jsonify(['Method Not Allowed'])

    data = request.get_json()
    if not data or not data['name'] or not data['ip'] :
        return jsonify(['Missing Parameters'])

    selector = Selector(name=data['name'], ip=data['ip'])
    db.session.add(selector)
    db.session.commit()

    return jsonify(selector)
   
@app.route('/selector', methods=['GET'])
def GetSelectorById(id):
    if request.method == 'GET':
        produto = Selector.query.get(id)
        return jsonify(produto)
    else:
        return jsonify(['Method Not Allowed'])

@app.route('/selector', methods=["PUT"])
def EditSelector():
    if request.method == 'PUT':
        try:
            data = request.get_json()
            validador = Selector.query.filter_by(id=data['id']).first()
            validador.name = data['name']
            validador.ip = data['ip']
            db.session.commit()
            return jsonify(validador)
        except Exception as e:
            data = {
                "message": "Atualização não realizada"
            }
            return jsonify(data)
    else:
        return jsonify(['Method Not Allowed'])

@app.route('/seletor', methods=['DELETE'])
def ApagarSeletor():
    if request.method == 'DELETE':
        data = request.get_json()
        objeto = Selector.query.get(data['id'])
        db.session.delete(objeto)
        db.session.commit()

        data = {
            "message": "Seletor Deletado com Sucesso"
        }

        return jsonify(data)
    else:
        return jsonify(['Method Not Allowed'])

@app.route('/hora', methods=['GET'])
def horario():
    if request.method == 'GET':
        objeto = datetime.now()
        return jsonify(objeto)

@app.route('/transaction', methods=['GET'])
def ListarTransacoes():
    if request.method == 'GET':
        transacoes = Transaction.query.all()
        return jsonify(transacoes)

@app.route('/transaction', methods=['POST'])
def CriaTransacao():
    if request.method == 'POST':
        data = request.get_json()
        remetente = Client.query.filter_by(id=data['sender'], is_active=True).first()
        recebedor = Client.query.filter_by(id=data['receiver'], is_active=True).first()

        if not remetente or not recebedor:
            return jsonify(['Cliente não encontrado']), 404

        # Verificação de saldo
        if remetente.balance < data['value']:
            return jsonify(['Saldo insuficiente']), 400

        # Verificação de horário
        transacoes_remetente = Transaction.query.filter_by(sender=data['sender']).order_by(Transaction.createdAt.desc()).first()
        if transacoes_remetente and transacoes_remetente.horario >= datetime.now():
            return jsonify(['Horário de transação inválido']), 400

        # Limite de transações por minuto
        um_minuto_atras = datetime.now() - timedelta(minutes=1)
        transacoes_no_ultimo_minuto = Transaction.query.filter(Transaction.sender == data['sender'], Transaction.createdAt > um_minuto_atras).count()
        if transacoes_no_ultimo_minuto > 100:
            return jsonify(['Limite de transações excedido']), 429

        # # Criação da transação
        objeto = Transaction(sender=data['sender'], receiver=data['receiver'], value=data['value'], status=0, datetime=datetime.now())
        db.session.add(objeto)
        db.session.commit()

        seletores = Selector.query.all()

        chosen_selector = random.choices(seletores)

        url = f"http://{chosen_selector.ip}/transaction"
        response = requests.post(url, json=objeto)
        # for seletor in seletores:
        #     # Verificação da chave única do seletor
        #     if seletor.chave != "chave_unica_recebida_do_validador":  # Substituir pela lógica real
        #         objeto.status = 2  # Não aprovada (erro)
        #         db.session.commit()
        #         return jsonify(['Chave do seletor inválida']), 400

        #     # Implementar a lógica de chamada à API do seletor
            # url = f"http://{seletor.ip}/transacoes/"
        #     requests.post(url, json=objeto)

        objeto.status = response.json()['status']  # Concluída com Sucesso
        db.session.commit()

        return jsonify(objeto)
    else:
        return jsonify(['Method Not Allowed'])

@app.route('/transaction/<int:id>', methods=['GET'])
def UmaTransacao(id):
    if request.method == 'GET':
        objeto = Transaction.query.get(id)
        return jsonify(objeto)
    else:
        return jsonify(['Method Not Allowed'])

@app.route('/transaction', methods=["PUT"])
def EditaTransacao():
    if request.method == 'PUT':
        try:
            data = request.get_json()
            objeto = Transaction.query.filter_by(id=data['id']).first()
            objeto.status = data['status']
            db.session.commit()
            return jsonify(objeto)
        except Exception as e:
            data = {
                "message": "Transação não atualizada"
            }
            return jsonify(data)
    else:
        return jsonify(['Method Not Allowed'])

# TODO: Patch para atualizar status

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(host='0.0.0.0',port=5000, debug=True)
