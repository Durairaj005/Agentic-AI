import os

os.environ["GOOGLE_API_KEY"] = "AIzaSyACkO3ztzLC0wrU08cdQ5eouUib1wWTRl4"

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from langchain_huggingface import HuggingFaceEmbeddings

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma

from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

# Create PDF
doc = SimpleDocTemplate("sample.pdf")
elements = []

styles = getSampleStyleSheet()
normal_style = styles["Normal"]

content = """
AuroraTech Employee Policy Handbook 2026

Working Hours:
Standard working hours are 9:30 AM to 6:30 PM.
Flexible login allowed between 8:30 AM and 10:30 AM.

Leave Policy:
Casual Leave: 12 days per year.
Sick Leave: 10 days per year.
Earned Leave: 15 days per year.

Refund Policy:
Refund processing time is 5 to 7 business days.
Refund allowed if service cancelled within 7 days.

Data Security:
Two-factor authentication is mandatory.
Passwords must be changed every 90 days.

Travel Policy:
Hotel reimbursement maximum is ₹5000 per night.
"""

for line in content.split("\n"):
    elements.append(Paragraph(line, normal_style))
    elements.append(Spacer(1, 0.2 * inch))

doc.build(elements)

print("PDF created successfully!")

# Load PDF
loader = PyPDFLoader("sample.pdf")
documents = loader.load()

# Split documents into chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
docs = text_splitter.split_documents(documents)

print(f"Loaded {len(documents)} pages and split into {len(docs)} chunks")

# Create embeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Vector Store
vectorstore = Chroma.from_documents(docs, embeddings)
retriever = vectorstore.as_retriever()
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)

# 6️⃣ Prompt
prompt = ChatPromptTemplate.from_template("""
Answer the question based only on the context below.

Context:
{context}

Question:
{question}
""")

# RAG Chain (Modern LCEL)
rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# Ask Question
response = rag_chain.invoke(
    "What was the company's Leave Policy?"
)
print(response)