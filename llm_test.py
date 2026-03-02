from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="llama3:latest",
    validate_model_on_init=True,
    temperature=0.8,
    num_predict=512,
)

with open("temp.txt", "r") as f:
    content = f.read()

prompt = """
You are an email processor.

1. Remove all headers.
2. Extract only the body.
3. Summarize the body. Do NOT exclude any dates or time mentioned in the body

Return ONLY the final summary.
No explanations.
No extra text.
Markdown formatted text only.
"""

messages = [
    ("system", prompt),
    ("user", content)
]

response = llm.invoke(messages)
print(response.content.strip())