import os, json, httpx
from msal import ConfidentialClientApplication
TENANT = os.getenv("TENANT")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
WORKSPACE_ID = os.getenv("WORKSPACE_ID")

AUTHOIRTY = f"https://login.microsoftonline.com/{TENANT}"
SCOPE = ["https://analysis.windows.net/powerbi/api/.default"]
powerbi_api = "https://api.powerbi.com/v1.0/myorg"

def get_access_token():
    app = ConfidentialClientApplication(CLIENT_ID, authority=AUTHOIRTY, client_credential=CLIENT_SECRET)
    result = app.acquire_token_for_client(SCOPE, account = None)
    if not result:
        result = app.acquire_token_for_client(scopes = SCOPE)
    return result["access_token"]

async def import_csv_to_powerbi(csv_bytes: bytes, dataset_name: str):
    token = get_access_token()
    url = f"{powerbi_api}/groups/{WORKSPACE_ID}/imports?datasetDisplayName={dataset_name}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "multipart/form-data"
    }
    
    files = {"file": (f"{dataset_name}.csv", csv_bytes, "text/csv")}
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers = headers, files=files)
    resp.raise_for_status()
    return resp.json()

async def generate_embed_token(report_id: str):
    token = get_access_token
    url = f"{powerbi_api}/groups/{WORKSPACE_ID}/reports/{report_id}/GenerateToken"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {"accessLevel": "view"}
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json=body)
    resp.raise_for_status()
    return resp.json().get("token")
    