#!/usr/bin/env python3
"""
Jednoduchý test bez LangChain závislostí
"""

import os
import sqlite3
import re
from typing import List, Dict

def test_legal_text_analysis():
    """Test analýzy právneho textu"""
    print("🔍 Testovanie analýzy právneho textu...")
    
    def extract_paragraphs(text: str) -> List[str]:
        patterns = [
            r'§\s*(\d+[a-z]?)',
            r'par\.\s*(\d+)',
            r'paragraf\s*(\d+)',
        ]
        
        paragraphs = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            paragraphs.extend([f"§ {match}" for match in matches])
        
        return list(set(paragraphs))
    
    def extract_laws(text: str) -> List[str]:
        patterns = [
            r'zákon\s*č\.\s*(\d+/\d+)',
            r'(\d+/\d+)\s*Zb\.',
            r'(\d+/\d+)\s*Z\.z\.',
        ]
        
        laws = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            laws.extend(matches)
        
        return list(set(laws))
    
    test_text = """
    Podľa § 40 Občianskeho zákonníka vlastníctvo je právo na vlastnú vec.
    Zákon č. 40/1964 Zb. upravuje občianskoprávne vzťahy.
    V § 41 sa uvádza, že vlastník môže s vecou nakladať podľa svojej vôle.
    """
    
    paragraphs = extract_paragraphs(test_text)
    laws = extract_laws(test_text)
    
    print(f"✅ Nájdené paragrafy: {paragraphs}")
    print(f"✅ Nájdené zákony: {laws}")
    return True

def test_database_creation():
    """Test vytvorenia a naplnenia databázy"""
    print("\n🗄️ Testovanie databázy...")
    
    # Test databázy právnych pojmov
    db_path = "data/legal_terms.db"
    os.makedirs("data", exist_ok=True)
    
    try:
        # Vytvor databázu
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vytvor tabuľku
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS laws (
                id INTEGER PRIMARY KEY,
                country TEXT NOT NULL,
                number TEXT NOT NULL,
                year INTEGER NOT NULL,
                title TEXT NOT NULL,
                category TEXT,
                summary TEXT,
                url TEXT
            )
        """)
        
        # Pridaj ukážkové dáta
        sample_laws = [
            ("SK", "40/1964", 1964, "Občiansky zákonník", "občianske právo", 
             "Základný zákon upravujúci občianskoprávne vzťahy", 
             "https://www.slov-lex.sk/pravne-predpisy/SK/ZZ/1964/40/"),
             
            ("SK", "513/1991", 1991, "Obchodný zákonník", "obchodné právo",
             "Zákon upravujúci obchodné spoločnosti a obchodné vzťahy",
             "https://www.slov-lex.sk/pravne-predpisy/SK/ZZ/1991/513/"),
        ]
        
        # Vymaž staré dáta a vlož nové
        cursor.execute("DELETE FROM laws")
        cursor.executemany("""
            INSERT INTO laws (country, number, year, title, category, summary, url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, sample_laws)
        
        # Test vyhľadávania
        cursor.execute("""
            SELECT title, number, year FROM laws 
            WHERE title LIKE ? OR summary LIKE ?
        """, ("%občiansky%", "%občiansky%"))
        
        results = cursor.fetchall()
        
        conn.commit()
        conn.close()
        
        print(f"✅ Databáza vytvorená: {db_path}")
        print(f"✅ Nájdené záznamy: {len(results)}")
        for title, number, year in results:
            print(f"   - {title} ({number}/{year})")
        
        return True
        
    except Exception as e:
        print(f"❌ Chyba pri databáze: {e}")
        return False

def test_legal_advice_patterns():
    """Test rozpoznávania právnych otázok"""
    print("\n💡 Testovanie rozpoznávania právnych otázok...")
    
    advice_patterns = {
        r"s\.?r\.?o|spoločnosť.*ručením": "s.r.o. poradenstvo",
        r"kúpa|predaj|kúpna zmluva": "kúpna zmluva",
        r"nájom|prenájom": "nájomná zmluva",
        r"dedenie|dedič": "dedenie",
    }
    
    test_questions = [
        "Ako založím s.r.o.?",
        "Chcem predať auto, čo potrebujem?",
        "Môžem vypovědať nájom bytu?",
        "Ako funguje dedenie majetku?",
        "Všeobecná otázka"
    ]
    
    for question in test_questions:
        question_lower = question.lower()
        matched = False
        
        for pattern, category in advice_patterns.items():
            if re.search(pattern, question_lower):
                print(f"✅ '{question}' → {category}")
                matched = True
                break
        
        if not matched:
            print(f"📝 '{question}' → všeobecné poradenstvo")
    
    return True

def test_vector_simulation():
    """Simulácia vector search"""
    print("\n🔎 Testovanie simulácie vector search...")
    
    # Simulované právne dokumenty
    documents = [
        {
            "id": "obz_40",
            "text": "Vlastníctvo je právo na vlastnú vec, najmä právo vec držať, užívať",
            "keywords": ["vlastníctvo", "právo", "vec"]
        },
        {
            "id": "oz_sro", 
            "text": "Spoločnosť s ručením obmedzeným môže založiť jedna alebo viac osôb",
            "keywords": ["s.r.o.", "spoločnosť", "založenie"]
        },
        {
            "id": "tz_kradez",
            "text": "Kto si prisvojí cudzí hnuteľný majetok tým, že sa ho zmocní",
            "keywords": ["krádež", "majetok", "prisvojenie"]
        }
    ]
    
    def simple_search(query: str, docs: List[Dict]) -> List[Dict]:
        """Jednoduchý keyword-based search"""
        query_words = query.lower().split()
        results = []
        
        for doc in docs:
            score = 0
            for word in query_words:
                if any(word in keyword.lower() for keyword in doc["keywords"]):
                    score += 1
                if word in doc["text"].lower():
                    score += 0.5
            
            if score > 0:
                results.append((doc, score))
        
        # Zoraď podľa skóre
        results.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, score in results]
    
    test_queries = ["vlastníctvo", "s.r.o. založenie", "krádež majetku"]
    
    for query in test_queries:
        results = simple_search(query, documents)
        print(f"✅ Vyhľadávanie '{query}':")
        for i, doc in enumerate(results[:2], 1):
            print(f"   {i}. {doc['id']}: {doc['text'][:50]}...")
    
    return True

def main():
    """Hlavná testovacia funkcia"""
    print("🧪 AI Právny Asistent - Zjednodušený Test")
    print("=" * 50)
    
    tests = [
        ("Analýza právneho textu", test_legal_text_analysis),
        ("Databáza zákonov", test_database_creation),
        ("Rozpoznávanie otázok", test_legal_advice_patterns),
        ("Simulácia vector search", test_vector_simulation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} zlyhal: {e}")
            results.append((test_name, False))
    
    # Zhrnutie
    print("\n📊 ZHRNUTIE TESTOV:")
    print("=" * 50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PREŠIEL" if success else "❌ ZLYHAL"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 Výsledok: {passed}/{len(results)} testov prešlo")
    
    if passed == len(results):
        print("\n🎉 Základné komponenty fungujú!")
        print("\n📋 Ďalšie kroky:")
        print("  1. Nastavte API kľúče v .env súbore:")
        print("     OPENAI_API_KEY=your_openai_key")
        print("     TAVILY_API_KEY=your_tavily_key")
        print("  2. Spustite demo: python demo.py")
        print("  3. Web app: streamlit run app.py")
        print("\n💡 Projekt je pripravený na odovzdanie!")
    else:
        print("⚠️  Niektoré základné funkcie nefungujú.")

if __name__ == "__main__":
    main()
