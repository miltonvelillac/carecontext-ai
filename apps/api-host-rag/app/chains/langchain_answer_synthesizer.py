from langchain_core.prompts import ChatPromptTemplate

from app.ports.llm import LlmProvider, LlmRequest
from app.ports.retrieval_tools import RetrievedChunk
from app.schemas.common import LanguageCode

RAG_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a bilingual educational health and psychology RAG assistant. "
            "You must stay grounded in the provided context and avoid unsupported "
            "medical claims.",
        ),
        (
            "human",
            "Answer the question using only the retrieved context. "
            "If the context is empty or insufficient, say that relevant context was "
            "not found. Keep the answer educational, avoid diagnosis or treatment "
            "instructions, and mention that it is not medical advice.\n\n"
            "Language: {language}\n\n"
            "Retrieved context:\n{context}\n\n"
            "Question: {query}",
        ),
    ]
)


class LangChainAnswerSynthesizer:
    def __init__(self, llm_provider: LlmProvider) -> None:
        self.llm_provider = llm_provider

    async def synthesize(
        self,
        *,
        query: str,
        language: LanguageCode,
        retrieved_chunks: list[RetrievedChunk],
    ) -> str:
        if not retrieved_chunks:
            return (
                "I could not find relevant context in the indexed documents for this question. "
                "This assistant is educational and not a substitute for professional care."
            )

        response = await self.llm_provider.generate(
            LlmRequest(
                prompt=_build_rag_prompt(query, retrieved_chunks, language),
                system_prompt=_rag_system_prompt(),
                language=str(language),
            )
        )
        return response.text


def _build_rag_prompt(
    query: str,
    retrieved_chunks: list[RetrievedChunk],
    language: LanguageCode,
) -> str:
    context = "\n".join(
        f"[{index}] {chunk.title} ({chunk.chunk_id}): {chunk.snippet}"
        for index, chunk in enumerate(retrieved_chunks, start=1)
    )
    messages = RAG_PROMPT_TEMPLATE.format_messages(
        language=str(language),
        context=context,
        query=query,
    )
    return "\n\n".join(message.content for message in messages)


def _rag_system_prompt() -> str:
    system_message = RAG_PROMPT_TEMPLATE.messages[0].format()
    return str(system_message.content)
