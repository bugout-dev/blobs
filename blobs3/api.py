"""
Top-level Spire API
"""
import logging
import os
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import access, blockchains
from .version import VERSION

LOG_LEVEL = logging.INFO
if os.getenv("BLOBS3_DEBUG", "").lower() == "true":
    LOG_LEVEL = logging.DEBUG

LOG_FORMAT = "[%(levelname)s] %(name)s (Source: %(pathname)s:%(lineno)d, Time: %(asctime)s) - %(message)s"
logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)

app = FastAPI(
    title=f"blobs3",
    description="Blob storage with web3 access control",
    version=VERSION,
    openapi_url="/openapi.json",
    docs_url=None,
    redoc_url="/docs",
)

# CORS configuration
origins_raw = os.environ.get("BLOBS3_CORS_ALLOWED_ORIGINS")
if origins_raw is None:
    raise ValueError("BLOBS3_CORS_ALLOWED_ORIGINS environment variable must be set")
origins = origins_raw.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["OPTIONS", "GET"],
    allow_headers=[],
)

# Blockchain configuration
blockchain_config_file = os.environ.get("BLOBS3_BLOCKCHAIN_CONFIG")
if blockchain_config_file is None:
    raise ValueError("BLOBS3_BLOCKCHAIN_CONFIG environment variable must be set")
blockchain_definitions = blockchains.load_definitions_from_file(blockchain_config_file)
blockchain_manager = blockchains.BlockchainManager(blockchain_definitions)

# Access configuration
access_config_file = os.environ.get("BLOBS3_ACCESS_CONFIG")
if access_config_file is None:
    raise ValueError("BLOBS3_ACCESS_CONFIG environment variable must be set")
access_list = access.load_access_list_from_file(access_config_file)
access_manager = access.AccessManager(
    storage_access_list=access_list, blockchains=blockchain_manager
)


@app.on_event("startup")
async def startup() -> None:
    blockchain_manager.start_healthchecks()


@app.on_event("shutdown")
def shutdown() -> None:
    blockchain_manager.stop_healthchecks()


@app.get("/ping")
async def ping() -> str:
    return "OK"


@app.get("/version")
async def version() -> str:
    return VERSION


@app.get("/health", response_model=Dict[str, blockchains.BlockchainHealth])
async def health() -> Dict[str, blockchains.BlockchainHealth]:
    return blockchain_manager.health_status()


@app.get("/authorization", response_model=Optional[access.StorageAccess])
async def authorization(
    user_address: str = Query(None),
    path: str = Query(None),
    access_type: access.AccessType = Query(None),
) -> Optional[access.StorageAccess]:
    if user_address is None:
        raise HTTPException(
            status_code=400, detail="Please pass the user_address query parameter"
        )

    if path is None:
        raise HTTPException(
            status_code=400, detail="Please pass the path query parameter"
        )

    print({"path": path, "user_address": user_address, "access_type": access_type})

    return access_manager.authorization(
        user_address=user_address, access_type=access_type, path=path
    )
