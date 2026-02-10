from dotenv import load_dotenv

load_dotenv()

def generate_prompt(chunked_perl, action):
    '''
    generates the watsonx prompt based on the input cobol, analysis type
    and context.
    '''

    if action == 'explain':
        prompt = (f"""
                    You are an expert in the Perl programming language. Your job is to explain the following Perl code chunk:
                    The code chunk will include the variables and the sub routines. Explain in detail what the does does and what is the sub routine returning. 
                    Perl code chunk for explanation: {chunked_perl}
                    Explanation:""")

    elif action == 'conversion':
        prompt = (f"""
                Transform the following Perl script to equivalent JAVA code.
                Mentioned below the mandatory instructions to be followed -
                1. Try to maintain the data types, file I/O, regex patterns, control structures, error handling, java libraries properly.
                2. Import all the necessary packages in output JAVA code.
                3. Don't include the input data (PERL script) in to the output.
                4. The data types in the perl script should be replicated properly in the output JAVA code.
                5. Don't exceed the input and output token greater than 16000 token.
                Important: You should only response in java code. Do not generate any additional information.     
                Perl Code: '{chunked_perl}'
                Java Code:""")
    
    elif action == 'convert_full':
        prompt = (f"""
                Transform the following Perl script to equivalent JAVA code.
                Mentioned below the mandatory instructions to be followed -
                1. Try to maintain the data types, file I/O, regex patterns, control structures, error handling, java libraries properly.
                2. Import all the necessary packages in output JAVA code.
                3. Don't include the input data (PERL script) in to the output.
                4. The data types in the perl script should be replicated properly in the output JAVA code.
                Important: You should only response in java code. Do not generate any additional information.     
                Perl Code: '{chunked_perl}'
                Java Code:""")
        
    elif action == 'explain_full':
        prompt = (f"""
                    You are an expert in the Perl programming language. Your job is to explain the following Perl code:
                    The code will include the variables and the sub routines. Explain in detail what the code does and what is the sub routine returning. 
                    Avoid returning code in the explanation.
                    Perl code chunk for explanation: '{chunked_perl}'
                    Explanation:""")
        
    return(prompt)