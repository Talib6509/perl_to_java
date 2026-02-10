from ibm_watsonx_ai.foundation_models import Model
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams
from dotenv import load_dotenv
import os
from .milvus import query_database, query_by_cb_filenames
from pymilvus import connections, Collection
from .prompts import generate_prompt
from .chunking import chunking_call, get_copybooks, get_procedures, get_sql_copybooks

load_dotenv()

# MILVUS_URI = os.getenv('MILVUS_URI')
# HUGGINGFACE_URI = os.getenv('HUGGINGFACE_URI')

def watsonx_call(chunked_perl, action):
    '''
    The main logic that performs inference with a generated prompt for an input
    chunk of perl code. The prompt varies based on the action from frontend, either conversion or explain.
    '''
    # attempt project id fetch from .env
    try:
        WATSONX_PROJECT_ID = os.getenv('WATSONX_PROJECT_ID')
        print(WATSONX_PROJECT_ID)
    except KeyError:
        print("Error Fetching PROJECT ID from .env")

    # attempt api key fetch from .env
    try:
        WATSONX_API_KEY = os.getenv('WATSONX_API_KEY')
    except KeyError:
        print("Error Fetching API key from .env")

    generate_params = {
        GenParams.MAX_NEW_TOKENS: 16384,
        GenParams.DECODING_METHOD:"greedy",
        GenParams.REPETITION_PENALTY: 1,

    }

    prompt = generate_prompt(chunked_perl, action)

    model = Model(
        model_id = 'mistralai/mistral-large',
        params = generate_params,
        credentials={
            "apikey": WATSONX_API_KEY,
            "url": "https://us-south.ml.cloud.ibm.com/"
        },
        project_id=WATSONX_PROJECT_ID
        )
    
    gen_parms_override = None
    
    # generated_response = model.generate(prompt, gen_parms_override)
    # return(generated_response)
    return {"model": model, "prompt": prompt}



# def watsonx_call(chunked_perl, action):
#     '''
#     The main logic that performs inference with a generated prompt for an input
#     chunk of cobol code. The prompt varies based on the action from frontend, either conversion or explain.
#     '''
#     # attempt project id fetch from .env
#     try:
#         WATSONX_PROJECT_ID = os.getenv('WATSONX_PROJECT_ID')
#         print(WATSONX_PROJECT_ID)
#     except KeyError:
#         print("Error Fetching PROJECT ID from .env")

#     # attempt api key fetch from .env
#     try:
#         WATSONX_API_KEY = os.getenv('WATSONX_API_KEY')
#     except KeyError:
#         print("Error Fetching API key from .env")

#     generate_params = {
#         GenParams.MAX_NEW_TOKENS: 1000,
#         # GenParams.MIN_NEW_TOKENS: 100,
#         # GenParams.RANDOM_SEED: 42 

#     }
    
#     connections.connect(
#         alias="default",
#         uri=MILVUS_URI,
#     )
    
#     # query code embedding on Milvus
#     code_collection_name = "chunk_size_2000_v2"
#     limit = 2

#     collection = Collection(code_collection_name)
#     collection.load()
#     code_context_chunk = []

#     if action == "search":

#         # query code embedding on Milvus
#         code_collection_name = "chunk_size_1500"
#         limit = 2

#         collection = Collection(code_collection_name)
#         collection.load()

#         # query VDB to get most relevant context
#          # query code embedding on Milvus
#         code_collection_name = "chunk_size_1500"

#         collection = Collection(code_collection_name)
#         collection.load()

#         code_context_chunks = query_database(custom_variable, collection, True, limit, file_name)
#     elif len(copybooks) > 0:
#         limit = 3
#         code_collection_name = "modular_copybooks_2000_chunk_v2"
#         code_context_chunks = query_by_cb_filenames(cobol_code, copybooks, limit=limit, collection_name=code_collection_name)
#     else:
#         code_context_chunks = query_database(cobol_code, collection, False, limit)

#     for chunk in code_context_chunks:
#         code_context_chunk.append(chunk.chunk)

#     code_context_chunk = '\n'.join(code_context_chunk)

#     # query file embedding on Milvus
#     file_collection_name = "chunk_size_1501"
#     limit = 1

#     collection = Collection(file_collection_name)
#     collection.load()

#     file_context_chunk = []

#     # query VDB to get most relevant context
#     file_context_chunks = query_database(cobol_code, collection, False, limit)
#     for chunk in file_context_chunks:
#         file_context_chunk.append(chunk.chunk)

#     file_context_chunk = '\n'.join(file_context_chunk)

#     print("RAG CODE CON: ", code_context_chunk)
#     print("RAG FILE CON: ", file_context_chunk)

#     prompt = generate_prompt(cobol_code, analysis_type, code_context_chunk, file_context_chunk, custom_question, custom_variable)

#     model = Model(
#         model_id = 'meta-llama/llama-2-70b-chat',
#         params = generate_params,
#         credentials={
#             "apikey": WATSONX_API_KEY,
#             "url": "https://eu-de.ml.cloud.ibm.com/"
#         },
#         project_id=WATSONX_PROJECT_ID
#         )
    
#     gen_parms_override = None
    
#     generated_response = model.generate(prompt, gen_parms_override)
#     return(generated_response)


