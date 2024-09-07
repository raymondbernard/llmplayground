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
     'response': 'his eyes are bluer'},
     
    {'id': 3,
     'prompt': 'User: What is my name',
     'response': 'Ray Bernard'}
]

def create_vector_db(conversations):
    vector_db_name = 'conversations'
    try:
        client.delete_collection(name=vector_db_name)
    except ValueError as e:
        pass  # Handle collection not existing
    
    # Create or re-create the vector database collection
    vector_db = client.create_collection(name=vector_db_name)

    for c in conversations:
        serialized_convo = f'prompt:{c["prompt"]} response:{c["response"]}'
        response = ollama.embeddings(model='nomic-embed-text', prompt=serialized_convo)
        embedding = response['embedding']
        # Use 'embeddings' (plural) instead of 'embedding'
        vector_db.add(
            ids=[str(c['id'])],
            embeddings=[embedding],  # Corrected to 'embeddings'
            documents=[serialized_convo]
        )

def retrieve_embedding(prompt):
    response = ollama.embeddings(model='nomic-embed-text', prompt=prompt)
    prompt_embedding = response['embedding']
    
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
    
    # Streaming response from the model
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
    
    # Retrieve the best context based on the embedding
    context = retrieve_embedding(prompt=prompt)
    
    # Format the prompt with the retrieved context
    prompt = f'USER PROMPT:{prompt} \nCONTEXT FROM EMBEDDING: {context}'
    
    # Stream the assistant's response
    stream_response(prompt=prompt)
