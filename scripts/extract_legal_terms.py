"""
Skript na extrahovanie právnych pojmov z textov zákonov pomocí OpenAI API
"""

import os
import json
import sqlite3
import re
from typing import List, Dict, Tuple
from pathlib import Path
import sys

# Pridaj project root do Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv()
    OPENAI_AVAILABLE = True
except ImportError:
    print("❌ OpenAI knižnica nie je dostupná")
    OPENAI_AVAILABLE = False


class LegalTermExtractor:
    """Extrahuje právne pojmy z textov zákonov pomocí OpenAI API"""
    
    def __init__(self, data_dir: str = "data/law_texts", db_path: str = "data/legal_terms.db"):
        self.data_dir = Path(data_dir)
        self.db_path = Path(db_path)
        
        # Vytvor adresár pre databázu ak neexistuje
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Inicializuj OpenAI klienta
        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            print("✅ OpenAI klient inicializovaný")
        else:
            self.client = None
            print("❌ OpenAI API key nie je nastavený")
        
        # Inicializuj databázu
        self.init_database()
    
    def init_database(self):
        """Vytvorí SQL databázu pre právne pojmy"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Vytvor tabuľku pre právne pojmy
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS legal_terms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    term TEXT NOT NULL,
                    definition TEXT NOT NULL,
                    law_id TEXT NOT NULL,
                    paragraph TEXT,
                    context TEXT,
                    confidence REAL DEFAULT 0.0,
                    category TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(term, law_id, paragraph)
                )
            ''')
            
            # Index pre rýchlejšie vyhľadávanie
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_term ON legal_terms(term)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_law_id ON legal_terms(law_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON legal_terms(category)')
            
            conn.commit()
            conn.close()
            print("✅ SQL databáza inicializovaná")
            
        except Exception as e:
            print(f"❌ Chyba pri inicializácii databázy: {e}")
    
    def load_metadata(self) -> Dict:
        """Načíta metadáta súborov"""
        metadata_path = self.data_dir / "files_metadata.json"
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Chyba pri načítaní metadát: {e}")
            return {"files": []}
    
    def chunk_text_for_ai(self, text: str, chunk_size: int = 2000) -> List[str]:
        """Rozdelí text na chunky vhodné pre OpenAI API"""
        # Rozdeľ podľa paragrafov
        paragraphs = re.split(r'(§\s*\d+[a-z]*)', text)
        
        chunks = []
        current_chunk = ""
        current_paragraph = ""
        
        for i, part in enumerate(paragraphs):
            # Je to paragraf?
            if re.match(r'§\s*\d+[a-z]*', part.strip()):
                current_paragraph = part.strip()
                # Ak by chunk bol príliš veľký, ulož ho
                if len(current_chunk) > chunk_size:
                    if current_chunk.strip():
                        chunks.append(current_chunk.strip())
                    current_chunk = current_paragraph + "\n"
                else:
                    current_chunk += current_paragraph + "\n"
            else:
                # Je to obsah paragrafu
                if len(current_chunk + part) > chunk_size and current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = current_paragraph + "\n" + part
                else:
                    current_chunk += part
        
        # Pridaj posledný chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def extract_terms_with_ai(self, text_chunk: str, law_info: Dict) -> List[Dict]:
        """Extrahuje právne pojmy z textu pomocí OpenAI"""
        if not self.client:
            return []
        
        try:
            # Prompt pre GPT-4o-mini
            prompt = f"""
Analyzuj tento text zo slovenského zákona a extrahuj všetky právne pojmy a ich definície.

ZÁKON: {law_info['title']} ({law_info['law_id']})
KATEGÓRIA: {law_info.get('category', 'neznáma')}

TEXT:
{text_chunk}

INŠTRUKCIE:
1. Hľadaj explicitné definície (obsahujúce "rozumie sa", "znamená", "je to", "je definované ako")
2. Hľadaj implicitné definície z kontextu paragrafov
3. Ignoruj čisto procedurálne ustanovenia bez definícií
4. Pre každý pojem uveď:
   - term: presný názov pojmu (krátko)
   - definition: definícia (1-3 vety)
   - paragraph: číslo paragrafu (ak je zrejmé)
   - confidence: hodnotenie 0.0-1.0 ako si istý
   - category: typ pojmu (subjekt, činnosť, dokument, lehota, povinnosť, právo, iné)

Vráť JSON array vo formáte:
[
  {{
    "term": "názov pojmu",
    "definition": "definícia pojmu",
    "paragraph": "§ X", 
    "confidence": 0.8,
    "category": "kategória"
  }}
]

