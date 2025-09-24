## Smart Shopping Pulse (Streamlit)

### Setup

1. Create/activate a virtual environment (Windows PowerShell):
```powershell
python -m venv .venv
. .venv\\Scripts\\Activate.ps1
```

2. Install dependencies:
```powershell
pip install -r requirements.txt
```

3. (Optional) Configure Langflow for LLM insights:
```powershell
$env:LANGFLOW_URL = "http://localhost:7860/api/v1/run/231292dc-aa6c-449a-b565-dbcf5667ff23"
$env:LANGFLOW_API_KEY = "<your_key>"
```

### Run

```powershell
streamlit run app.py
```

### Features

- Multisource data (stubbed) with price/rating/reviews/sustainability
- Multimodal search: text, image upload, audio upload
- Predictive/agentic tips and optional LLM insights via Langflow
 - Dashboard: price vs rating, sustainability boxplot, trending, shopping list


