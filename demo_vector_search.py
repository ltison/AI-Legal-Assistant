"""
Demo script na testovanie nahraných právnych textov v ChromaDB
"""

import sys
import os
from pathlib import Path

# Pridaj project root do Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from agent.legal_agent import create_legal_assistant


def demo_vector_search():
    """Demo rôznych vyhľadávaní v nahraných textoch"""
    
    print("🎯 DEMO: AI Právny Asistent s nahranými textmi")
    print("=" * 60)
    
    try:
        # Vytvor agenta
        agent = create_legal_assistant()
        
        # Test otázky na demonštráciu
        test_questions = [
            {
                "question": "Čo je to vlastníctvo podľa Občianskeho zákonníka?",
                "description": "Základná definícia vlastníctva"
            },
            {
                "question": "Aké sú podmienky pre založenie s.r.o.?", 
                "description": "Informácie o spoločnosti s ručením obmedzeným"
            },
            {
                "question": "Ako funguje vydržanie v občianskom práve?",
                "description": "Spôsob nadobudnutia vlastníctva"
            },
            {
                "question": "Analyzuj paragraf 40 Občianskeho zákonníka",
                "description": "Konkrétny právny text"
            }
        ]
        
        for i, test in enumerate(test_questions, 1):
            print(f"\n📋 Test {i}: {test['description']}")
            print("-" * 50)
            print(f"❓ Otázka: {test['question']}")
            
            try:
                result = agent.ask(test['question'])
                
                if result['success']:
                    answer = result['answer']
                    print(f"✅ Odpoveď: {answer[:400]}{'...' if len(answer) > 400 else ''}")
                    
                    # Zobraz intermediate steps ak sú zaujímavé
                    if result.get('intermediate_steps'):
                        used_tools = []
                        for step in result['intermediate_steps']:
                            if hasattr(step, 'tool') and step.tool not in used_tools:
                                used_tools.append(step.tool)
                        if used_tools:
                            print(f"🔧 Použité nástroje: {', '.join(used_tools)}")
                else:
                    print(f"❌ Chyba: {result['answer']}")
                    
            except Exception as e:
                print(f"❌ Chyba pri testovaní: {e}")
            
            print()  # Prázdny riadok
        
        # Štatistiky
        print("\n📊 Informácie o nahraných dátach:")
        print("-" * 50)
        
        # Získaj vector tool a zobraz štatistiky
        for tool in agent.tools:
            if tool.name == "vector_search" and hasattr(tool, 'collection') and tool.collection:
                try:
                    count = tool.collection.count()
                    print(f"📝 Celkový počet chunkov v ChromaDB: {count}")
                    
                    # Ukážkové vyhľadávanie pre štatistiky
                    sample_results = tool.collection.query(
                        query_texts=["zákon"],
                        n_results=10
                    )
                    
                    if sample_results['metadatas']:
                        laws = set()
                        for meta in sample_results['metadatas'][0]:
                            if 'law_id' in meta:
                                laws.add(meta['law_id'])
                        
                        print(f"⚖️ Dostupné zákony: {', '.join(sorted(laws))}")
                    
                except Exception as e:
                    print(f"⚠️ Chyba pri získavaní štatistík: {e}")
                break
        else:
            print("❌ Vector search nástroj nie je dostupný")
            
    except Exception as e:
        print(f"❌ Chyba pri inicializácii agenta: {e}")


def main():
    """Hlavná funkcia"""
    
    # Skontroluj či existuje ChromaDB
    db_path = Path("data/vector_db")
    if not db_path.exists():
        print("❌ ChromaDB databáza neexistuje!")
        print("💡 Spustite najprv: python scripts/load_law_texts.py")
        return
    
    demo_vector_search()
    
    print("\n🎉 Demo dokončené!")
    print("\n💡 Pre spustenie web aplikácie použite:")
    print("   streamlit run app.py")


if __name__ == "__main__":
    main()
