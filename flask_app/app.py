from flask import Flask, request, jsonify
import utils
import numpy as np

app = Flask(__name__)

@app.route('/query', methods=['POST'])
def query():
    """
    Handles the POST request to '/query'. Extracts the query from the request,
    processes it through the search, concatenate, and generate functions,
    and returns the generated answer.
    """
    if request.content_type != 'application/json':
        return jsonify({'error': 'Unsupported Media Type. Expected application/json'}), 415
    
    data = request.json
    if not data or 'query' not in data:
        return jsonify({'error': 'No query provided'}), 400

    query = data['query']
    history = data.get("history", [])
    print(f"Received query: {query}")
    print(f"Recevied History: {history}")
    
    print("Step 1: Searching articles")
    query = str(query)
    articles = utils.search_articles(query=query)
    if not articles:
        return jsonify({'error': 'No articles found'}), 404

    print("Step 2: Concatenating content")
    content = utils.concatenate_content(articles=articles)
    if not content:
        return jsonify({'error': 'No content to concatenate'}), 404
    

    print("Step 3: Generating answer")
    response = utils.generate_answer(content=content, query=query, history=history)
    if not response:
        return jsonify({'answer': 'Failed to generate a response'}), 500    

    return jsonify({'answer': response})

@app.route("/embed", methods=['POST'])
def get_embed():
    data = request.json
    data = data['query']
    embedding = utils.get_embeddings(data)
    return jsonify({'embedding':embedding.tolist()})

@app.route("/check", methods=['POST'])
def is_same():
    data = request.json
    query_embed = np.array(data['query'])
    other_embed = np.array(data['embedding'])
    check = utils.is_similar(query_embed, other_embed)
    return jsonify({'similar':check})

if __name__ == '__main__':
    app.run(host='localhost', port=5001)
