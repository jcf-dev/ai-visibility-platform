from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.infrastructure.database import get_db
from app.features.settings.models import ApiKey
from app.features.settings.schemas import ApiKeySet, ApiKeyList
from app.infrastructure.security import encrypt_value
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Settings"])


@router.put("/settings/keys", summary="Set an API key for a provider")
async def set_api_key(key_data: ApiKeySet, db: AsyncSession = Depends(get_db)):
    # Encrypt the key before saving
    encrypted_key = encrypt_value(key_data.api_key)

    # Safety check: Ensure encryption actually happened
    if encrypted_key == key_data.api_key and key_data.api_key:
        logger.error("Encryption failed: Value returned unchanged")
        raise HTTPException(status_code=500, detail="Encryption failed")

    # Check if exists
    result = await db.execute(
        select(ApiKey).where(ApiKey.provider == key_data.provider)
    )
    existing_key = result.scalars().first()

    if existing_key:
        existing_key.api_key = encrypted_key
    else:
        new_key = ApiKey(provider=key_data.provider, api_key=encrypted_key)
        db.add(new_key)

    await db.commit()
    logger.info(f"API key for {key_data.provider} updated (encrypted)")
    return {"message": f"API key for {key_data.provider} updated successfully"}


@router.get(
    "/settings/keys", response_model=ApiKeyList, summary="List configured providers"
)
async def list_configured_providers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ApiKey.provider))
    providers = result.scalars().all()
    return ApiKeyList(providers=list(providers))
