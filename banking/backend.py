from fastapi import FastAPI
from .transactions import router as transaction_router


app = FastAPI()

app.include_router(transaction_router)