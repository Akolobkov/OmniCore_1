from langchain_talordata import TalorSerpTool
from dotenv import load_dotenv
import os
search_tool = TalorSerpTool.from_env()
def search_web(query: str, engine: str = "google") -> str:
    """
    Выполняет поиск в интернете через TalorData SERP API.

    Args:
        query (str): Поисковый запрос
        engine (str): Поисковая система (по умолчанию "google")

    Returns:
        str: Результаты поиска в текстовом формате
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
        return str(result) if result else "Ничего не найдено."
    except Exception as err:
        print(f'Ошибка при поиске: {err}')
        return f"ОШИБКА: {err}"
