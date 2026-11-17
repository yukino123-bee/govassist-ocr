import os
import shutil
import tempfile

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile

from document_review import review
from translate import translate_text

app = FastAPI()
API_KEY = os.environ.get("OCR_API_KEY", "")


def check_key(key):
    if not API_KEY or key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


def save_upload(upload, directory, name):
    extension = os.path.splitext(upload.filename or "")[1].lower()
    path = os.path.join(directory, name + extension)
    with open(path, "wb") as target:
        shutil.copyfileobj(upload.file, target)
    return path


@app.get("/health")
def health():
    return {
        "status": "ok",
        "tesseract": bool(shutil.which("tesseract")),
        "pdftoppm": bool(shutil.which("pdftoppm")),
    }


@app.post("/review")
def review_document(
    document: UploadFile = File(...),
    template: UploadFile | None = File(None),
    keywords: str = Form(""),
    x_api_key: str = Header(""),
):
    check_key(x_api_key)
    with tempfile.TemporaryDirectory(prefix="govassist-") as directory:
        document_path = save_upload(document, directory, "document")
        template_path = save_upload(template, directory, "template") if template else None
        return review(document_path, template_path, keywords)


@app.post("/translate")
def translate(text: str = Form(...), x_api_key: str = Header("")):
    check_key(x_api_key)
    return translate_text(text)