Ak nenájdeš žiadne definície, vráť prázdny array [].
"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Si expert na slovenské právo. Extraktuješ presne a správne právne pojmy a ich definície zo zákonov."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1500
            )
            
            # Parsuj odpoveď
            content = response.choices[0].message.content.strip()
            
            # Odstráň markdown bloky ak sú
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            # Parsuj JSON
            terms = json.loads(content)
            
            # Validuj a doplň dáta
            validated_terms = []
            for term_data in terms:
                if isinstance(term_data, dict) and "term" in term_data and "definition" in term_data:
                    # Doplň chýbajúce polia
                    term_data["law_id"] = law_info["law_id"]
                    term_data["context"] = text_chunk[:200] + "..." if len(text_chunk) > 200 else text_chunk
                    
                    # Validuj confidence
                    if "confidence" not in term_data:
                        term_data["confidence"] = 0.5
                    
                    validated_terms.append(term_data)
            
            return validated_terms
            
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parse error: {e}")
            print(f"Odpoveď: {content[:200]}...")
            return []
        except Exception as e:
            print(f"❌ Chyba pri volaní OpenAI API: {e}")
            return []
    
    def save_terms_to_db(self, terms: List[Dict]) -> int:
        """Uloží extrahované pojmy do databázy"""
        if not terms:
            return 0
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            saved_count = 0
            for term_data in terms:
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO legal_terms 
                        (term, definition, law_id, paragraph, context, confidence, category)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        term_data.get("term", ""),
                        term_data.get("definition", ""),
                        term_data.get("law_id", ""),
                        term_data.get("paragraph", ""),
                        term_data.get("context", ""),
                        float(term_data.get("confidence", 0.0)),
                        term_data.get("category", "iné")
                    ))
                    saved_count += 1
                except Exception as e:
                    print(f"⚠️ Chyba pri ukladaní pojmu {term_data.get('term', 'N/A')}: {e}")
            
            conn.commit()
            conn.close()
            
            return saved_count
            
        except Exception as e:
            print(f"❌ Chyba pri ukladaní do databázy: {e}")
            return 0
    
    def process_file(self, file_info: Dict) -> int:
        """Spracuje jeden súbor a extrahuje z neho pojmy"""
        filepath = self.data_dir / file_info["filename"]
        
        try:
            print(f"📖 Spracovávam: {file_info['title']} ({file_info['law_id']})")
            
            # Načítaj obsah
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Rozdeľ na chunky
            chunks = self.chunk_text_for_ai(content)
            print(f"   📄 Vytvorených {len(chunks)} chunkov na analýzu")
            
            all_terms = []
            for i, chunk in enumerate(chunks):
                print(f"   🤖 Analyzujem chunk {i+1}/{len(chunks)}...")
                
                # Extrahuj pojmy pomocí AI
                terms = self.extract_terms_with_ai(chunk, file_info)
                all_terms.extend(terms)
                
                if terms:
                    print(f"   ✅ Nájdených {len(terms)} pojmov v chunku {i+1}")
            
            # Ulož do databázy
            saved_count = self.save_terms_to_db(all_terms)
            
            print(f"   💾 Uložených {saved_count} pojmov z {file_info['law_id']}")
            return saved_count
            
        except Exception as e:
            print(f"❌ Chyba pri spracovaní {file_info['filename']}: {e}")
            return 0
    
    def extract_all_terms(self) -> int:
        """Extrahuje pojmy zo všetkých súborov"""
        if not self.client:
            print("❌ OpenAI API nie je dostupné")
            return 0
        
        metadata = self.load_metadata()
        files = metadata.get("files", [])
        
        print(f"🚀 Spúšťam extrahovanie pojmov z {len(files)} súborov")
        print("=" * 60)
        
        total_terms = 0
        for file_info in files:
            terms_count = self.process_file(file_info)
            total_terms += terms_count
        
        print("=" * 60)
        print(f"🎉 Celkovo extrahovaných {total_terms} právnych pojmov!")
        
        # Zobraz štatistiky
        self.show_statistics()
        
        return total_terms
    
    def show_statistics(self):
        """Zobrazí štatistiky databázy"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Celkový počet pojmov
            cursor.execute("SELECT COUNT(*) FROM legal_terms")
            total_count = cursor.fetchone()[0]
            
            # Počet podľa zákonov
            cursor.execute("""
                SELECT law_id, COUNT(*) as count 
                FROM legal_terms 
                GROUP BY law_id 
                ORDER BY count DESC
            """)
            by_law = cursor.fetchall()
            
            # Počet podľa kategórií
            cursor.execute("""
                SELECT category, COUNT(*) as count 
                FROM legal_terms 
                GROUP BY category 
                ORDER BY count DESC
            """)
            by_category = cursor.fetchall()
            
            print(f"\n📊 Štatistiky databázy právnych pojmov:")
            print(f"📝 Celkový počet pojmov: {total_count}")
            
            print(f"\n⚖️ Rozdelenie podľa zákonov:")
            for law_id, count in by_law:
                print(f"   {law_id}: {count} pojmov")
            
            print(f"\n🏷️ Rozdelenie podľa kategórií:")
            for category, count in by_category:
                print(f"   {category}: {count} pojmov")
            
            conn.close()
            
        except Exception as e:
            print(f"⚠️ Chyba pri získavaní štatistík: {e}")
    
    def test_search(self, search_term: str = "spoločnosť"):
        """Test vyhľadávania v databáze"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            print(f"\n🔍 Test vyhľadávania: '{search_term}'")
            
            # Fuzzy search
            cursor.execute("""
                SELECT term, definition, law_id, paragraph, confidence, category
                FROM legal_terms 
                WHERE term LIKE ? OR definition LIKE ?
                ORDER BY confidence DESC
                LIMIT 5
            """, (f"%{search_term}%", f"%{search_term}%"))
            
            results = cursor.fetchall()
            
            if results:
                for i, (term, definition, law_id, paragraph, confidence, category) in enumerate(results, 1):
                    print(f"\n{i}. {term} ({category})")
                    print(f"   📍 {law_id} {paragraph if paragraph else ''}")
                    print(f"   📝 {definition[:150]}...")
                    print(f"   🎯 Confidence: {confidence:.2f}")
            else:
                print("❌ Žiadne výsledky")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Chyba pri teste vyhľadávania: {e}")


def main():
    """Hlavná funkcia"""
    print("🚀 Extrahovanie právnych pojmov z textov zákonov")
    print("=" * 50)
    
    # Vytvor extraktor
    extractor = LegalTermExtractor()
    
    # Extrahuj pojmy
    count = extractor.extract_all_terms()
    
    if count > 0:
        # Testuj vyhľadávanie
        extractor.test_search("spoločnosť")
        extractor.test_search("vlastníctvo")
        
    else:
        print("\n❌ Žiadne pojmy neboli extrahované")


if __name__ == "__main__":
    main()
