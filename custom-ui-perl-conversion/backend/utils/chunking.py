import re
import os

def chunking_call(file_content, char_limit, file_name):
    '''
    Takes the contents of a file, then cleans and splits it based on
    a char limit that defines the max amount of characters per chunk.
    '''
    if(file_name.endswith('.cbl')):

        chunks = []

        pretty_data = prettify_file(file_content)
        procedure_list_raw = split_off_procedure(pretty_data)

        procedure_list = []

        for procedure in procedure_list_raw:
            if procedure != "":
                procedure_list.append(procedure)

        # Copybooks won't have a procedure division so trigger the else
        if len(procedure_list) > 1:
            for i, procedure in enumerate(procedure_list):
                    # i >= 1 if post procedure division
                    if i >= 1:
                        procedure_chunks = split_cbl(procedure, char_limit)
                        chunks.extend(procedure_chunks)
                    else:
                        procedure_chunks = split_cbl(procedure, char_limit, post_procedure=False)
                        chunks.extend(procedure_chunks)
        else:
            procedure_chunks = split_cbl(procedure_list[0], char_limit)
            chunks.extend(procedure_chunks)

        # chunks_middle = chunks
        # Combine smaller chunks into larger ones (but keep them under char limit)
        chunks_middle = []
        curr_chunk = ''

        for chunk in chunks:
            if len(curr_chunk + chunk) > char_limit:
                chunks_middle.append(curr_chunk)
                curr_chunk = chunk
            else:
                curr_chunk += chunk + '\n'

        chunks_middle.append(curr_chunk)
        chunks_final = []

        # Just in case chunks haven't been split properly
        for chunk in chunks_middle:
            if len(chunk) > char_limit + 1000:
                chunk_1, chunk_2 = chunk[:len(chunk)//2], chunk[len(chunk)//2:]
                chunks_final.append(chunk_1)
                chunks_final.append(chunk_2)
            else:
                chunks_final.append(chunk)

        # chunks_final = [f"SECTION {i + 1} OF {len(chunks_final)} FOR {file_name}:\n{chunk} " for i, chunk in enumerate(chunks_final)]
    
        return chunks_final

def split_off_procedure(file_content):
    '''
    Splits the file content on the occurance of the phrase 'procedure division'
    '''
    # Splitting the cbl file by procedure division first
    procedure_list = []
    lines = file_content.splitlines()
    curr_str = ""

    for row in lines:
        # some lines contain things like 'SHELL PROCEDURE DIVISION' we want the shell to be in the same chunk
        if bool(re.search('procedure division', row, re.IGNORECASE)):
            procedure_list.append(curr_str)
            curr_str = ""

        curr_str += row + '\n'

    procedure_list.append(curr_str)

    return procedure_list


def prettify_file(file_content):
    '''
    Cleans the file by removing unnecessary/confusing content in the input
    code such as trailing whitespace, empty lines or comments.
    '''
    # Removing fluff
    lines = file_content.splitlines()
    result = ""

    for row in lines:
        row = row.rstrip()

        # Remove commented out lines that only contain PROCEDURE DIVION (but not SHELL PROCEDURE DIVISION etc.)
        if bool(re.search('(?<!\w )procedure division', row, re.IGNORECASE)) and row.lstrip()[0] in ('*', '/'):
            continue

        # Remove comments
        if row.lstrip():
            if row.lstrip()[0] in ('*', '/'):
                continue
                row = row.replace('.', '')

        if bool(re.search('\w', row)):
            result += row + '\n'

    return result


def split_cbl(content, char_limit, post_procedure=True):
    '''
    Main splitting logic, the goal of this is to split into individual
    procedures. If a procedure is too large, it splits it into smaller
    chunks.
    '''
    # splits the cobol
    lines = content.splitlines()
    cobol_chunks = []
    current_chunk = ""
    procedure_bool = True
    spaces = 0

    try:
        for i, line in enumerate(lines):
            line_test = ''

            # Remove chars at the start of the line that aren't actually code
            for j in range(len(line)):
                if line[j] != ' ':
                    line_test += ' '
                else:
                    break
            
            line_test += line[j:]

            # Checking spacing to deduce whether a period is denoting a procedure
            if not procedure_bool:
                space_split_line = line.split(" ")
                
                for i, character in enumerate(space_split_line):
                    if character != "":
                        if i + 1 <= spaces:
                            procedure_bool = True
                            spaces = 0
                        break

            # If part of initialize call, periods are not procedures
            if "INITIALIZE" in line:
                procedure_bool = False
                spaces = len(line.split('INITIALIZE')[0]) + 11

            # If part of Using call, periods are not procedures
            if "USING" in line:
                procedure_bool = False
                spaces = len(line.split('USING')[0]) + 6

            if " EXIT." in line or "EJECT" in line or "END-EXEC." in line or 'END-IF.' in line:
                current_chunk += line + '\n'

                if i + 1 != len(lines):
                    if " EXIT." in line or "EJECT" or "END-EXEC" in lines[i + 1]:
                        continue
    
                if len(current_chunk) > char_limit:
                    # if more then char limit, split to smaller chunks
                    smaller_chunks=split_smaller(current_chunk, char_limit)
                    cobol_chunks.extend(smaller_chunks)
                    current_chunk = ""
                else:
                    cobol_chunks.append(current_chunk)
                    current_chunk = ""
            elif line_test.strip()[-1] == '.' and len([i for i in line_test.split(" ") if i != ""]) == 1 and procedure_bool and not len(line_test.strip()) == 1 and post_procedure:
                if len(current_chunk) > char_limit:
                    smaller_chunks = split_smaller(current_chunk, char_limit)
                    cobol_chunks.extend(smaller_chunks)
                else:
                    cobol_chunks.append(current_chunk)

                current_chunk = line + '\n'
            else:
                current_chunk += line + '\n'

        if current_chunk:
            if len(current_chunk) > char_limit:
                smaller_chunks = split_smaller(current_chunk, char_limit)
                cobol_chunks.extend(smaller_chunks)
            else:
                cobol_chunks.append(current_chunk)  # Append the last chunk if any

        # cobol_chunks = [f"SPLIT {index + 1} OF {len(cobol_chunks)}\n{block} " for index, block in enumerate(cobol_chunks)]
    except Exception as e:
        print(f"Error in split_cbl_code: {e}")

    return cobol_chunks


def split_smaller(large_chunk, char_limit):
    '''
    If a chunk is over the char_limit, it is split into smaller chunks
    based on some additional logic.
    '''
    result_chunks = []
    current_chunk = ""

    # Split the large chunk at a period
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', large_chunk)

    for sentence in sentences:
        if len(current_chunk) + len(sentence) < char_limit:
            current_chunk += sentence + '\n'
        else:
            # If the chunk still exceeds char limit, split before else/ELSE
            if 'else' in sentence.lower():
                chunks = re.split('else', sentence, flags=re.IGNORECASE)
                
                for i, chunk in enumerate(chunks):
                    if i > 0:
                        chunk = 'ELSE' + chunk

                    if len(current_chunk) + len(chunk) < char_limit:
                        current_chunk += chunk
                    else:
                        result_chunks.append(current_chunk)
                        current_chunk = chunk
                    
                result_chunks.append(current_chunk)
                current_chunk = ""
            else:
                result_chunks.append(current_chunk)
                current_chunk = sentence

    if current_chunk:
        result_chunks.append(current_chunk)

    return result_chunks


def get_copybooks(content):
    '''
    Finds all the copybooks in some file-content based on the include
    statement.
    '''
    lines = content.splitlines()
    copybooks = []

    for row in lines:
        row = row.strip()

        row_split = row.split('*')

        if len(row_split) > 1:
            row = row_split[0]

        if bool(re.search('include\s', row, re.IGNORECASE)):
            copybook = re.split("INCLUDE ", row, flags=re.IGNORECASE)[1]
            copybooks.append(copybook)

    return copybooks


def get_procedures(content):
    '''
    Finds all the procedures called in some file-content based on the perform
    statement.
    '''
    lines = content.splitlines()
    procedures = []

    for row in lines:
        row = row.strip()

        if row:
            if row[0] in ('*', '/'):
                continue

        if bool(re.search('perform\s', row, re.IGNORECASE)):
            procedure = re.split("(?<!end-)perform ", row, flags=re.IGNORECASE)[-1]
            procedures.append(procedure)

    return procedures

def get_sql_copybooks(copybooks):
    '''
    Takes a list of copybooks and returns which ones are used for sql
    calls based on client specific naming conventions.
    '''
    sql_copybooks = []
    
    for copybook in copybooks:
        if copybook[-4:] == 'QQ01' or copybook[-3:] == 'QQ1' or copybook[-4:] == 'QQ02':
            sql_copybooks.append(f'{copybook}.copy')

    return sql_copybooks


if __name__ == "__main__":
    file_paths = []
    base_path = ''
    files = os.listdir(base_path)
    char_limit = 2000

    for i, file_name in enumerate(files):
        print(f'embedding and storing file {i + 1} of {len(files)}')
        file = open(f'{base_path}/{file_name}', "r")
        file_content = file.read()
        file.close()

        f = open(f"", "w")

        chunks = chunking_call(file_content, char_limit, file_name)

        # print(f'{file_name}:')

        for j, chunk in enumerate(chunks):
            f.write(chunk + '\n')

        f.close()
