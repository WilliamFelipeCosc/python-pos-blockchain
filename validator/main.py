from flask import Flask, request, jsonify
import hashlib
import time
import requests
#maior > menor < maior
app = Flask(__name__)

class Transaction:
    def __init__(self, id, sender, receiver, amount, timestamp):
        self.id = id
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.timestamp = timestamp
        self.status = 0

def validate_transaction(transaction):
    if transaction.amount <= 0:
        return False
    #placeholder
    valid_users = ['user1', 'user2', 'user3']
    
    if transaction.sender not in valid_users or transaction.receiver not in valid_users:
        return False
    
    user_balances = {
        'user1': 1000,
        'user2': 500,
        'user3':200
    }#Placeholder for user balance
    
    if user_balances.get(transaction.sender, 0) < transaction.amount:
        return False
    return True
    

def send_result_to_selector(transaction):
    url = 'http://localhost:5001/selector/receive_validation_result'
    data = {
        'transaction_id': transaction.id,
        'status': transaction.status
    }
    # response = requests.post(url, json=data)
    # return response.json()
    print("Deu boa!!! PÈNIS")

@app.route('/validator/receive_transaction', methods=['POST'])
def receive_transaction():
    data = request.get_json()
    transaction = Transaction(id=data['id'], sender=data['sender'], receiver=data['receiver'], amount=data['amount'], timestamp=data['timestamp'])
    
    is_valid = validate_transaction(transaction)
    
    # # if is_valid:
    #     consensus_result = participate_in_consensus(transaction)
    #     transaction.status = 1 if consensus_result else 2
    # else:
    #     transaction.status = 2
    
    send_result_to_selector(transaction)
    
    return jsonify({'transaction_id': transaction.id, 'status': transaction.status})

if __name__ == '__main__':
    app.run('127.0.0.1',port=5000,debug=True)