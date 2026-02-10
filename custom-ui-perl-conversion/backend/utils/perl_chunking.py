import re
import os

def chunk_perl_code(perl_code,char_limit, file_name):
    chunks = []
    current_chunk = []
    bracket_stack = []
    sub_chunks=[]
    lines = perl_code.splitlines()

    for line in lines:
        stripped_line = line.strip()

        if stripped_line.startswith('#'):

            continue

        current_chunk.append(line)

        # Track brackets
        for char in stripped_line:
            if char == '{':
                bracket_stack.append('{')
            elif char == '}':
                if bracket_stack:
                    bracket_stack.pop()

        # Check for semicolon or the closing bracket of a complete block followed by a comment
        if (stripped_line.endswith(';') and not bracket_stack) or (stripped_line.endswith('}') and not bracket_stack) or re.search(r'[;}] *#', stripped_line):
            chunks.append('\n'.join(current_chunk).strip())
            current_chunk = []

    # Add any remaining code as the last chunk
    if current_chunk:
        chunks.append('\n'.join(current_chunk).strip())
    
    

    for i in chunks:
        #print(i)
        #print("--------------------------------------------------")
        pattern = re.compile(r'^sub\s+\w+\s*(\([^\)]*\))?\s*\{')
        if (pattern.match(i)):
            sub_chunks.append(i)




    variable_pattern = re.compile(r'\$(\w+)')
    final_list = []
    l3 = [item for item in chunks if item not in sub_chunks]
    #print(len(chunks))
    
    for chunk in sub_chunks:
        s=''
        variables = set()
        lines = chunk.splitlines()

        for line in lines:
            line = line.strip()
            # Extract variables
            for var in variable_pattern.findall(line):
                  
                variables.add(var)
        #print(variables)
        #print("------------------------------------------------")
            
            
        for j in l3:
            count=0
            for i in variables:
                if(re.search(r'\$'+i, j)):
                    count+=1
            if(count>0):
                s+=j+'\n'
        if(len(s+'\n'+chunk)<char_limit):
            final_list.append(s+'\n'+chunk)


    
    return final_list

def remove_extra_comments(perl_code):
    current_chunk = []
    result = ""
    count = 0
    lines = perl_code.splitlines()

    for line in lines:
        stripped_line = line.strip()

        if stripped_line.startswith('#') and not stripped_line.startswith('#!'):

            continue

        current_chunk.append(line)
    
    for j, chunk in enumerate(current_chunk):
        if result == "":
            result = chunk + "\n"
        else:
            result = result + chunk + "\n"
    return result

    
if __name__ == "__main__":
    file_paths = []
    base_path = ''
    files = os.listdir(base_path)
    char_limit = 2000

    for i, file_name in enumerate(files):
        print(f'embedding and storing perl file {i + 1} of {len(files)}')
        file = open(f'{base_path}/{file_name}', "r")
        file_content = file.read()
        file.close()

        f = open(f"", "w")

        chunks = chunk_perl_code(file_content, char_limit, file_name)

        # print(f'{file_name}:')

        for j, chunk in enumerate(chunks):
            f.write(chunk + '\n')

        f.close()
