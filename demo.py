#!/usr/bin/env python3
"""
Demo script pre AI Právneho Asistenta
"""

import os
from dotenv import load_dotenv
from agent.legal_agent import create_legal_assistant

# Načítaj environment variables
load_dotenv()

def main():
    """Hlavná funkcia demo scriptu"""
    
    print("🎯 AI Právny Asistent - Demo")
    print("=" * 50)
    
    # Skontroluj API kľúče
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY nie je nastavený.")
        print("   Prosím nastavte ho v .env súbore alebo export OPENAI_API_KEY=your_key")
        print("\n💡 Pre demo môžete použiť offline funkcie agenta.")
        
        while True:
            choice = input("\nPokračovať bez OpenAI? (y/n): ").lower()
            if choice in ['y', 'yes']:
                break
            elif choice in ['n', 'no']:
                print("👋 Ukončujem demo.")
                return
    
    try:
        print("\n🔧 Inicializujem agenta...")
        agent = create_legal_assistant()
        
        print("\n📋 Dostupné nástroje:")
        for tool_info in agent.list_available_tools():
            print(f"  • {tool_info['name']}: {tool_info['description'][:50]}...")
        
        # Demo otázky
        demo_questions = [
            "Aké sú podmienky pre založenie s.r.o. na Slovensku?",
            "Analyzuj tento text: 'Podľa § 40 Občianskeho zákonníka vlastníctvo je právo na vlastnú vec.'",
            "Vyhľadaj informácie o občianskom zákonníku"
        ]
        
        print(f"\n🤖 Demo s {len(demo_questions)} otázkami:")
        print("=" * 50)
        
        for i, question in enumerate(demo_questions, 1):
            print(f"\n{i}. Otázka: {question}")
            print("-" * 40)
            
            try:
                result = agent.ask(question)
                
                if result["success"]:
                    print("✅ Odpoveď:")
                    print(result["answer"])
                else:
                    print("❌ Chyba:")
                    print(result["answer"])
                    
            except Exception as e:
                print(f"❌ Chyba pri spracovaní: {e}")
            
            # Pauza medzi otázkami
            if i < len(demo_questions):
                input("\nStlačte Enter pre pokračovanie...")
        
        print("\n🎉 Demo dokončené!")
        print("\n💡 Pre spustenie web aplikácie použite:")
        print("   streamlit run app.py")
        
    except Exception as e:
        print(f"❌ Chyba pri inicializácii agenta: {e}")
        print("\n🔍 Možné riešenia:")
        print("  1. Skontrolujte API kľúče v .env súbore")
        print("  2. Overte či sú nainštalované všetky závislosti")
        print("  3. Skontrolujte internetové pripojenie")


if __name__ == "__main__":
    main()
