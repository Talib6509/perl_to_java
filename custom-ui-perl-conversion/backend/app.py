import re
from flask import Flask, request, Response
from flask_cors import CORS
from utils.watsonx import watsonx_call, summarise_file, watsonx_get_db_tables
from utils.chunking import chunking_call, get_copybooks
from utils.perl_chunking import chunk_perl_code, remove_extra_comments
from utils.rag import add_context_to_prompt
from utils.milvus import embed_and_store_chunks
import json
import ast

app = Flask(__name__)
CORS(app)

# check the status of the API
@app.route('/health', methods=['GET', 'POST'])
def health():
    return('API is up and running')

# get explaination of the code using watsonx
@app.route('/explain', methods=['POST'])
def explain():
    data = request.data.decode('utf-8')
    data_decode = ast.literal_eval(data)
    action = request.headers['analysis-type']

    if action == 'convert_full' or action == 'explain_full':
        chunked_perl = remove_extra_comments(data_decode["data"])
    else:
        chunked_perl = data_decode["data"]

    print('Chunked Perl Fetched: ', chunked_perl)
    print('Action: ', action)

    result = watsonx_call(chunked_perl, action)
    model = result['model']
    prompt = result['prompt']
    def stream_response():
        text_stream = model.generate_text_stream(prompt)
        for chunk in text_stream:
            yield chunk

    return Response(stream_response(), content_type="text/event-stream")

# get explanation of a file using spr to condense input
@app.route('/summarise', methods=['POST'])
def summarise_file():
    request_type = request.headers['request-type']

    try:
        file = request.files['file'].read()
        file_content = str(file, encoding="utf-8")
    except KeyError:
        print('Must be file upload')

    char_limit = int(request.headers['char-limit'])

    response = summarise_file(file_content, char_limit)

    return(response)

# call RAG Service
@app.route('/add_context_to_prompt', methods=['POST'])
def context_prompt():
    prompt = request.args.get("prompt")
    collection_name = request.args.get("collection-name")
    limit = request.args.get("limit")
    response = add_context_to_prompt(prompt, collection_name, limit, context_limit=6000)
    return(response)


@app.route('/chunk', methods=['POST'])
def chunk_and_store():
    request_type = request.headers['request-type']
    store_chunks = request.headers['store-chunks']
    new_collection = request.headers['new-collection']
    file_name = request.headers['file-name']
    copybooks=[]
    

    if new_collection == 'true':
        new_collection = True
    else:
        new_collection = False

    if request_type == 'upload':
        file = request.files['file'].read()
        try:
             file_content = str(file, encoding="utf-8")
        except UnicodeDecodeError:
             file_content = file.decode('ISO-8859-1')
             
    else:
        file_content = request.args.get("file-content")

    char_limit = int(request.headers['char-limit'])

    print(file_name)   
    print("--------------------------------")
    print(request.headers['Access-Control-Allow-Origin'])   

    if(file_name.endswith('.cbl')):
            chunks = chunking_call(file_content, char_limit, file_name)
            copybooks = get_copybooks(file_content)
    elif(file_name.endswith('.pl')):
            chunks = chunk_perl_code(file_content, char_limit, file_name)
            copybooks = []

    for i, copybook in enumerate(copybooks):
            copybooks[i] = copybook + '.copy'

    if store_chunks == 'true':
        collection_name = request.headers['collection-name']
        collection = embed_and_store_chunks(chunks, char_limit, collection_name, file.filename, new_collection)
        return({"chunks": chunks, "collection": collection, "copybooks": copybooks})

    return({"chunks": chunks, "copybooks": copybooks})

if __name__ == "__main__":
    app.run('0.0.0.0', port=5000)
