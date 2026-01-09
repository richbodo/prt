"""
FastAPI server for Natural Language SQL Interface.

Provides endpoints for:
- File upload (CSV, JSON, JSONL)
- Natural language query processing
- Database management
"""

import logging

from core.constants import ACCEPTED_FILE_EXTENSIONS
from core.data_models import ErrorResponse
from core.data_models import FileUploadResponse
from core.file_processor import convert_csv_to_sqlite
from core.file_processor import convert_json_to_sqlite
from core.file_processor import convert_jsonl_to_sqlite
from fastapi import FastAPI
from fastapi import File
from fastapi import HTTPException
from fastapi import UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Natural Language SQL Interface",
    description="Upload data files and query them using natural language",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {"status": "ok", "message": "Natural Language SQL Interface API"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/api/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a data file (CSV, JSON, or JSONL) and convert it to a SQLite table.

    Args:
        file: The uploaded file

    Returns:
        FileUploadResponse with table metadata

    Raises:
        HTTPException: If file type is unsupported or processing fails
    """
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(400, "No filename provided")

        # Check if file extension is supported
        if not any(file.filename.lower().endswith(ext) for ext in ACCEPTED_FILE_EXTENSIONS):
            raise HTTPException(
                400, f"Only {', '.join(ACCEPTED_FILE_EXTENSIONS)} files are supported"
            )

        # Read file content
        content = await file.read()

        if not content:
            raise HTTPException(400, "File is empty")

        # Extract table name from filename (without extension)
        table_name = file.filename.rsplit(".", 1)[0]

        # Route to appropriate converter based on file type
        result = None

        if file.filename.lower().endswith(".csv"):
            logger.info(f"Processing CSV file: {file.filename}")
            result = convert_csv_to_sqlite(content, table_name)

        elif file.filename.lower().endswith(".jsonl"):
            logger.info(f"Processing JSONL file: {file.filename}")
            result = convert_jsonl_to_sqlite(content, table_name)

        elif file.filename.lower().endswith(".json"):
            logger.info(f"Processing JSON file: {file.filename}")
            result = convert_json_to_sqlite(content, table_name)

        if result is None:
            raise HTTPException(500, "Failed to process file")

        logger.info(
            f"Successfully processed {file.filename}: "
            f"{result['row_count']} rows imported to table '{result['table_name']}'"
        )

        return FileUploadResponse(
            success=True,
            message=f"Successfully uploaded {file.filename}",
            table_name=result["table_name"],
            row_count=result["row_count"],
            schema=result["schema"],
            sample_data=result["sample_data"],
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error processing {file.filename}: {str(e)}")
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Error processing {file.filename}: {str(e)}", exc_info=True)
        raise HTTPException(500, f"Internal server error: {str(e)}")


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom exception handler for HTTPException."""
    return JSONResponse(status_code=exc.status_code, content=ErrorResponse(error=exc.detail).dict())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
