import logging
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

def create_prompt():
    prompt = \
    """
    You are a helpful email summariser.
    
    Perform the following tasks:
    1. Remove ALL Headers
    2. Extract the main body of the email.
    3. Extract and summarize the key information from the email below.
        Include:
        - Purpose of the email
        - Important dates mentioned
        - Reason (if any)
        - When normal operations resume
        - Any action required
    4. Do not add any extra comments before or after the summary.

    Email:
    {email}
    """
    return ChatPromptTemplate.from_template(prompt)

def get_llm(model_name="llama3:latest", temperature=0.1):
    return ChatOllama(
        model=model_name,
        validate_model_on_init=True,
        temperature=temperature,
        num_predict=512
    )

def build_chain(prompt, llm):
    return prompt | llm

def run_llm(chain, mail: str):
    return chain.invoke({"email": mail}).content

def summarize(data):
    prompt = create_prompt()
    model = get_llm()
    chain = build_chain(prompt, model)
    result = run_llm(chain, data)

    return result