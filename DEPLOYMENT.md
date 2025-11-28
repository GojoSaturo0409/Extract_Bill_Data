# Deployment Guide

## Heroku

1. Initialize git: `git init && git add . && git commit -m "initial"`
2. Create app: `heroku create your-app-name`
3. Set env: `heroku config:set GOOGLE_API_KEY="AIzaSy..."`
4. Deploy: `git push heroku main`

## Docker

1. Build: `docker build -t bill-extractor .`
2. Run: `docker run -p 5000:5000 -e GOOGLE_API_KEY="AIzaSy..." bill-extractor`

## Google Cloud Run

```bash
gcloud run deploy bill-extractor --source .
```

## AWS Lambda

Package and deploy as Lambda function with API Gateway.

## Environment Variables

- GOOGLE_API_KEY (required)
- FLASK_ENV (optional, default: development)
- PORT (optional, default: 5000)

See README.md for API specification.
