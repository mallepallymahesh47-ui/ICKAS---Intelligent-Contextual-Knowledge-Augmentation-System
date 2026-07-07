from pydantic import BaseModel
from main import full_chain
import os, tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from main import load_document, Split_doc
from Qdrant import store_documents
from Qdrant import get_retriever
from main import LLM
from mongo import save_file, get_file

app=FastAPI(title="ICKAS API")

class QueryRequest(BaseModel):
    question:str

class QueryResponse(BaseModel):
    response:str


# Post or Upload File API
# Allow Upload and process for load , chunk, store in Qdrant and save retriever chain in memory for Query
@app.post("/Upload", summary="Upload a Document")
async def upload_file(file: UploadFile = File(...)):
    allowed={".pdf", ".xlsx", ".txt", ".csv", ".docx"}
    ext=os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"File not supported : {ext}")

    # Save the File to MongoDB (GridFS)
    try:
        file_id = save_file(file.file, filename=file.filename, content_type=file.content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store file in MongoDB: {e}")

    # Process: pull the file back out of MongoDB into a temp file on disk so the
    # existing loaders (which expect a filesystem path) can read it, then clean up.
    tmp_path = None
    try:
        grid_out = get_file(file_id)
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(grid_out.read())
            tmp_path = tmp.name

        docs = load_document(tmp_path)
        chunks = Split_doc(docs)
        store_documents(chunks)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    return {"message": "Loaded Document Sucessfully", "file_id": file_id}



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


    
