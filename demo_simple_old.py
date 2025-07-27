#!/usr/bin/env python3
"""
Jednoduchá demo aplikácia bez OpenAI závislosti
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.tools.database_tools import LegalTermSearchTool

def main():
    """Interaktívne demo bez AI"""
    print("🎯 AI Právny Asistent - Demo bez API kľúčov")
    print("=" * 50)
    
    # Inicializuj nástroje
    try:
        term_search = LegalTermSearchTool()
        
        print("✅ Nástroje úspešne načítané!")
        print("\n📋 Dostupné funkcie:")
        print("1. Vyhľadávanie v databáze právnych pojmov")
        print("2. Ukončiť")
        
    except Exception as e:
        print(f"❌ Chyba pri načítaní nástrojov: {e}")
        return
    
    while True:
        print("\n" + "="*50)
        try:
            choice = input("Vyberte funkciu (1-4): ").strip()
            
            if choice == "1":
                print("\n🔍 ANALÝZA PRÁVNEHO TEXTU")
                print("-" * 30)
                text = input("Vložte právny text na analýzu: ")
                if text.strip():
                    result = analyzer._run(text)
                    print(f"\n📊 Výsledok:\n{result}")
                else:
                    print("⚠️ Nevložili ste žiadny text.")
            
            elif choice == "2":
                print("\n💡 PRÁVNE PORADENSTVO")
                print("-" * 30)
                question = input("Aká je vaša právna otázka? ")
                if question.strip():
                    result = advice._run(question)
                    print(f"\n📝 Odpoveď:\n{result}")
                else:
                    print("⚠️ Nevložili ste žiadnu otázku.")
            
            elif choice == "3":
                print("\n🗄️ VYHĽADÁVANIE V DATABÁZE PRÁVNYCH POJMOV")
                print("-" * 40)
                query = input("Vložte hľadaný pojem: ")
                if query.strip():
                    result = term_search._run(query)
                    print(f"\n📚 Výsledky:\n{result}")
                else:
                    print("⚠️ Nevložili ste hľadaný pojem.")
            
            elif choice == "4":
                print("\n👋 Ďakujem za použitie AI Právneho Asistenta!")
                break
            
            else:
                print("⚠️ Neplatná voľba. Zvoľte číslo 1-4.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Ukončujem aplikáciu...")
            break
        except Exception as e:
            print(f"❌ Chyba: {e}")
    
    print("\n🎉 Aplikácia ukončená.")

if __name__ == "__main__":
    main()
