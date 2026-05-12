from openai import AsyncOpenAI

from services.config import settings


class OpenAIClientError(Exception):
    pass


client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)


def get_openai_client():
    return client