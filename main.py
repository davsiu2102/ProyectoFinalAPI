from fastapi import FastAPI, HTTPException, Path, Query
import models
from typing import Annotated
from contextlib import asynccontextmanager
from db import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)