def watsonx_combine_summary(summaries):
    '''
    A watsonx call that is meant to summarise a list of summaries.
    '''
    try:
        WATSONX_PROJECT_ID = os.getenv('WATSONX_PROJECT_ID')
    except KeyError:
        print("Error Fetching PROJECT ID from .env")

    # attempt api key fetch from .env
    try:
        WATSONX_API_KEY = os.getenv('WATSONX_API_KEY')
    except KeyError:
        print("Error Fetching API key from .env")

    generate_params = {
        GenParams.MAX_NEW_TOKENS: 3000,
    }

    prompt = (f"""
<SYS>[INST] Given a set of explanations of different sections of a COBOL file, connect and fully articulate these sections in a single, unified summary. Talk through the overall logic, and use your ability to perform inference and reasoning to fully elucidate this concept. Your output should be in the form of a single unified description of the overall file.
<</SYS>>
Summaries:
{summaries}
[/INST]""")

    model = Model(
        model_id = 'meta-llama/llama-2-70b-chat',
        params = generate_params,
        credentials={
            "apikey": WATSONX_API_KEY,
            "url": "https://us-south.ml.cloud.ibm.com/"
        },
        project_id=WATSONX_PROJECT_ID
        )
    
    gen_parms_override = None

    generated_response = model.generate(prompt, gen_parms_override)

    return(generated_response)


# Gets db tables and sql calls for file with context from file's procedures defined in its sql copybooks
def watsonx_get_db_tables(file_content):
    copybooks = get_copybooks(file_content)
    procedures = get_procedures(file_content)
    sql_copybooks = get_sql_copybooks(copybooks)
    joined_procedures = ', '.join(procedures)
    relevant_entries = query_by_cb_filenames(joined_procedures, sql_copybooks)

    context = ''

    for i, entry in enumerate(relevant_entries):
        context += f"\n*CHUNK {i + 1} of {len(relevant_entries)}\n{entry.chunk}"

    try:
        WATSONX_PROJECT_ID = os.getenv('WATSONX_PROJECT_ID')
    except KeyError:
        print("Error Fetching PROJECT ID from .env")

    try:
        WATSONX_API_KEY = os.getenv('WATSONX_API_KEY')
    except KeyError:
        print("Error Fetching API key from .env")

    generate_params = {
        GenParams.MAX_NEW_TOKENS: 3000
    }

    found_procedures = []

    for procedure in procedures:
        if procedure in context:
            found_procedures.append(procedure)

    prompt = (f"""
    <SYS>[INST]
    Given the following COBOL code list the db2 tables in the SQL queries that occur in this list of procedures: {found_procedures}. First list the tables and describe their procedure, then provide the SQL queries and explain what they do.
    <</SYS>>
    {context}
    [/INST]""")

    model = Model(
        model_id = 'meta-llama/llama-2-70b-chat',
        params = generate_params,
        credentials={
            "apikey": WATSONX_API_KEY,
            "url": "https://us-south.ml.cloud.ibm.com/"
        },
        project_id=WATSONX_PROJECT_ID
        )
    gen_parms_override = None

    generated_response = model.generate(prompt, gen_parms_override)

    return generated_response


def summarise_file(file_content, char_limit, file_name):
    '''
    Takes file_content for an entire cobol file and chunks it. It then
    attempts to summarise the entire file by running explain calls for
    each chunk and feeding the output of those explain calls back into
    the LLM.
    '''
    chunks = chunking_call(file_content, char_limit, file_name)
    num_chunks_original = len(chunks)
    num_chunks = num_chunks_original
    reset = True
    prompt = ""
    loop_back_num = 0

    while reset:
        for i in range(loop_back_num, len(chunks)):
            print(f'Processing part {i + 1} of {num_chunks_original}...')
            prompt += f"\nSection {i + 1 - loop_back_num} of {num_chunks}\n{watsonx_call(chunks[i], analysis_type='explain')['results'][0]['generated_text']}"

            # If appended summary is approaching context limit, break for loop
            if len(prompt) > 6000 and i + 1 != len(chunks):
                loop_back_num = i + 1
                num_chunks = num_chunks_original - (i + 1)
                print('loop back triggered at chunk: ', loop_back_num)
                break

        # If for loop is broken, resummarise
        if len(prompt) > 6000 and i + 1 != len(chunks):
            prompt = f"\nSection 1 of {num_chunks}\n{watsonx_combine_summary(prompt)['results'][0]['generated_text']}"
            continue

        reset = False

    response = watsonx_combine_summary(prompt)['results'][0]['generated_text']


    return response

# if __name__ == "__main__":
#     file_paths = ['/Users/brendan/Desktop/Project Code/lag-cobol-assistant/L&G Source Code/Modules/LBXB01.cbl']
#     char_limit = 2000

#     for file_path in file_paths:
#         file = open(file_path, "r")
#         file_content = file.read()
#         file.close()
#         copybooks = get_copybooks(file_content)

#         for i, copybook in enumerate(copybooks):
#             copybooks[i] = copybooks[i] + '.copy'

#         f = open(f"{os.path.basename(file_path)}_explain.txt", "w")

#         chunks = chunking_call(file_content, char_limit, file_name=os.path.basename(file_path))
#         # chunks = [chunks[11]]
#         # response = watsonx_get_db_tables(file_content)['results'][0]['generated_text']
#         # response = summarise_file(file_content, char_limit, os.path.basename(file_path))
#         # f.write(response)
#         for chunk in chunks:
#             if chunk == "":
#                 continue
#             response = watsonx_call(chunk, analysis_type='explain', copybooks=copybooks)
#             f.write('CHUNK:\n')
#             f.write(chunk)
#             f.write(f'\nRESPONSE:\n\n')
#             f.write(response['results'][0]['generated_text'])
#             f.write('\n\n')

#         f.close()
