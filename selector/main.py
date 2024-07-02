from flask import Flask, request,  jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dataclasses import dataclass
import random
import hashlib
import string
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///selector.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

@dataclass
class Validator(db.Model):
  id: str
  balance: float
  unique_key: str
  flags: int
  selected_count: int
  min_stake: float
  in_hold: bool
  hold_count: int
  consecutive_transactions: int
  coherent_transactions: int

  id = db.Column(db.Integer, primary_key=True)
  balance = db.Column(db.Float, nullable=False)
  unique_key = db.Column(db.String(64), nullable=False)
  flags = db.Column(db.Integer, default=0)
  selected_count = db.Column(db.Integer, default=0)
  min_stake = db.Column(db.Float, nullable=False, default=50)
  in_hold = db.Column(db.Boolean, nullable=False, default=False)
  hold_count= db.Column(db.Integer, nullable=False, default=0)
  consecutive_transactions = db.Column(db.Integer, nullable=False, default=0)
  coherent_transactions = db.Column(db.Integer, nullable=False, default=0)


with app.app_context():
  db.create_all()

def get_random_string(length):
    pool = string.ascii_letters + string.digits
    return ''.join(random.choice(pool) for i in range(length))

@app.route('/seletor/register', methods=['POST'])
def register_validator():
  if request.method != 'POST':
    return jsonify(['Method Not Allowed'])
  
  data = request.get_json()
  if not data or not data['id'] or not data['balance']:
    return jsonify(['Missing arguments'])
  
  random_string = get_random_string(64)
  unique_hash = hashlib.sha256(random_string)

  validator = Validator(id=data['id'], balance=data['balance'], unique_key=unique_hash.hexdigest())
  db.session.add(validator)
  db.session.commit()

  return jsonify({'message': 'Validator registered successfully.'})


@app.route('/seletor/transaction', methods=['POST'])
def handle_transaction():
    if request.method != 'POST':
       return jsonify({'message': 'Method Not Allowed'})
    
    data = request.get_json()
    chosen_validators = select_validators()

    if(len(chosen_validators) < 3):
      return jsonify({'transaction_id': data['id'], 'status': 0, 'message': "Não há validadores suficientes para concluir essa transação"}), 

    transaction_data = {} # TODO: use real data
    results = []

    for validator in chosen_validators:
      try:
        url: f'http://localhost:5002/{validator.id}/receive_transaction'
        data = {
          'data': transaction_data,
          'validator_id': validator.id,
          'validator_key': validator.unique_key
        }
        response = requests.post(url, json=data)

        if response.status_code == 200:
          results.append(response.json())
        else:
          print(f"Erro na comunicação com validadores: {validator.name} - {response.status_code}")
      except requests.exceptions.RequestException as e:
        print(f"Falha ao conectar ao validador {validator.name}: {e}")

    consensus = manage_consensus(results)
    update_validator_flags(results, consensus)

    return jsonify({'transaction_id': 123, 'status': consensus})

def select_validators():
    eligible_validators = Validator.query.filter(Validator.in_hold == False).all()

    total_stake = sum(v.balance for v in eligible_validators)
    max_weight = total_stake * 0.2
    weights = []

    # TODO: limite de transações por minuto e retirada de flags

    for validator in eligible_validators:
      weight = validator.balance

      if validator.flags == 1:
        weight *= 0.50
      elif validator.flags == 2:
        weight *= 0.25
      
      final_weight = min(weight, max_weight)
      weights.append(final_weight)

    # TODO: add option to more validators
    selected_validators = random.choices(eligible_validators, weights=weights, k=3)
    
    return selected_validators

def manage_consensus(votes):
    # for validator in validators:
    #     vote = validate_transaction(validator, transaction)
    #     votes.append(vote)
    status = 0
    if votes.count(1) > len(votes) / 2:
      status = 1
    else:
      status = 2
  
    return status

def update_validator_flags(votes, transaction_status):
  # validators_ids = [votes.validator_id for i in votes]
  # selected_validators = Validator.query.filter(Validator.id in validators_ids).all()

  correct_votes = []
  wrong_votes = []
  for vote in votes:
    if vote.status == transaction_status:
      correct_votes.append(vote.validator_id)
    else:
      wrong_votes.append(vote.validator_id)
  
  flagged_validators = Validator.query.filter(Validator.id in wrong_votes).all()
  correct_validators = Validator.query.filter(Validator.id in correct_votes).all()

  for validator in flagged_validators:
    validator.flags += 1
    validator.coherent_transactions = 0
    validator.consecutive_transactions += 1

  #TODO: logica de banir validador
  
  for validator in correct_validators:
    validator.coherent_transactions += 1
    validator.consecutive_transactions += 1

    if(validator.coherent_transactions > 10000):
      if(validator.flags > 0):
        validator.flags -= 1 
   
  db.session.commit()


if __name__ == '__main__':
  with app.app_context():
    db.create_all() 

app.run(host= '0.0.0.0', debug=True)
