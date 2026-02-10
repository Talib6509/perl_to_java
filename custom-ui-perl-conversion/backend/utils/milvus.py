from pymilvus import connections, utility, Collection, CollectionSchema, FieldSchema, DataType
from dotenv import load_dotenv
import os
import requests
import json

load_dotenv()

MILVUS_URI = os.getenv('MILVUS_URI')
print(MILVUS_URI)
HUGGINGFACE_URI = os.getenv('HUGGINGFACE_URI')


def embed(chunk):
    '''
    Embeds a chunk of code in order to perform a similarity search. It does
    this to a deployed huggingface embedding model.
    '''
    body = {'request': chunk}
    response = requests.post(HUGGINGFACE_URI, json=body)

    embedding = response.text
    embedding = json.loads(embedding)

    return embedding


def createCollection(char_limit, collection_name):
    '''
    Creates a milvus collection based on a maximum chunk size and
    collection name. The schema contains id, which is an auto-id,
    auto-indexing primary key that can be ignored. Embeddings, which
    are created with the embed function. Chunk, the code to be stored.
    file_name, which is the name of the file the chunk originated
    from. It also creates two indexes (indexes allow searches to be
    performed on the field) for embeddings and file_name.
    '''
    DIMENSION = 384

    connections.connect(
        alias="default",
        uri=MILVUS_URI,
    )

    if utility.has_collection(f"{collection_name}"):
        utility.drop_collection(f"{collection_name}")

    # Setup collection fields to store text and associated embeddings
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, descrition="Ids", is_primary=True, auto_id=True),
        FieldSchema(name='embeddings', dtype=DataType.FLOAT_VECTOR, description='Embedding vectors', dim=DIMENSION),
        FieldSchema(name="chunk", dtype=DataType.VARCHAR, max_length=char_limit+1500),
        FieldSchema(name="file_name", dtype=DataType.VARCHAR, max_length=30)
    ]

    schema = CollectionSchema(fields=fields, description='Test Embedding',enable_dynamic_field=True)
    collection = Collection(name=f"{collection_name}", schema=schema)

    # Setup index to allow querying with embeddings
    index_params = {
        'metric_type':'L2',
        'index_type':"IVF_FLAT",
        'params':{"nlist":2048}
    }
    collection.create_index(field_name="embeddings", index_params=index_params)
    collection.create_index(field_name="file_name")

    return collection


def embed_and_store_chunks(chunks, char_limit, collection_name, file_name, new_collection=False):
    '''
    Takes a list of chunks and embeds stores the chunks in either a
    new collection or a given existing one.
    '''
    connections.connect(
        alias="default",
        uri=MILVUS_URI,
    )

    # create collection to store chunks
    if new_collection:
        collection = createCollection(char_limit, collection_name)
    else:
        collection = Collection(f"{collection_name}")      
        collection.load()

    # insert chunks and embeddings into VDB
    for chunk in chunks:
        embeddings = embed(chunk)
        collection.insert({
            'embeddings': embeddings,
            'chunk': chunk,
            'file_name': file_name
            })

    collection.flush()

    return collection


def query_database(prompt, collection, search_analysis, limit=3, file_name=""):
    '''
    Takes in a prompt, embeds it and performs a vector similarity search
    in the given collection.
    '''
    search_params = {
        "metric_type": "L2",
        "offset": 0,
        "ignore_growing": False,
        "params": {"nprobe": 10},
    }

    prompt_embedding = embed(prompt)

    if (search_analysis):
        relevant_entries_raw = collection.search(data=[prompt_embedding], 
            anns_field="embeddings",
            param=search_params,
            limit=50,
            expr=f"file_name in {[file_name]}",
            output_fields=["chunk","file_name"],
            consistency_level="Strong",
            )[0]
        relevant_entries = []

        for entry in relevant_entries_raw:
            if prompt in entry.chunk:
                relevant_entries.append(entry)        
    else:
        relevant_entries = collection.search(data=[prompt_embedding], 
            anns_field="embeddings",
            param=search_params,
            limit=limit,
            expr=None, 
            output_fields=["chunk","file_name"],
            consistency_level="Strong",
            )[0]    

    return relevant_entries

def master_setup():
    connections.connect(
        alias="default",
        uri=MILVUS_URI,
    )
    
def query_by_cb_filenames(procedures, copybook_list, limit=5, collection_name='copybooks_2000_chunk'):
    '''
    takes in procedures and a list of file names and does a vector similarity
    search that only looks at entries where the file_name field exists in the
    list of filenames provided.
    '''
    connections.connect(
            alias="default",
            uri=MILVUS_URI,
        )

    collection = Collection(collection_name)
    collection.load()

    search_params = {
        "metric_type": "L2",
        "offset": 0,
        "ignore_growing": False,
        "params": {"nprobe": 10},
    }

    procedures_embedding = embed(procedures)
    
    if (type(copybook_list) is not list):
        new_list = copybook_list.split(',')
        copybook_list = new_list
    
    # finds most relevant entries with filename included in the copybook list
    relevant_entries = collection.search(data=[procedures_embedding], 
        anns_field="embeddings",
        param=search_params,
        limit=limit,
        expr=f"file_name in {copybook_list}",
        output_fields=["chunk", "file_name"],
        consistency_level="Strong",
        )[0]

    return relevant_entries


if __name__ == "__main__":
    from chunking import chunking_call
    
    connections.connect(
        alias="default",
        uri=MILVUS_URI,
    )
    print(utility.list_collections()) # lists existing collections
    base_path = 'PATH TO FOLDER WITH FILES TO EMBED AND STORE'
    files = os.listdir(base_path)
    char_limit = 2000
    collection_name = 'COLLECTION NAME HERE'
    # if collection with same name is found, deletes collection
    collection = createCollection(char_limit, collection_name)

    # Loop through files in directory, embed and store
    for i, file_name in enumerate(files):
        print(f'embedding and storing file {i + 1} of {len(files)}')
        file = open(f'{base_path}/{file_name}', "r")
        file_content = file.read()
        chunks = chunking_call(file_content, char_limit, file_name)
        embed_and_store_chunks(chunks, char_limit, collection_name, file_name, new_collection=False)
        file.close()

    collection = Collection(f"{collection_name}")      
    collection.load()
    # Check number of chunks stored
    print(collection.num_entities)
