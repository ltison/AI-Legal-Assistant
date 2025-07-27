#!/usr/bin/env python3
"""
Test analýzy konkrétneho právneho textu
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_contract_analysis():
    """Test analýzy príkaznej zmluvy"""
    print("🔍 Test analýzy príkaznej zmluvy")
    print("=" * 50)
    
    # Ukážkový text zmluvy
    contract_text = """
    PRÍKAZNÁ ZMLUVA č. 2025/59
    
    Príkazca: Slovenská akreditačná agentúra pre vysoké školstvo
    Príkazník: dr.h.c. prof. Ing. Tatiana Čorejová, PhD.
    
    Článok I. - Predmet zmluvy
    Príkazník sa zaväzuje vykonávať posudzovateľskú činnosť v rámci pracovných skupín agentúry podľa § 40 Občianskeho zákonníka.
    
    Článok II. - Odmena
    Za vykonanie činnosti podľa článku I. sa príkazníkovi poskytne odmena vo výške 605 EUR.
    Odmena je splatná do 30 dní od prijatia rozhodnutia výkonnou radou agentúry.
    
    Článok III. - Záverečné ustanovenia
        Zmluva nadobúda platnosť dňom jej podpisu a účinnosť dňom nasledujúcim po zverejnení v Centrálnom registri zmlúv.
    """
    
    # Test s legal_term_search
    print("\n1️⃣ Test s LegalTermSearchTool:")
    try:
        from agent.tools.database_tools import LegalTermSearchTool
        term_search = LegalTermSearchTool()
        result = term_search._run("zmluva")
        print("✅ Vyhľadávanie pojmu 'zmluva':")
        print(result[:300] + "...")
        
    except Exception as e:
        print(f"❌ Chyba: {e}")
    
    # Test s AI agentom ak je OpenAI dostupné
    print("\n2️⃣ Test s AI agentom:")
    try:
        if os.getenv("OPENAI_API_KEY"):
            from agent.legal_agent import create_legal_assistant
            agent = create_legal_assistant()
            
            question = f"Analyzuj tento právny text: {contract_text}"
            result = agent.ask(question)
            
            print("✅ AI Agent odpoveď:")
            print(result["answer"])
        else:
            print("⚠️ OPENAI_API_KEY nie je nastavený - preskakujem AI test")
    except Exception as e:
        print(f"❌ Chyba s AI agentom: {e}")
    
    # Test fallback funkcionality
    print("\n3️⃣ Test fallback funkcionality:")
    try:
        from agent.legal_agent import LegalAssistantAgent
        
        # Simuluj zlyhanie hlavného agenta
        class MockAgent(LegalAssistantAgent):
            def __init__(self):
                self.conversation_history = []
            
            def _fallback_response(self, question):
                return super()._fallback_response(question)
        
        mock_agent = MockAgent()
        result = mock_agent._fallback_response(contract_text)
        print("✅ Fallback odpoveď:")
        print(result[:500] + "...")
        
    except Exception as e:
        print(f"❌ Chyba s fallback: {e}")

def test_specific_questions():
    """Test konkrétnych otázok"""
    print("\n\n🎯 Test konkrétnych právnych otázok")
    print("=" * 50)
    
    questions = [
        "Aké sú podmienky pre založenie s.r.o. na Slovensku?",
        "Analyzuj § 40 Občianskeho zákonníka",
        "Nájdi informácie o nájomných zmluvách"
    ]
    
    try:
        from agent.tools.database_tools import LegalTermSearchTool
        
        term_tool = LegalTermSearchTool()
        
        for i, question in enumerate(questions, 1):
            print(f"\n{i}. {question}")
            print("-" * 40)
            
            # Pre všetky otázky použijeme vyhľadávanie v databáze pojmov
            if "s.r.o." in question.lower():
                result = term_tool._run("spoločnosť s ručením obmedzeným")
            elif "nájdi" in question.lower():
                result = term_tool._run("nájom")
            elif "zákonník" in question.lower():
                result = term_tool._run("občiansky zákonník")
            else:
                result = term_tool._run("zmluva")
            
            print(result[:300] + "..." if len(result) > 300 else result)
            
    except Exception as e:
        print(f"❌ Chyba: {e}")

def main():
    """Hlavná testovacia funkcia"""
    print("🧪 Test analýzy právnych textov a fallback funkcionalít")
    print("=" * 60)
    
    test_contract_analysis()
    test_specific_questions()
    
    print("\n🎉 Test dokončený!")
    print("\n💡 Tip: Pre plnú funkcionalnost nastavte OPENAI_API_KEY")

if __name__ == "__main__":
    main()
