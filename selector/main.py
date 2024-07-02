from flask import Flask, request,  jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dataclasses import dataclass
import random
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///selector.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

print(__name__)

@dataclass
class Validator(db.Model):
  id: str
  balance: float
  unique_key: str
  flags: int
  selected_count: int

  id = db.Column(db.Integer, primary_key=True)
  balance = db.Column(db.Float, nullable=False)
  unique_key = db.Column(db.String(64), nullable=False)
  flags = db.Column(db.Integer, default=0)
  selected_count = db.Column(db.Integer, default=0)

with app.app_context():
  db.create_all()

@app.route('/seletor/register', methods=['POST'])
def register_validator():
  if request.method != 'POST':
    return jsonify(['Method Not Allowed'])
  
  data = request.get_json()
  if not data or not data['id'] or not data['balance'] or not data['unique_key']:
    return jsonify(['Missing arguments'])

  validator = Validator(id=data['id'], balance=data['balance'], unique_key=data['unique_key'])
  db.session.add(validator)
  db.session.commit()

  return jsonify({'message': 'Validator registered successfully.'})


@app.route('/seletor/transaction', methods=['POST'])
def handle_transaction():
    data = request.get_json()
    # TODO: handle transaction logic
    # transaction = Transaction(id=data['id'], sender=data['sender'], receiver=data['receiver'], amount=data['amount'], timestamp=data['timestamp'])
    # transaction_pool.append(transaction)
    # status = manage_consensus(transaction)
    return jsonify({'transaction_id': 123, 'status': 'sim'})

def select_validators(transaction):
    eligible_validators = Validator.query.filter(Validator.flags < 2).all()

    weights = [v.balance for v in eligible_validators]
    # TODO: flags logic
    selected_validators = random.choices(eligible_validators, weights=weights, k=3)
    
    return selected_validators

def manage_consensus(votes, validators):
    # for validator in validators:
    #     vote = validate_transaction(validator, transaction)
    #     votes.append(vote)
    
    # if votes.count(1) > len(validators) / 2:
    #     transaction.status = 1
    # else:
    #     transaction.status = 2
    
    # update_validator_flags(validators, transaction.status)
    return 'sim'

def update_validator_flags(validators, transaction_status):
    for validator in validators:
        if transaction_status == 2:
            validator.flags += 1
        elif transaction_status == 1:
            validator.flags = max(0, validator.flags - 1)
        if validator.flags >= 2:
            db.session.delete(validator)
        db.session.commit()



if __name__ == '__main__':
  with app.app_context():
    db.create_all() 

app.run(host= '0.0.0.0', debug=True)
