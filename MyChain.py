import hashlib
import json
from time import time
from uuid import uuid4
from urllib.parse import urlparse
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, request
import requests

# Constructor and decorators with needed functionalities
class BlockChain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()
        self.new_block(previous_hash=1, miner_message='Something with chancelors, banks & bailouts', nonce=1337)

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    # Here I put the desired block contents
    def new_block(self, nonce, miner_message, previous_hash=None,):
        block = {
            'index': len(self.chain)+1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'nonce': nonce,
            'miner_message': miner_message,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        self.current_transactions = []
        self.chain.append(block)
        return block

    @property
    def last_block(self):
        return self.chain[-1]

    #Function for adding new transactions
    def new_transaction(self, sender, recipient, amount, data):
        self.current_transactions.append({
            "sender":sender,
            "recipient":recipient,
            "MYC":amount,
            "input":data
        })
        return int(self.last_block['index'])+1

    def proof_of_work(self, last_nonce):
        nonce = 0
        while self.validate_proof(last_nonce, nonce) is False:
            nonce += 1
        return nonce
    
    def register_node(self, address):
        # add a new node to the list of nodes
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        # determine if a given blockchain is valid and protect against double spending
        last_block = chain[0]
        current_index = 1
            
        while current_index < len(chain):
            block = chain[current_index]
            # check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False
            # check that the proof of work is correct
            if not self.validate_proof(last_block['nonce'], block['nonce']):
                return False
            
            last_block = block
            current_index += 1

            return True

    def resolve_conflicts(self):
        # this is our Consensus Algorithm, it resolves conflicts by replacing
        # our chain with the longest one in the network.

        neighbours = self.nodes
        new_chain = None

        # we are only looking for the chains longer than ours
        max_length = len(self.chain)

        # grab and verify chains from all the nodes in our network
        for node in neighbours:

            # we utilize our own api to construct the list of chains :)
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:

                length = response.json()['length']
                chain = response.json()['chain']
                    
                # check if the chain is longer and whether the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
            
        # replace our chain if we discover a new longer valid chain
        if new_chain:
            self.chain = new_chain
            return True

        return False

    @staticmethod
    def validate_proof(last_nonce, nonce):
        guess = f'{last_nonce}{nonce}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

def mine():
    # Run the proof of work algorithm to calculate the new nonce
    last_block = blockchain.last_block
    last_nonce = last_block['nonce']
    nonce = blockchain.proof_of_work(last_nonce)

    # Implement halving + miner reward
    reward = 100
    block_no = int(blockchain.last_block['index'])+1
    no_halvings=int(block_no/100)
    for x in range(no_halvings):
        reward = reward / 2
    
    blockchain.new_transaction(
        sender=0,
        recipient=node_identifier,
        amount=reward,
        data='mining reward'
    )

    # Create a new block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    miner_message = 'miner_message'
    block = blockchain.new_block(nonce, miner_message, previous_hash)

# Make the mining function run as a background daemon
mining_job = BackgroundScheduler(daemon=True)
mining_job.add_job(mine,'interval',seconds=30)
mining_job.start()

app = Flask(__name__)

# Generate an address for this node and initiate the Blockchain
node_identifier = str(uuid4()).replace('-', '')
blockchain = BlockChain()

# Note: mining functionality is also put outside the Flask API endpoint code to mine one block every 30 secs. 
# I'll this here for the option to mine manually
@app.route('/mine', methods=['GET'])
def mine():

    # Run the proof of work algorithm to calculate the new nonce
    last_block = blockchain.last_block
    last_nonce = last_block['nonce']
    nonce = blockchain.proof_of_work(last_nonce)

    # Implement halving + miner reward
    reward = 100
    block_no = int(blockchain.last_block['index'])+1
    no_halvings=int(block_no/100)
    for x in range(no_halvings):
        reward = reward / 2
    
    blockchain.new_transaction(
        sender=0,
        recipient=node_identifier,
        amount=reward,
        data='mining reward'
    )

    # Create a new block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    miner_message = 'miner_message'
    block = blockchain.new_block(nonce, miner_message, previous_hash)

    response = {
        'message': "Forged new block.",
        'index': block['index'],
        'transactions': block['transactions'],
        'nonce': block['nonce'],
        'miner_message': block['miner_message'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response, 200)

@app.route('/transaction/new', methods=['POST'])
def new_transaction():

    values = request.get_json()
    required = ['sender', 'recipient', 'MYC', 'input']

    if not all(k in values for k in required):
        return 'Missing values.', 400

    # Create a new transaction
    index = blockchain.new_transaction(
        sender = values['sender'],
        recipient = values['recipient'],
        amount = values['MYC'],
        data = values['input']
    )

    response = {
        'message': f'Transaction will be added to the Block {index}',
    }
    return jsonify(response, 200)

# GET current Blockchain content
@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

# Register + run multiple nodes
@app.route('/miner/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    
    # get the list of miner nodes
    nodes = values.get('nodes')
    if nodes is None: 
        return "Error: Please supply list of valid nodes", 400

    # register nodes
    for node in nodes:
        blockchain.register_node(node)
        
    response = {
        'message': 'New nodes have been added.',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 200

# Note: consensus and validation functionality is also put outside the Flask API endpoint 
# code so the chain stays in sync and is validated every 60 seconds. 
# I'll this here for the option to sync manually
@app.route('/miner/nodes/resolve', methods=['POST', 'GET'])
def consensus():
    # Resolves conflicts / sync nodes to reach the consensus
    conflicts = blockchain.resolve_conflicts()
    
    if(conflicts):
        response = {
            'message': 'Our chain was replaced.',
            'new_chain': blockchain.chain,
        }
        with app.app_context():
            return jsonify(response), 200
    
    response = {
        'message': 'Our chain is authoritative.',
        'chain': blockchain.chain,
    }
    with app.app_context():
        return jsonify(response), 200

sync = BackgroundScheduler(daemon=True)
sync.add_job(consensus,'interval',seconds=30)
sync.start()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)