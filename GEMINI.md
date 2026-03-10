# Project Overview: FastAPI File Uploads

This project is a FastAPI application designed to demonstrate robust file upload functionalities. It supports uploading files to both local storage and Amazon S3, incorporating best practices for handling large files through multipart uploads with `boto3`.

## Technologies Used:
*   **FastAPI**: For building the web API.
*   **boto3**: AWS SDK for Python, used for S3 interactions.
*   **pydantic-settings**: For managing application settings and environment variables.
*   **python-dotenv**: For loading environment variables from a `.env` file.
*   **uvicorn**: An ASGI server for running the FastAPI application.
*   **React (with TypeScript)**: For the user interface (frontend).
*   **Vite**: A fast build tool for the frontend.
*   **mongodb**: For storing upload information.

## Architecture:
The application exposes two main endpoints for file uploads:
1.  `/upload/local`: Handles uploads to a designated local directory (configured via `UPLOAD_DIR`).
2.  `/upload/s3`: Manages uploads to an Amazon S3 bucket, utilizing `boto3`'s `TransferConfig` for efficient multipart uploads of potentially large files.

Configuration settings for S3 (region, profile, bucket name) and the local upload directory are managed through `config/config.py` and loaded from environment variables defined in a `.env` file.

The frontend is a React application located in the `frontend/` directory, which interacts with these FastAPI endpoints.

## Building and Running:

### 1. Backend Environment Setup (FastAPI):
This project uses `uv` to manage Python versions and `uvicorn` to run the FastAPI application.

First, ensure you have `uv` installed. Then, create a virtual env and install dependencies:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv
uv sync --locked
```

### 2. Backend Configuration (FastAPI):
Create a `.env` file in the project root with the following variables:

```
UPLOAD_DIR=uploads
S3_REGION=your_aws_region
S3_PROFILE=your_aws_cli_profile
S3_BUCKET=your_s3_bucket_name
MONGO_DB_ROOT_USERNAME=mongo_username
MONGO_DB_ROOT_PASSWORD=mongo_root_password
MONGO_DB_USER=mongo_db_user
MONGO_DB_PASSWORD=mongo_db_password
```

Replace `your_aws_region`, `your_aws_cli_profile`, and `your_s3_bucket_name` with your actual AWS details. Ensure your AWS CLI profile has the necessary permissions to upload to the specified S3 bucket.

### 3. Running the Backend (FastAPI):
In a separate terminal, start the mongodb replicaset using docker compose:
```bash
docker compose -f compose-multi.yml up
```

In another terminal window, start the FastAPI application using Uvicorn:

```bash
uvicorn main:app --reload
```

The application will be accessible at `http://127.0.0.1:8000`. The API documentation (Swagger UI) will be available at `http://127.0.0.1:8000/docs`.

### 4. Frontend Setup and Running (React):

Navigate to the `frontend` directory, install dependencies, and start the development server:

```bash
cd frontend
npm install
npm run dev
```

The React development server will typically start on `http://localhost:5173` (or another available port). The frontend will then communicate with your FastAPI backend.

### 5. Testing:
Currently, explicit backend test commands are not defined.
TODO: Add comprehensive backend testing instructions and commands.

## Development Conventions:

*   **Code Style (Python)**: Adhere to standard Python best practices and conventions (e.g., PEP 8). Ruff is used for linting and formatting.
*   **Pre-commit Hooks**: This project uses `pre-commit` to ensure code quality. To set up:
    ```bash
    uv add pre-commit
    pre-commit install
    ```
*   **Code Style (React/TypeScript)**: Follow standard React and TypeScript conventions.
*   **Configuration**: All sensitive or environment-specific configurations should be managed via environment variables and loaded through `pydantic-settings` (backend) or defined as constants (frontend, for API base URL).
*   **Error Handling**: Use FastAPI's `HTTPException` for API-specific error responses on the backend. Implement client-side error handling in the React frontend to inform users of upload failures.
*   **Logging**: Basic logging is configured on the backend to provide insights into application flow.
