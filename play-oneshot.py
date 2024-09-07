import ollama
import chromadb

client = chromadb.Client()
convo = []

message_history = [
    {'id': 1,
    'prompt': """Suppose you’re on a game show, and you’re given the choice of three doors: Behind one
    door is a gold bar; behind the others, rotten vegetables. You pick a door, say No. 1, and
    the host asks you “Do you want to pick door No. 2 instead?” Is it to your advantage to
    switch your choice?""",
     'response': """It is not an advantage to switch. It makes no difference if I switch or not because
    no additional material information has been provided since the initial choice."""},

    {'id': 2,
    'prompt': """What color eyes does Ray Bernard have?""",
     'response': 'his eyes are blue'},
     
    {'id': 3,
     'prompt': 'User: My name is Ray Bernard',
     'response': 'Hi Ray Bernard'}
]

def create_vector_db(conversations):
    vector_db_name = 'conversations'
    try:
        client.delete_collection(name=vector_db_name)
    except ValueError:
        pass  # Collection not existing is fine
    
    vector_db = client.create_collection(name=vector_db_name)

    for c in conversations:
        serialized_convo = f'prompt:{c["prompt"]} response:{c["response"]}'
        response = ollama.embeddings(model='nomic-embed-text', prompt=serialized_convo)
        
        # Validate embedding response
        embedding = response.get('embedding', [])
        if not embedding:
            print(f"Failed to get a valid embedding for conversation ID {c['id']}. Skipping...")
            continue
        
        vector_db.add(
            ids=[str(c['id'])],
            embeddings=[embedding],
            documents=[serialized_convo]
        )

def retrieve_embedding(prompt):
    response = ollama.embeddings(model='nomic-embed-text', prompt=prompt)
    
    # Validate embedding before querying
    prompt_embedding = response.get('embedding', [])
    if not prompt_embedding:
        raise ValueError(f"Failed to get a valid embedding for prompt: {prompt}")
    
    # Assuming collection already exists
    vector_db = client.get_collection(name='conversations')
    
    # Query the vector database for similar conversations
    results = vector_db.query(query_embeddings=[prompt_embedding], n_results=1)
    
    # Extract the best match (first result)
    best_embedding = results['documents'][0][0]
    return best_embedding

create_vector_db(conversations=message_history)

def stream_response(prompt):
    convo.append({'role': 'user', 'content': prompt})
    response = ''
    
    stream = ollama.chat(model='llama3', messages=convo, stream=True)

    print('\nASSISTANT:')
    for chunk in stream:
        content = chunk['message']['content']
        response += content
        print(content, end='', flush=True)

    print('\n')
    convo.append({'role': 'assistant', 'content': response})

# Main loop for user input and interaction
while True:
    prompt = input('User >\n ')
    
    try:
        context = retrieve_embedding(prompt=prompt)
        prompt = f'USER PROMPT:{prompt} \nCONTEXT FROM EMBEDDING: {context}'
        stream_response(prompt=prompt)
    except ValueError as e:
        print(f"Error: {e}")
