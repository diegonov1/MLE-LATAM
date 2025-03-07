# Challenge Documentation
## Part I: Model Implementation (`model.py`)
### Model Selection

In `exploration.ipynb`, **XGBoost** and **Logistic Regression** were evaluated. **Logistic Regression** was chosen for operationalization.

**Reasoning:**

Logistic Regression offers a better balance for this specific production environment:

*   **Speed and Efficiency:** Logistic Regression is significantly faster for training and inference, crucial for a low-latency API.
*   **Interpretability:** Logistic Regression coefficients provide insights into feature importance, aiding in understanding delay factors.
*   **Simplicity and Maintainability:**  Simpler models are easier to maintain and debug in production.

While XGBoost might offer slightly better performance, this difference is not significant and can be biased by the random state, on the other hand, Logistic Regression's speed, and interpretability make it a pragmatic choice. However, this choice might change if parameter's tuning is applied to XGBOOST.

### Bug Fixes and Code Improvements

The `exploration.ipynb` code was transcribed to `model.py` with these improvements:

*   **Encapsulation:**  A `DelayModel` class encapsulates model logic, preprocessing, training, and prediction.
*   **Model Persistence:** `__load_model` and `__save_model` methods use `pickle` for model persistence.
*   **Error Handling and Logging:** `try-except` blocks and the `logging` module provide robust error handling and informative messages.
*   **Input Validation and Type Hinting:** Type hints improve readability. Input validation is handled implicitly by Pandas and Scikit-learn.
*   **Code Clarity:** Descriptive variable names and comments enhance readability.
*   **Removed Unnecessary Code:** Only code relevant to the Logistic Regression model was kept.
*   **Threshold Constant:** The delay threshold (15 minutes) is a class constant `_THRESHOLD_IN_MINUTES`.
*   **Feature Selection Consistency:** `_TOP_FEATURES` ensures consistent feature use.
*   **Model Training Check:** `self._is_trained` prevents predictions before training.

## Part II: API Implementation (`api.py`)

### API Framework

**FastAPI** was used for this API. FastAPI offers:

*   **Performance:** Built on Starlette and Uvicorn for high performance.
*   **Automatic Data Validation:** Uses Pydantic for data validation.
*   **Automatic Documentation:** Generates interactive API documentation.
*   **Ease of Use:** Clean and intuitive API.

### API Endpoints

*   **`/health` (GET):** Health check endpoint (returns `200 OK` and `{"status": "OK"}`).
*   **`/predict` (POST):** Prediction endpoint. Accepts a JSON payload (list of `FlightData` objects with `OPERA`, `MES`, `TIPOVUELO`).
    *   **Input Validation:** Validates `MES` (1-12), `TIPOVUELO` ("I" or "N"), and `OPERA` (from `VALID_AIRLINES`).
    *   **Prediction Logic:** Extracts data, creates a DataFrame, preprocesses with `DelayModel.preprocess`, predicts with `DelayModel.predict`, and returns predictions.
    *   **Error Handling:** Uses `HTTPException` for input errors (400), model `ValueError` (400), and unexpected errors (500).

## Part III: API Deployment in GCP Cloud Run

### Cloud Provider

**Google Cloud Platform (GCP)**, specifically **Cloud Run**, was chosen for:

*   **Serverless and Scalable:** Automatically scales and is cost-efficient.
*   **Container-Based Deployment:** Uses container images (provided `Dockerfile`).
*   **Ease of Deployment:** Simple deployment with `gcloud run deploy`.
*   **Integration with GCP Ecosystem:** Integrates with Artifact Registry.

### Deployment Steps (Automated in `cd.yml`)

1.  **Containerization:** Docker image built using the `Dockerfile`.
2.  **Container Registry:** Image pushed to **Artifact Registry**.
3.  **Cloud Run Deployment:** `gcloud run deploy` with:
    *   Service Name: `secrets.GCP_SERVICE_NAME`.
    *   Region: `secrets.GCP_REGION`.
    *   Platform: `managed`.
    *   Allow Unauthenticated Invocations: `--allow-unauthenticated`.
    *   Timeout: `--timeout=300`.
    *   Memory and CPU: `--memory=1Gi --cpu=2`.

### API URL

The API URL is in the `Makefile` (`API_URL`) for stress tests.

## Part IV: CI/CD Implementation (`.github/workflows`)

### CI/CD Pipeline

**GitHub Actions** automates build, test, and deployment.

### Continuous Integration (CI) - `ci.yml`

1.  **Trigger:** `push` and `pull_request` to `main` and `develop`.
2.  **Checkout Code:** `actions/checkout@v3`.
3.  **Set up Python:** `actions/setup-python@v4` (version 3.11).
4.  **Install Libraries:** Installs dependencies from `requirements.txt` and `requirements-test.txt`.
5.  **Run Unit Tests:** `pytest tests/model` and `pytest tests/api`.

### Continuous Delivery (CD) - `cd.yml`

1.  **Trigger:** `push` to `main` and `develop`.
2.  **Checkout Code:** `actions/checkout@v3`.
3.  **Authenticate to GCP:** `google-github-actions/auth@v2` (using `secrets.GCP_SA_KEY`).
4.  **Set up Google Cloud SDK:** `google-github-actions/setup-gcloud@v1`.
5.  **Configure Docker:** `gcloud auth configure-docker`.
6.  **Build and Push Docker Image:** Builds and pushes to Artifact Registry.
7.  **Deploy to Cloud Run:** `gcloud run deploy` with configurations from secrets.

### GitHub Secrets

*   `GCP_SA_KEY`: GCP Service Account key.
*   `GCP_PROJECT_ID`: GCP Project ID.
*   `GCP_REGION`: GCP Region.
*   `GCP_REPO_NAME`: Artifact Registry repository name.
*   `GCP_SERVICE_NAME`: Cloud Run service name.

### Deployment Adjustments

Initial adjustments were made to GCP service account permissions (IAM).  Experience with Azure Functions/App Services helped in understanding GCP's IAM, focusing on least privilege for Artifact Registry and Cloud Run.

### GitFlow Practices

The repository uses GitFlow, adapted for this project:

*   **`main`:** Official release branch.
*   **`develop`:** Integration branch.
*   **Feature branches:** Branched from `develop`, merged back into `develop`.
*   **Release branches:** Branched from `develop`, merged into `main` and `develop`.
*   **Hotfix branches:** Branched from `main`, merged into `main` and `develop`. Used for quick adjustments and improvements during development and deployment (e.g., documentation updates, configuration tweaks).

CI/CD workflows trigger on `main` and `develop`.