import openai
import os
from langchain.document_loaders import PyPDFLoader
from langchain.document_loaders import Docx2txtLoader
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Qdrant
from langchain.embeddings import OpenAIEmbeddings


os.environ["OPENAI_API_KEY"] = "sk-123"
os.environ["OPENAI_API_BASE"] = "https://api.openai-proxy.com/v1"


# 加载知识库
base_dir = ".\test_data_source"
documents = []

for file in os.listdir(base_dir):
    file_path = os.path.join(base_dir, file)
    if file.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
        documents.extend(loader.load())
    elif file.endswith(".docx"):
        loader = Docx2txtLoader(file_path)
        documents.extend(loader.load())
    elif file.endswith(".txt"):
        loader = TextLoader(file_path)
        documents.extend(loader.load())

# 切片 准备存入向量数据库
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
chunked_documents = text_splitter.split_documents(documents)

# 进行嵌入和向量存储
vectorstore = Qdrant.from_documents(
    documents=chunked_documents,  # 以分块的文档
    embedding=OpenAIEmbeddings(),  # 用OpenAI的Embedding Model做嵌入
    location=":memory:",  # in-memory 存储
    collection_name="my_documents",  # 指定collection_name
)


response = openai.completions.create(
    model="deepseek-chat",
    temperature=0.5,
    max_tokens=100,
)

print(response.choices[0].text.strip())
