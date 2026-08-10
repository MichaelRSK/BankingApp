from fastapi import FastAPI
from banking.account_controller import router as account_router

app = FastAPI()

app.include_router(account_router)