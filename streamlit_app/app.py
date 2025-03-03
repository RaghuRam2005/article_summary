import streamlit as st
import requests
import numpy as np

st.title("LLM bases article search")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Load chat history into chat
for message in st.session_state.messages:
    with st.chat_message('user'):
        st.markdown(message['user'])
    with st.chat_message('assistant'):
        st.markdown(message['assistant'])

# Input for user query
query = st.chat_input("what do you want?")

if len(str(query)) > 50:
    st.warning("Query length limit exceeded!")

if query:
    try:
        history = st.session_state.messages[-2:]['history']
    except Exception:
        history = []

    # Make a POST request to the Flask API
    with st.chat_message("user"):
        st.markdown(query)
    
    payload = {
        "query" : query
    }

    embed_url = "http://localhost:5001/embed"
    embeddings = requests.post(embed_url, json=payload)
    embeddings = np.array(embeddings.json()['embedding'])

    is_similar = False
    ans_index = None
    check_url = "http://localhost:5001/check"

    for index in range(len(st.session_state.messages)):
        query_embed = {'embedding':st.session_state.messages[index]['embed'].tolist(), 'query':embeddings.tolist()}
        check = requests.post(check_url, json=query_embed)
        check = check.json()

        if check['similar']:
            is_similar=True
            ans_index = index
            break
        else:
            continue
    
    if is_similar:
        answer = st.session_state.messages[ans_index]['assistant']
    else:
        payload = {
            'query':query,
            'history':history
        }
        flask_url = "http://localhost:5001/query"
        response = requests.post(flask_url, json=payload)
        if response.status_code == 200:
            answer = response.json()['answer']
        else:
            answer = response.json()['answer']
        history = query
        st.session_state.messages.append({
            'user':query,
            'assistant': answer,
            'history' : history,
            'embed':embeddings
        })


    with st.chat_message('assistant'):
        st.markdown(answer)

    
