import os
import sys
import asyncio
from google import genai
from google.genai import types, errors
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from config import GOOGLE_API_KEY, MODEL_NAME, FALLBACK_MODEL, COLLECTION_NAME
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
client = genai.Client(api_key=GOOGLE_API_KEY)
SYSTEM_PROMPT = """
You are an AI document assistant.
Use search_documents to answer questions about uploaded files.
Use list_documents to list uploaded files.
Answer using the tool results. Do not invent facts.
Mention the source filename when possible.
If information is missing, say it was not found in the documents.
Reply normally to greetings.
"""
async def call_gemini(contents, settings):
    last_error = "unknown error"
    for model in [MODEL_NAME, FALLBACK_MODEL]:
        for attempt in range(3):
            try:
                return await client.aio.models.generate_content(
                    model=model,
                    contents=contents,
                    config=settings
                )
            except errors.APIError as error:
                last_error = f"{model} - {error.code}: {error.message}"
                print("Gemini error:", last_error)
                if error.code in (500, 503, 504):
                    await asyncio.sleep(2 * (attempt + 1))
                elif error.code in (404, 429):
                    break
                else:
                    raise
    raise RuntimeError(last_error)
async def ask(question, history=None, session_id=None):
    collection_name = f"{COLLECTION_NAME}_{session_id}"
    server = StdioServerParameters(
        command=sys.executable,
        args=[os.path.join(BASE_DIR, "mcp_server.py")],
        cwd=BASE_DIR,
        env={
            **os.environ,
            "RAG_COLLECTION_NAME": collection_name,
            "GOOGLE_API_KEY": GOOGLE_API_KEY
        }
    )
    tool_calls = []
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_tools = await session.list_tools()
            tools = [
                types.Tool(
                    function_declarations=[
                        types.FunctionDeclaration(
                            name=tool.name,
                            description=tool.description,
                            parameters_json_schema=tool.inputSchema
                        )
                    ]
                )
                for tool in mcp_tools.tools
            ]
            contents = []
            for message in (history or [])[-6:]:
                role = "user" if message["role"] == "user" else "model"
                contents.append(
                    types.Content(role=role, parts=[types.Part(text=message["content"])])
                )
            contents.append(
                types.Content(role="user", parts=[types.Part(text=question)])
            )
            settings = types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=tools,
                temperature=0,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
            )
            for step in range(5):
                try:
                    response = await call_gemini(contents, settings)
                except (errors.APIError, RuntimeError) as error:
                    return {
                        "answer": f"The AI model is not available right now. Reason: {str(error)[:300]}",
                        "tool_calls": tool_calls,
                        "failed": True
                    }
                if not response.candidates or response.candidates[0].content is None:
                    return {
                        "answer": "No answer received. Please try a different question.",
                        "tool_calls": tool_calls,
                        "failed": True
                    }
                contents.append(response.candidates[0].content)
                if not response.function_calls:
                    return {
                        "answer": response.text or "No answer generated.",
                        "tool_calls": tool_calls,
                        "failed": False
                    }
                results = []
                for call in response.function_calls:
                    arguments = dict(call.args or {})
                    result = await session.call_tool(call.name, arguments)
                    result_text = "\n".join(
                        item.text for item in result.content if item.type == "text"
                    )
                    tool_calls.append({
                        "name": call.name,
                        "args": arguments,
                        "result": result_text
                    })
                    results.append(
                        types.Part.from_function_response(
                            name=call.name,
                            response={"result": result_text}
                        )
                    )
                contents.append(types.Content(role="user", parts=results))
    return {
        "answer": "Please try asking your question again.",
        "tool_calls": tool_calls,
        "failed": True
    }