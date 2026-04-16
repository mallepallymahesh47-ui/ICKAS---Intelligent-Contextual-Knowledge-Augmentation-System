from pydantic import BaseModel
from main import full_chain
import os, shutil, uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from main import load_document, Split_doc
from Qdrant import store_documents
from Qdrant import get_retriever
from main import LLM

app=FastAPI(title="ICKAS API")

# In Memory store for active retriever
UPLOADED_DIR="Uploaded_files"
os.makedirs(name=UPLOADED_DIR, exist_ok=True)

class QueryRequest(BaseModel):
    question:str

class QueryResponse(BaseModel):
    response:str


# Post or Upload File API
# Allow Upload and process for load , chunk, store in Qdrant and save retriever chain in memory for Query
@app.post("/Upload", summary="Upload a Document")
async def upload_file(file: UploadFile = File(...)):
    allowed={".pdf", ".xlsx", ".txt", ".csv", ".docx"}
    path=os.path.splitext(file.filename)[1].lower()
    if path not in allowed:
        raise HTTPException(status_code=400, detail=f"File not supported : {path}")
    
    # Save the File
    unique_name = f"{uuid.uuid4()}_{file.filename}"
    save_path = os.path.join(UPLOADED_DIR, unique_name)
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    # Process 
    try:
        docs = load_document(save_path)
        chunks = Split_doc(docs)
        store_documents(chunks)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"message":"Loaded Document Sucessfully"}



# Post / Question or Query API
# Allow Query and Return Answer from retriever
@app.post("/Query", response_model=QueryResponse, summary="Ask Question form the File")
async def Query(query:QueryRequest):
    try:
        retriever=get_retriever()
        if not retriever:
            raise HTTPException(400, "No documents indexed yet")
        chain=full_chain(retriever)
        result=chain.invoke({"input":query.question})
        return {"response": result["answer"]}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
# Normal Chat
@app.post("/chat")
async def chat(query: QueryRequest):
    try:
        result = LLM.invoke(query.question)
        return {"response": result.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# Health Check
@app.get("/health")
async def health():
    return {
        "status":"Running"
    } 


    
