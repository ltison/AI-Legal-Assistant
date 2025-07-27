"""
Vyhľadávacie nástroje pre agenta - Tavily a Wikipedia
"""

from typing import Optional, Dict, Any, Type
from langchain.tools import BaseTool
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from pydantic import Field
import os
from dotenv import load_dotenv
import warnings

load_dotenv()

# Fallback pre Tavily ak nie je dostupné
try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False


class TavilySearchTool(BaseTool):
    """Nástroj pre vyhľadávanie právnych informácií cez Tavily API"""
    
    name: str = "tavily_search"
    description: str = """
    Použite tento nástroj na vyhľadávanie aktuálnych právnych informácií, zákonov, 
    súdnych rozhodnutí a právnych predpisov. Vhodné pre otázky o slovenskom a českom práve.
    Input: vyhľadávacia fráza (string)
    """
    
    # Pydantic fields
    client: Optional[Any] = Field(default=None, exclude=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        api_key = os.getenv("TAVILY_API_KEY")
        
        if not TAVILY_AVAILABLE:
            self.client = None
        elif not api_key:
            self.client = None
        else:
            try:
                self.client = TavilyClient(api_key=api_key)
            except Exception:
                self.client = None
    
    def _run(self, query: str) -> str:
        """Vykonaj vyhľadávanie cez Tavily"""
        if not self.client:
            return f"Tavily search nie je dostupný. Skúste nastaviť TAVILY_API_KEY pre otázku: {query}"
        
        try:
            # Pridáme kontext pre slovenské právo
            enhanced_query = f"{query} slovenské právo zákon"
            
            response = self.client.search(
                query=enhanced_query,
                search_depth="advanced",
                max_results=5,
                include_domains=["justice.gov.sk", "zbierka.sk", "epi.sk", "lexforum.cz"]
            )
            
            results = []
            for result in response.get('results', []):
                results.append(f"**{result['title']}**\n{result['content']}\nZdroj: {result['url']}\n")
            
            return "\n".join(results) if results else "Neboli nájdené žiadne relevantné výsledky."
            
        except Exception as e:
            return f"Chyba pri vyhľadávaní: {str(e)}"
    
    async def _arun(self, query: str) -> str:
        """Async verzia"""
        return self._run(query)


class LegalWikipediaTool(BaseTool):
    """Upravený Wikipedia nástroj pre právne pojmy"""
    
    name: str = "wikipedia_legal"
    description: str = """
    Vyhľadáva základné informácie o právnych pojmoch, inštitúciách a konceptoch 
    na Wikipédii. Najlepšie pre definície a všeobecné informácie.
    Input: právny pojem alebo koncept (string)
    """
    
    # Pydantic fields
    wikipedia: Optional[Any] = Field(default=None, exclude=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            self.wikipedia = WikipediaQueryRun(
                api_wrapper=WikipediaAPIWrapper(
                    lang="sk",  # Slovenská wikipedia ako primárna
                    top_k_results=3,
                    doc_content_chars_max=2000
                )
            )
        except Exception:
            self.wikipedia = None
    
    def _run(self, query: str) -> str:
        """Vyhľadaj na Wikipédii"""
        if not self.wikipedia:
            return f"Wikipedia search nie je dostupný pre otázku: {query}"
            
        try:
            # Ignoruj varovania o parseri
            # Toto je potrebné pre niektoré verzie Wikipedie, ktoré používajú
            # BeautifulSoup bez explicitného parsera
            # a môže spôsobiť varovania pri načítaní stránok.
            
            warnings.filterwarnings(
                "ignore",
                category=UserWarning,
                message="No parser was explicitly specified"
            )
            
            # Skús najprv slovensky
            result = self.wikipedia.run(query)
            
            # Ak nič nenájde, skús česky
            if "No good Wikipedia Search Result was found" in result:
                self.wikipedia.api_wrapper.lang = "cs"
                result = self.wikipedia.run(query)
                
            # Vráť späť na slovenčinu pre ďalšie vyhľadávania
            self.wikipedia.api_wrapper.lang = "sk"
            
            return result
            
        except Exception as e:
            return f"Chyba pri vyhľadávaní na Wikipédii: {str(e)}"
    
    async def _arun(self, query: str) -> str:
        """Async verzia"""
        return self._run(query)


def get_search_tools():
    """Vráti zoznam všetkých vyhľadávacích nástrojov"""
    return [
        TavilySearchTool(),
        LegalWikipediaTool()
    ]
