from fastapi import APIRouter 
from fastapi.responses import StreamingResponse


from .models import QueryRequest
from utils.llm.llm import Llm

router = APIRouter()
llm = Llm()

@router.post("/generate")
async def generate(request: QueryRequest) -> StreamingResponse:
    """
    Generates a response based on the user input text using a pre-trained causal language model.

    This endpoint takes a JSON object with a single key "query" containing the user input text.
    The response is a stream of generated text, which is produced in real-time.

    Parameters:
    request (QueryRequest): A JSON object with a single key "query" containing the user input text.

    Returns:
    StreamingResponse: A stream of generated text, which is produced in real-time.
    """

    stream_response: Iterable[str] = llm.run_generation(request.query)
    return StreamingResponse(stream_response, media_type="text/plain")

