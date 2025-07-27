#!/usr/bin/env python3
"""
Demo jednoduchých funkcionalít bez potreby OpenAI API
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

    # Hlavná slučka
    while True:
        print("\n" + "="*50)
        try:
            choice = input("Vyberte funkciu (1-2): ").strip()
            
            if choice == "1":
                print("\n🗄️ VYHĽADÁVANIE V DATABÁZE PRÁVNYCH POJMOV")
                print("-" * 40)
                query = input("Vložte hľadaný pojem: ")
                if query.strip():
                    result = term_search._run(query)
                    print(f"\n📚 Výsledky:\n{result}")
                else:
                    print("⚠️ Nevložili ste hľadaný pojem.")
            
            elif choice == "2":
                print("\n👋 Ďakujeme za používanie AI právneho asistenta!")
                break
            
            else:
                print("⚠️ Neplatná voľba. Zadajte číslo 1 alebo 2.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Demo ukončené používateľom.")
            break
        except Exception as e:
            print(f"❌ Chyba: {e}")

if __name__ == "__main__":
    main()
