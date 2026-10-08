import os

from fastapi import FastAPI

app = FastAPI(title="aws-ecs-fargate-cicd-pipeline")


@app.get("/")
def root():
    return {"message": "Hello from FastAPI on ECS Fargate"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/version")
def version():
    return {"version": os.getenv("APP_VERSION", "dev")}
