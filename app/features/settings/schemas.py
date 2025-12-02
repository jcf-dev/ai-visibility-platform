from pydantic import BaseModel


class ApiKeySet(BaseModel):
    provider: str
    api_key: str


class ApiKeyList(BaseModel):
    providers: list[str]
