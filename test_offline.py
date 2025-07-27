#!/usr/bin/env python3
"""
Test offline funkcionalít bez potreby OpenAI API
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import nástrojov na úrovni modulu
from agent.tools.database_tools import LegalTermSearchTool
from agent.tools.enhanced_vector_search import EnhancedVectorSearchTool

def test_imports():
    """Test importov všetkých modulov"""
    print("🧪 Test importov...")
    
    try:
        # Test základných importov už sú na úrovni modulu
        print("✅ Databázové nástroje - OK")
        
        # Test offline nástrojov
        term_search = LegalTermSearchTool()
        vector_search = EnhancedVectorSearchTool()
        
        print("✅ Inicializácia nástrojov - OK")
        
        return term_search, vector_search
        
    except Exception as e:
        print(f"❌ Chyba pri importe: {e}")
        return None, None

def test_database():
    """Test databázy"""
    print("\n🗄️ Testovanie databázy právnych pojmov...")
    
    try:
        term_search = LegalTermSearchTool()
        
        # Test vyhľadávania
        result = term_search._run("občiansky zákonník")
        print("✅ Vyhľadávanie v databáze právnych pojmov:")
        print(result[:300] + "...")
        
    except Exception as e:
        print(f"❌ Chyba pri testovaní databázy: {e}")

def test_vector_search():
    """Test vektorového vyhľadávania"""
    print("\n🔍 Testovanie vektorového vyhľadávania...")
    
    try:
        vector_search = EnhancedVectorSearchTool()
        
        # Test sémantického vyhľadávania
        result = vector_search._run("nájomná zmluva")
        print("✅ Sémantické vyhľadávanie:")
        print(result[:300] + "...")
        
    except Exception as e:
        print(f"❌ Chyba pri vektorovom vyhľadávaní: {e}")

def main():
    """Hlavná testovacia funkcia"""
    print("🧪 Test offline funkcionalít AI právneho asistenta")
    print("=" * 60)
    
    # Test všetkých funkcionalít
    tools = test_imports()
    
    if tools[0] is not None:
        test_database()
        test_vector_search()
        
        print("\n✅ Všetky offline testy dokončené!")
        print("💡 Ak máte problémy, skontrolujte:")
        print("   - Je databáza vytvorená? (scripts/extract_legal_terms.py)")
        print("   - Je ChromaDB pripravená? (scripts/load_data.py)")
        print("   - Sú nainštalované dependencies? (pip install -r requirements.txt)")
        
    else:
        print("\n❌ Testy zlyhali kvôli problémom s importmi")

if __name__ == "__main__":
    main()
