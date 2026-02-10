from dotenv import load_dotenv
import os
from . import milvus
from pymilvus import connections, Collection
from .chunking import prettify_file, split_off_procedure, split_cbl
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from pymilvus import connections, utility, Collection, CollectionSchema, FieldSchema, DataType
import requests
import json
from typing import Literal, Optional, Any
import re

load_dotenv()

MILVUS_URI = os.getenv('MILVUS_URI')
HUGGINGFACE_URI = os.getenv('HUGGINGFACE_URI')

def embed(chunk):
    body = {'request': chunk}
    response = requests.post(HUGGINGFACE_URI, json=body)

    embedding = response.text
    embedding = json.loads(embedding)

    return embedding

def chunk_n_store(file_path, char_limit, new_collection=False):
    # Read data from file in as string
    file_name = os.path.basename(file_path)
    with open(file_path) as f:
        data = f.read()

    # Clean and chunk code
    chunks = []

    pretty_data = prettify_file(data)
    procedure_list = split_off_procedure(pretty_data)

    for procedure in procedure_list:
        procedure_chunks = split_cbl(procedure, char_limit)
        chunks.extend(procedure_chunks)

    # embed with huggingface and store in milvus VDB
    collection = milvus.embed_and_store_chunks(chunks, char_limit,file_name, new_collection)

    return collection



def pdf_to_text(path):
    start_page = 1
    loader = PyPDFLoader(path)
    pages = loader.load()
    total_pages = len(pages)

    if total_pages is None:
        total_pages = len(pages)

    text_list = []
    for i in range(start_page-1, total_pages):
        text = pages[i].page_content
        text = text.replace('\n', ' ')
        text = re.sub(r'\s+', ' ', text)
        text_list.append(text)

    return text_list

def text_to_chunks(texts: list[str], 
                    word_length: int = 150, 
                    start_page: int = 1) -> list[list[str]]:
    
    text_toks = [t.split(' ') for t in texts]
    chunks = []

    for idx, words in enumerate(text_toks):
        for i in range(0, len(words), word_length):
            chunk = words[i:i+word_length]
            if (i+word_length) > len(words) and (len(chunk) < word_length) and (
                len(text_toks) != (idx+1)):
                text_toks[idx+1] = chunk + text_toks[idx+1]
                continue
            chunk = ' '.join(chunk).strip() 
            chunk = f'[Page no. {idx+start_page}]' + ' ' + '"' + chunk + '"'
            chunks.append(chunk)
            
    return chunks

def file_chunk_n_store(file_path, char_limit, new_collection=False):

    text_list = pdf_to_text("../../../L&G Source Code/Provided_files/Data_Dictionary.pdf")

    collection = Collection(f"chunk_size_{char_limit}")      
    collection.load()

    chunks = text_to_chunks(text_list)

    for chunk in chunks:
        embeddings = embed(chunk)
        collection.insert({'embeddings': embeddings, 'chunk': chunk, 'file_name': 'Data_Dictionary.pdf'})

    collection.flush()

    return collection

def add_context_to_prompt(prompt, collection_name, limit, context_limit=6000):
    # Connect to milvus VDB to load collection
    connections.connect(
        alias="default",
        uri=MILVUS_URI,
    )

    collection = Collection(collection_name)
    collection.load()

    # query VDB to get most relevant context
    context_chunks = milvus.query_database(prompt, collection, limit)

    # update prompt with additional context
    for chunk in context_chunks:
        if len(prompt) + len(f"\n{chunk.chunk}") > context_limit:
            continue
        else:
            prompt += f"\n{chunk.chunk}"

    return prompt


if __name__ == "__main__":
    # example usage
    char_limit = 1000

    prompt = 'test_prompt'

    updated_prompt = add_context_to_prompt(prompt, f"chunk_size_{char_limit}", 3)
