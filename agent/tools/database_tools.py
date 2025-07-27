"""
Databázové nástroje - SQLite a Vector DB s právnymi pojmami
"""

from typing import List, Dict, Any, Optional, Type
from langchain.tools import BaseTool
from pydantic import Field
import sqlite3
import os
import json
import re

# Fallback pre ChromaDB ak nie je dostupné
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


class LegalTermSearchTool(BaseTool):
    """Nástroj pre vyhľadávanie právnych pojmov v databáze"""
    
    name: str = "legal_term_search"
    description: str = """
    Vyhľadáva definície právnych pojmov v databáze slovenských zákonov.
    Užitočné keď používateľ pýta na význam právnych termínov alebo chce vysvetlenie pojmov.
    Podporuje fuzzy vyhľadávanie a synonymá.
    Input: kľúčové slová alebo pojmy na vyhľadanie (string)
    """
    
    # Pydantic fields
    db_path: str = Field(default="data/legal_terms.db")
    
    def __init__(self, db_path: str = "data/legal_terms.db", **kwargs):
        super().__init__(db_path=db_path, **kwargs)
    
    def extract_keywords(self, query: str) -> List[str]:
        """Extrahuje kľúčové slová z používateľského dotazu"""
        # Odstráň bežné slová
        stop_words = {
            'čo', 'je', 'to', 'ako', 'kde', 'kedy', 'prečo', 'aký', 'aká', 'aké',
            'ktorý', 'ktorá', 'ktoré', 'môže', 'môžem', 'sa', 'si', 'ma', 'mi',
            'na', 'do', 'od', 'za', 'pre', 'pod', 'nad', 'o', 'v', 'vo', 'k', 'ku',
            'a', 'ale', 'alebo', 'ani', 'však', 'že', 'aby', 'keď', 'ak', 'či',
            'znamená', 'definícia', 'pojem', 'termín', 'vysvetli', 'objasni'
        }
        
        # Tokenizuj a vyčisti
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Pridaj aj pôvodné frázy s viacerými slovami
        phrases = []
        if 's ručením obmedzeným' in query.lower():
            phrases.append('spoločnosť s ručením obmedzeným')
        if 'právnická osoba' in query.lower():
            phrases.append('právnická osoba')
        if 'fyzická osoba' in query.lower():
            phrases.append('fyzická osoba')
        
        return keywords + phrases
    
    def _run(self, query: str) -> str:
        """Vyhľadaj právne pojmy"""
        try:
            # Extrahuj kľúčové slová
            keywords = self.extract_keywords(query)
            
            if not keywords:
                return "Neboli nájdené relevantné kľúčové slová v dotaze."
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Vyhľadávanie s fuzzy matching
            results = []
            for keyword in keywords[:3]:  # Max 3 kľúčové slová
                cursor.execute("""
                    SELECT term, definition, law_id, paragraph, confidence, category
                    FROM legal_terms 
                    WHERE term LIKE ? OR definition LIKE ?
                    ORDER BY confidence DESC, LENGTH(term) ASC
                    LIMIT 3
                """, (f"%{keyword}%", f"%{keyword}%"))
                
                keyword_results = cursor.fetchall()
                for result in keyword_results:
                    if result not in results:  # Vyvaruj sa duplicitám
                        results.append(result)
            
            conn.close()
            
            if not results:
                return f"Nenašli sa definície pre: {', '.join(keywords)}"
            
            # Formátuj výsledky
            response = f"🔍 Nájdené definície pre: {', '.join(keywords)}\n\n"
            
            for i, (term, definition, law_id, paragraph, confidence, category) in enumerate(results[:5], 1):
                response += f"{i}. **{term}** ({category})\n"
                response += f"   📍 {law_id}"
                if paragraph:
                    response += f" {paragraph}"
                response += f"\n"
                response += f"   📝 {definition}\n"
                response += f"   🎯 Spoľahlivosť: {confidence:.1f}/1.0\n\n"
            
            return response.strip()
            
        except sqlite3.Error as e:
            return f"Chyba databázy: {e}"
        except Exception as e:
            return f"Chyba pri vyhľadávaní: {e}"


def get_database_tools():
    """Vráti zoznam všetkých databázových nástrojov"""
    return [
        LegalTermSearchTool(),  # Tool pre vyhľadávanie právnych pojmov
        # VectorSearchTool() nahradený enhanced verziou v legal_agent.py
    ]
