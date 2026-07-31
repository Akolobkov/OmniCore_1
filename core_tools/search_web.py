from langchain_talordata import TalorSerpTool
from dotenv import load_dotenv
import os
search_tool = TalorSerpTool.from_env()
def search_web(query: str, engine: str = "google") -> str:
    """
    Searches through internet with TalorData SERP API.

    Args:
        query (str): query
        engine (str): Searching system (default "google")

    Returns:
        str: Search results text
    """
    load_dotenv()
    os.environ["TALOR_API_KEY"] = os.getenv("TALOR_API_KEY")
    try:
        # Выполняем поиск
        result = search_tool.invoke({
            "query": query,
            "engine": engine,
            "params": {
                "gl": "us",  # Гео-таргетинг (страна)
                "hl": "eng",  # Язык результатов
                "device": "desktop"
            }
        })
        return str(result) if result else "Nothing was found."
    except Exception as err:
        print(f'Searching error: {err}')
        return f"ERROR: {err}"
