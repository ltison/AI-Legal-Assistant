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
    
    DÔLEŽITÉ POKYNY PRE POUŽITIE:
    - Analyzuj používateľskú otázku a identifikuj v nej konkrétne právne pojmy alebo termíny
    - Extrahuj kľúčové právne pojmy ako: "vlastníctvo", "dedenie", "s.r.o.", "kúpna zmluva", "nájom", atď.
    - Pre komplexné otázky môžeš poslať viacero pojmov naraz oddelených čiarkami
    - Nepoužívaj celé vety, ale konkrétne termíny (napr. namiesto "ako založiť s.r.o." použij "s.r.o., založenie")
    - Kombinuj základné aj odborné názvy (napr. "spoločnosť s ručením obmedzeným, s.r.o.")
    
    Vstup: jeden alebo viacero pojmov oddelených čiarkami (napr. "vlastníctvo, dedenie" alebo "s.r.o.")
    Výstup: definície, zdroje zákonov a relevantné informácie pre každý pojem
    """
    
    # Pydantic fields
    db_path: str = Field(default="data/legal_terms.db")
    
    def __init__(self, db_path: str = "data/legal_terms.db", **kwargs):
        super().__init__(db_path=db_path, **kwargs)
    
    def _run(self, query: str) -> str:
        """Vyhľadaj právne pojmy"""
        try:
            # Agent môže poslať viacero pojmov oddelených čiarkami alebo slovami "a", "aj"
            search_terms = []
            
            # Rozdeľ na čiarky alebo spojky
            if ',' in query:
                search_terms = [term.strip() for term in query.split(',') if term.strip()]
            elif ' a ' in query or ' aj ' in query:
                # Nahraď spojky čiarkami a rozdeľ
                temp_query = query.replace(' a ', ', ').replace(' aj ', ', ')
                search_terms = [term.strip() for term in temp_query.split(',') if term.strip()]
            else:
                # Jeden pojem
                search_terms = [query.strip()]
            
            if not search_terms or not any(search_terms):
                return "Nebol zadaný žiadny pojem na vyhľadanie."
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            all_results = []
            
            # Vyhľadávaj každý pojem samostatne
            for search_term in search_terms[:5]:  # Max 5 pojmov
                if not search_term:
                    continue
                    
                cursor.execute("""
                    SELECT term, definition, law_id, paragraph, confidence, category
                    FROM legal_terms 
                    WHERE term LIKE ? OR definition LIKE ?
                    ORDER BY confidence DESC, LENGTH(term) ASC
                    LIMIT 3
                """, (f"%{search_term}%", f"%{search_term}%"))
                
                results = cursor.fetchall()
                
                if results:
                    all_results.append((search_term, results))
            
            conn.close()
            
            if not all_results:
                return f"Nenašli sa definície pre pojmy: {', '.join(search_terms)}"
            
            # Formátuj výsledky pre každý pojem
            response = ""
            
            for search_term, results in all_results:
                if response:  # Pridaj oddeľovač ak nie je prvý pojem
                    response += "\n" + "="*50 + "\n\n"
                    
                response += f"🔍 Definície pre pojem: **{search_term}**\n\n"
                
                for i, (term, definition, law_id, paragraph, confidence, category) in enumerate(results, 1):
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
