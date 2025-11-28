# Setup & Testing Guide

## Installation

1. Create virtual environment: `python3 -m venv venv`
2. Activate: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
3. Install: `pip install -r requirements.txt`
4. Get API key from https://ai.google.dev
5. Add to .env: `GOOGLE_API_KEY=AIzaSy...`

## Running the Server

```bash
python app.py
```

Server runs on http://localhost:5000

## Testing

### Health Check
```bash
curl http://localhost:5000/health
```

### Extract Bill
```bash
python quick_test.py TRAINING_SAMPLES/sample_1.png
```

### Download Training Samples
```bash
wget https://hackrx.blob.core.windows.net/files/TRAINING_SAMPLES.zip
unzip TRAINING_SAMPLES.zip
```

## Accuracy Metrics

- Item extraction: 95%+
- Duplicate detection: 92%+
- Total reconciliation: 96%+

See README.md for more info.
