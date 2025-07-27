"""
Skript na načítanie a chunkovanie právnych textov do ChromaDB
"""

import os
import re
import sys
import json
from typing import List, Dict, Tuple
from pathlib import Path

# Pridaj project root do Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
    CHROMADB_AVAILABLE = True
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError as e:
    print(f"❌ Chýbajúce knižnice: {e}")
    print("💡 Spustite: pip install chromadb sentence-transformers")
    CHROMADB_AVAILABLE = False
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class LegalTextLoader:
    """Načítava a spracováva právne texty do ChromaDB s optimálnym chunkovaním"""
    
    def __init__(self, data_dir: str = "data/law_texts", db_path: str = "data/vector_db"):
        self.data_dir = Path(data_dir)
        self.db_path = Path(db_path)
        
        # Nastavenia pre chunkovanie - optimalizované pre zachovanie kontextu
        self.chunk_size = 2000  # Väčšie chunky pre lepší kontext (≈500 tokenov)
        self.chunk_overlap = 400  # Veľký prekryv pre zachovanie kontextu
        self.min_chunk_size = 500  # Minimálna veľkosť chunku pre zachovanie významu
        
        if CHROMADB_AVAILABLE:
            try:
                # Inicializácia ChromaDB s lepším embedding modelom
                self.client = chromadb.PersistentClient(path=str(self.db_path))
                
                # Pokus o slovenský/multilingual model
                if SENTENCE_TRANSFORMERS_AVAILABLE:
                    try:
                        # Multilingual model s dobrou podporou slovenčiny
                        embedding_model = "paraphrase-multilingual-MiniLM-L12-v2"
                        print(f"🤖 Načítavam embedding model: {embedding_model}")
                        
                        # Vytvor embedding funkciu s normalizáciou pre konzistenciu
                        class MultilingualEmbeddingFunction:
                            def __init__(self, model_name):
                                from sentence_transformers import SentenceTransformer
                                self.model = SentenceTransformer(model_name)
                                self.model_name = model_name  # Pridaj názov modelu
                                self.name = f"multilingual-{model_name}"  # ChromaDB name atribút
                            
                            def __call__(self, input):
                                import numpy as np
                                
                                # Získaj embeddings
                                embeddings = self.model.encode(input)
                                
                                # Normalizuj pre konzistenciu
                                if len(embeddings.shape) == 1:
                                    # Jeden vektor
                                    norm = np.linalg.norm(embeddings)
                                    if norm > 0:
                                        embeddings = embeddings / norm
                                else:
                                    # Viac vektorov
                                    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
                                    embeddings = embeddings / np.maximum(norms, 1e-8)
                                
                                return embeddings.tolist()
                        
                        embedding_function = MultilingualEmbeddingFunction(embedding_model)
                        print("✅ Multilingual embedding model načítaný")
                        
                    except Exception as e:
                        print(f"⚠️ Chyba pri načítaní embedding modelu: {e}")
                        embedding_function = None
                else:
                    embedding_function = None
                
                # Vymaž existujúcu collection a vytvor novú
                try:
                    collections = self.client.list_collections()
                    for collection in collections:
                        if collection.name == "legal_documents":
                            self.client.delete_collection("legal_documents")
                            print("🗑️ Vymazaná stará collection")
                except:
                    pass
                
                # Vytvor novú collection s lepším embedding modelom
                if embedding_function:
                    self.collection = self.client.create_collection(
                        name="legal_documents",
                        embedding_function=embedding_function,
                        metadata={"description": "Slovenské a české právne predpisy - optimálne embeddingy"}
                    )
                else:
                    self.collection = self.client.create_collection(
                        name="legal_documents",
                        metadata={"description": "Slovenské a české právne predpisy"}
                    )
                
                print("✅ ChromaDB collection vytvorená s novými nastaveniami")
                
            except Exception as e:
                print(f"❌ Chyba pri inicializácii ChromaDB: {e}")
                self.client = None
                self.collection = None
        else:
            self.client = None
            self.collection = None
    
    def load_metadata(self) -> Dict[str, Dict]:
        """
        Načíta metadáta súborov z JSON súboru
        """
        metadata_path = self.data_dir / "files_metadata.json"
        if not metadata_path.exists():
            print(f"❌ Metadata súbor {metadata_path} neexistuje")
            return {}
        
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Vytvor mapping filename -> metadata
            metadata_map = {}
            for file_info in data.get('files', []):
                filename = file_info['filename']
                metadata_map[filename] = file_info
            
            print(f"✅ Načítané metadáta pre {len(metadata_map)} súborov")
            return metadata_map
            
        except Exception as e:
            print(f"❌ Chyba pri načítavaní metadát: {e}")
            return {}
    
    def smart_chunk_text(self, text: str, law_info: Dict) -> List[Dict]:
        """
        Inteligentné chunkovanie s dôrazom na zachovanie kontextu
        - Minimálne 500 tokenov (~2000 znakov) na chunk
        - Veľký prekryv pre zachovanie kontextu
        - Rešpektovanie štruktúry paragrafov ale spájanie malých
        """
        chunks = []
        
        # Najprv skús rozdeliť podľa paragrafov ale spájaj malé
        paragraph_chunks = self._chunk_by_paragraphs_contextual(text, law_info)
        
        if paragraph_chunks:
            chunks = paragraph_chunks
        else:
            # Ak nie sú paragrafy, použij kontextuálne okná
            chunks = self._contextual_window_chunk(text, law_info)
        
        # Filtrovanie príliš malých chunkov
        chunks = self._merge_small_chunks(chunks, law_info)
        
        return chunks
    
    def _chunk_by_paragraphs_contextual(self, text: str, law_info: Dict) -> List[Dict]:
        """Rozdelí text podľa paragrafov ale zachová kontext spájaním malých"""
        chunks = []
        
        # Rozdelenie podľa paragrafov (§ X)
        paragraph_pattern = r'(§\s*\d+[a-z]*(?:\s*[a-z]\))?)'
        parts = re.split(paragraph_pattern, text)
        
        current_paragraphs = []
        current_text = ""
        chunk_counter = 0
        
        for i, part in enumerate(parts):
            if re.match(paragraph_pattern, part.strip()):
                # Nový paragraf
                new_paragraph = part.strip()
                
                # Ak aktuálny chunk je dosť veľký, ulož ho
                if current_text and len(current_text) >= self.min_chunk_size:
                    chunk_counter += 1
                    chunks.append(self._create_contextual_chunk(
                        paragraphs=current_paragraphs,
                        text=current_text.strip(),
                        law_info=law_info,
                        chunk_num=chunk_counter
                    ))
                    
                    # Zachovaj prekryv - ponechaj posledný paragraf
                    if current_paragraphs:
                        last_para = current_paragraphs[-1]
                        last_para_text = self._get_paragraph_text(text, last_para)
                        current_paragraphs = [last_para]
                        current_text = f"{last_para}\n\n{last_para_text}\n\n"
                    else:
                        current_paragraphs = []
                        current_text = ""
                
                current_paragraphs.append(new_paragraph)
                
            else:
                # Text patriaci k paragrafu
                current_text += part
        
        # Ulož posledný chunk
        if current_paragraphs and current_text.strip():
            chunk_counter += 1
            chunks.append(self._create_contextual_chunk(
                paragraphs=current_paragraphs,
                text=current_text.strip(),
                law_info=law_info,
                chunk_num=chunk_counter
            ))
        
        return chunks
    
    def _contextual_window_chunk(self, text: str, law_info: Dict) -> List[Dict]:
        """Kontextuálne okná s veľkým prekryvom"""
        chunks = []
        
        # Rozdeľ na vety
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        current_chunk = ""
        chunk_num = 1
        i = 0
        
        while i < len(sentences):
            # Pridávaj vety pokým nedosiahneš cieľovú veľkosť
            while i < len(sentences) and len(current_chunk) < self.chunk_size:
                current_chunk += sentences[i] + ". "
                i += 1
            
            # Ak je chunk príliš malý, pridaj ešte vety
            while i < len(sentences) and len(current_chunk) < self.min_chunk_size:
                current_chunk += sentences[i] + ". "
                i += 1
            
            if current_chunk.strip():
                chunks.append(self._create_contextual_chunk(
                    paragraphs=[f"Časť {chunk_num}"],
                    text=current_chunk.strip(),
                    law_info=law_info,
                    chunk_num=chunk_num
                ))
                
                # Veľký prekryv - vráť sa o 1/3 textu
                overlap_chars = len(current_chunk) // 3
                overlap_text = current_chunk[-overlap_chars:]
                overlap_sentences = len(overlap_text.split('.'))
                
                i = max(0, i - overlap_sentences)
                current_chunk = ""
                chunk_num += 1
        
        return chunks
    
    def _merge_small_chunks(self, chunks: List[Dict], law_info: Dict) -> List[Dict]:
        """Spája príliš malé chunky so susednými"""
        if not chunks:
            return chunks
        
        merged_chunks = []
        i = 0
        
        while i < len(chunks):
            current_chunk = chunks[i]
            
            # Ak je chunk príliš malý a nie je posledný
            if (len(current_chunk['text']) < self.min_chunk_size and 
                i < len(chunks) - 1):
                
                # Spoj s nasledujúcim
                next_chunk = chunks[i + 1]
                
                merged_text = current_chunk['text'] + "\n\n" + next_chunk['text']
                merged_paragraphs = (current_chunk['metadata']['paragraphs'] + 
                                   next_chunk['metadata']['paragraphs'])
                
                merged_chunk = self._create_contextual_chunk(
                    paragraphs=merged_paragraphs,
                    text=merged_text,
                    law_info=law_info,
                    chunk_num=f"{current_chunk['metadata']['chunk_num']}-{next_chunk['metadata']['chunk_num']}"
                )
                
                merged_chunks.append(merged_chunk)
                i += 2  # Preskočme oba chunky
            else:
                merged_chunks.append(current_chunk)
                i += 1
        
        return merged_chunks
    
    def _get_paragraph_text(self, full_text: str, paragraph: str) -> str:
        """Extrahuje text patriaci k paragrafu"""
        # Nájdi pozíciu paragrafu v texte
        para_pos = full_text.find(paragraph)
        if para_pos == -1:
            return ""
        
        # Nájdi nasledujúci paragraf
        next_para_pattern = r'§\s*\d+[a-z]*(?:\s*[a-z]\))?'
        remaining_text = full_text[para_pos + len(paragraph):]
        
        next_match = re.search(next_para_pattern, remaining_text)
        if next_match:
            return remaining_text[:next_match.start()].strip()
        else:
            return remaining_text.strip()
    
    def _create_contextual_chunk(self, paragraphs: List[str], text: str, law_info: Dict, chunk_num) -> Dict:
        """Vytvorí chunk s kontextovými metadátami"""
        
        # Vyčisti text
        clean_text = re.sub(r'\s+', ' ', text).strip()
        
        # Vytvor unikátne ID
        para_ids = "_".join([p.replace('§', 'par').replace(' ', '_') for p in paragraphs[:3]])
        chunk_id = f"{law_info['law_id']}_{para_ids}_{chunk_num}"
        chunk_id = re.sub(r'[^\w_-]', '_', chunk_id)[:100]  # Obmedzme dĺžku
        
        # Hlavný paragraf (prvý)
        main_paragraph = paragraphs[0] if paragraphs else "N/A"
        
        return {
            "id": chunk_id,
            "text": clean_text,
            "metadata": {
                "law_id": law_info["law_id"],
                "title": law_info["title"],
                "category": law_info.get("category", ""),
                "paragraph": main_paragraph,
                "paragraphs": ", ".join(paragraphs),  # Konvertuj na string pre ChromaDB
                "filename": law_info["filename"],
                "type": "legal_text",
                "chunk_num": str(chunk_num),
                "text_length": len(clean_text),
                "chunk_method": "contextual",
                "token_estimate": len(clean_text) // 4  # Hrubý odhad tokenov
            }
        }
    
    def extract_law_title(self, text: str) -> str:
        """Extrahuje názov zákona z textu"""
        lines = text.split('\n')[:20]  # Pozri prvých 20 riadkov
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.upper() for keyword in ['ZÁKONNÍK', 'ZÁKON', 'VYHLÁŠKA']):
                if len(line) < 100:  # Rozumná dĺžka názvu
                    return line
        
        return "Neurčený právny predpis"
    
    def load_file(self, filepath: Path, metadata: Dict) -> List[Dict]:
        """Načíta a spracuje jeden súbor s kontextovým chunkovaním"""
        try:
            print(f"📖 Spracovávam: {filepath.name}")
            
            # Načítaj obsah
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Použij kontextové chunkovanie
            chunks = self.smart_chunk_text(content, metadata)
            
            # Štatistiky
            total_chars = sum(len(chunk['text']) for chunk in chunks)
            avg_chunk_size = total_chars // len(chunks) if chunks else 0
            min_chunk = min(len(chunk['text']) for chunk in chunks) if chunks else 0
            max_chunk = max(len(chunk['text']) for chunk in chunks) if chunks else 0
            
            print(f"✅ Vytvorených {len(chunks)} kontextových chunkov pre {metadata['law_id']} - {metadata['title']}")
            print(f"   📊 Veľkosť chunkov: min={min_chunk}, avg={avg_chunk_size}, max={max_chunk} znakov")
            
            return chunks
            
        except Exception as e:
            print(f"❌ Chyba pri spracovaní {filepath.name}: {e}")
            return []
    
    def clear_collection(self):
        """Vymaže všetky existujúce dáta z ChromaDB kolekcie"""
        try:
            # Získaj počet existujúcich záznamov
            count = self.collection.count()
            if count > 0:
                print(f"🗑️ Vymazávam {count} existujúcich záznamov...")
                
                # Vymaž všetky dáta
                self.collection.delete()
                print("✅ Kolekcia úspešne vymazaná")
            else:
                print("ℹ️ Kolekcia je už prázdna")
                
        except Exception as e:
            print(f"⚠️ Chyba pri vymazávaní kolekcie: {e}")

    def load_all_files(self) -> int:
        """Načíta všetky súbory pomocou JSON metadát"""
        if not CHROMADB_AVAILABLE or not self.collection:
            print("❌ ChromaDB nie je dostupné")
            return 0
        
        # Najprv vymaž existujúce dáta
        self.clear_collection()
        
        # Načítaj metadáta súborov
        metadata_map = self.load_metadata()
        if not metadata_map:
            print("❌ Žiadne metadáta súborov")
            return 0
        
        print(f"📋 Nájdených {len(metadata_map)} súborov na spracovanie")
        
        all_chunks = []
        for filename, metadata in metadata_map.items():
            filepath = self.data_dir / filename
            if filepath.exists():
                chunks = self.load_file(filepath, metadata)
                all_chunks.extend(chunks)
            else:
                print(f"⚠️ Súbor {filename} neexistuje")
        
        # Nahraj do ChromaDB s lepším batchingom
        if all_chunks:
            print(f"\n🔄 Nahrávam {len(all_chunks)} kontextových chunkov do ChromaDB...")
            
            # Priprav dáta pre ChromaDB
            ids = [chunk["id"] for chunk in all_chunks]
            documents = [chunk["text"] for chunk in all_chunks]
            metadatas = [chunk["metadata"] for chunk in all_chunks]
            
            try:
                # Pridaj nové dáta po menších dávkach pre stabilitu
                batch_size = 50  # Menšie dávky pre lepšiu stabilitu
                successful_chunks = 0
                
                for i in range(0, len(ids), batch_size):
                    batch_ids = ids[i:i+batch_size]
                    batch_docs = documents[i:i+batch_size] 
                    batch_metas = metadatas[i:i+batch_size]
                    
                    try:
                        self.collection.add(
                            ids=batch_ids,
                            documents=batch_docs,
                            metadatas=batch_metas
                        )
                        successful_chunks += len(batch_ids)
                        print(f"✅ Nahraných {successful_chunks}/{len(ids)} chunkov")
                    except Exception as e:
                        print(f"⚠️ Chyba pri batch {i//batch_size + 1}: {e}")
                        continue
                
                if successful_chunks > 0:
                    print(f"🎉 Úspešne nahraných {successful_chunks} kontextových chunkov!")
                    
                    # Zobraz štatistiky
                    self.show_statistics()
                    
                    return successful_chunks
                else:
                    print("❌ Žiadne chunky neboli úspešne nahrané")
                    return 0
                
            except Exception as e:
                print(f"❌ Kritická chyba pri nahrávaní do ChromaDB: {e}")
                return 0
        
        return 0
    
    def show_statistics(self):
        """Zobrazí štatistiky nahraných dát"""
        if not self.collection:
            return
        
        try:
            count = self.collection.count()
            print(f"\n📊 Štatistiky ChromaDB:")
            print(f"📝 Celkový počet chunkov: {count}")
            
            # Skús získať vzorku dát
            sample = self.collection.get(limit=5)
            if sample and sample['metadatas']:
                laws = set()
                paragraphs = 0
                for meta in sample['metadatas']:
                    if 'law_id' in meta:
                        laws.add(meta['law_id'])
                    if 'paragraph' in meta and meta['paragraph'].startswith('§'):
                        paragraphs += 1
                
                print(f"⚖️ Zákony v databáze: {', '.join(sorted(laws))}")
                print(f"📖 Paragrafy vo vzorke: {paragraphs}/{len(sample['metadatas'])}")
                
        except Exception as e:
            print(f"⚠️ Chyba pri získavaní štatistík: {e}")
    
    def test_search(self, query: str = "vlastníctvo"):
        """Testuje vyhľadávanie v nahraných dátach"""
        if not self.collection:
            print("❌ Databáza nie je dostupná")
            return
        
        try:
            print(f"\n🔍 Test vyhľadávania: '{query}'")
            results = self.collection.query(
                query_texts=[query],
                n_results=3
            )
            
            if results['documents'] and results['documents'][0]:
                for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                    print(f"\n{i+1}. {meta.get('law_id', 'N/A')} - {meta.get('paragraph', 'N/A')}")
                    print(f"   {doc[:200]}...")
            else:
                print("❌ Žiadne výsledky")
                
        except Exception as e:
            print(f"❌ Chyba pri teste: {e}")


def main():
    """Hlavná funkcia"""
    print("🚀 Načítavanie právnych textov do ChromaDB")
    print("=" * 50)
    
    # Vytvor loader
    loader = LegalTextLoader()
    
    # Načítaj všetky súbory
    count = loader.load_all_files()
    
    if count > 0:
        print(f"\n✅ Úspešne načítaných {count} chunkov!")
        
        # Test vyhľadávania
        loader.test_search("vlastníctvo")
        loader.test_search("spoločnosť s ručením obmedzeným")
        
    else:
        print("\n❌ Žiadne dáta neboli načítané")


if __name__ == "__main__":
    main()
