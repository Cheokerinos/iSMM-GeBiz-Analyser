import os

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from powerbi import import_csv_to_powerbi, generate_embed_token
from fastapi.responses import JSONResponse

app = FastAPI()
@app.get("/")
def read_root():
    return {"status": "running", "message": "Power BI scraper back-end is up"}  

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  allow_methods=["*"], allow_headers=["*"]
)

@app.post("/uploadfile/")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code = 400, detail = "Only CSV files are allowed.")
    csv_bytes = await file.read()
    dataset_name = os.path.splitext(file.filename)[0]
    try:
        response = await import_csv_to_powerbi(csv_bytes, dataset_name)
        report_id = response["import"]["reports"][0]["id"]
        embed_token = await generate_embed_token(report_id)
        embed_url = response["import"]["reports"][0]["id"]
        return JSONResponse(content = {"filename": file.filename})
    except Exception as e:
        raise HTTPException(status_code = 500, detail = str(e))
'''
@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")  
    csv_bytes = await file.read()
    dataset_name = os.path.splitext(file.filename)[0]
    try:
        response = await import_csv_to_powerbi(csv_bytes, dataset_name)
        report_id = response["import"]["reports"][0]["id"]
        embed_token = await generate_embed_token(report_id)
        embed_url = response["import"]["reports"][0]["embedUrl"]
        return {"embedUrl": embed_url, "embedToken": embed_token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
'''