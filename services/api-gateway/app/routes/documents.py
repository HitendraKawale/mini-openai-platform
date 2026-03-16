from fastapi import APIRouter, Depends, File, Request, UploadFile

from app.middleware.auth import verify_api_key

router = APIRouter(prefix="/v1/documents", tags=["documents"])

@router.post("/upload", dependencies=[Depends(verify_api_key)])
async def upload_document(request: Request, file: UploadFile = File(...)):
    contents = await file.read()

    return {
        "message": "Document upload endpoint reached",
        "request_id": request.state.request_id,
        "filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": len(contents),
    }