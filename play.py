import ollama
import chromadb

client = chromadb.Client()

convo = []

message_history = [
    {'id': 1,
     'prompt': 'What is my name',
     'response': 'Your name Ray Bernard?'},
    {'id': 2,
     'prompt': 'Ray Bernard owns  two cats?',
     'response': 'Lucy and Penny'},
    {'id': 3,
     'prompt': 'Where is Ray Bernard astrological sign?',
     'response': 'Virgo'}
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
    stream = ollama.chat(model='reflection', messages=convo, stream=True)

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
