"""
Rozšírený vector search s fulltext možnosťami
"""

from typing import List, Dict, Any, Optional, Type, Union
from langchain.tools import BaseTool
from pydantic import Field
import re

# Fallback pre ChromaDB ak nie je dostupné
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


class EnhancedVectorSearchTool(BaseTool):
    """Rozšírený vector search s podporou fulltext vyhľadávania"""
    
    name: str = "enhanced_vector_search"
    description: str = """
    Pokročilý vyhľadávací nástroj kombinujúci sémantické vyhľadávanie a fulltext search v databáze slovenských zákonov.
    
    Podporované formáty dotazov:
    1. Sémantické vyhľadávanie: "povinnosti konateľa"
    2. Fulltext search: "contains:spoločnosť"
    3. Regex vyhľadávanie: "regex:§\\s*135[a-z]*"
    4. Kombinované: "law:513/1991 contains:súd" (hľadá text "súd" len v zákone 513/1991)
    5. Negácia: "not_contains:fyzická osoba"
    
    Databáza obsahuje: 40/1964, 513/1991, 530/2003, 300/2005, 160/2015, 161/2015
    
    Input: vyhľadávací dotaz s voliteľnými prefixmi (string)
    """
    
    # Pydantic fields
    collection_name: str = Field(default="legal_documents")
    client: Optional[Any] = Field(default=None, exclude=True)
    collection: Optional[Any] = Field(default=None, exclude=True)
    embedding_function: Optional[Any] = Field(default=None, exclude=True)
    
    def __init__(self, collection_name: str = "legal_documents", **kwargs):
        super().__init__(collection_name=collection_name, **kwargs)
        if CHROMADB_AVAILABLE:
            try:
                # Vytvor PRESNE ROVNAKÝ embedding model ako pri vytváraní databázy
                try:
                    from sentence_transformers import SentenceTransformer
                    
                    # Vytvor embedding funkciu IDENTICKÚ s load_law_texts.py
                    class MultilingualEmbeddingFunction:
                        def __init__(self, model_name):
                            from sentence_transformers import SentenceTransformer
                            self.model = SentenceTransformer(model_name)
                            self.model_name = model_name
                            self.name = f"multilingual-{model_name}"
                        
                        def __call__(self, input):
                            import numpy as np
                            
                            # Získaj embeddings
                            embeddings = self.model.encode(input)
                            
                            # Normalizuj PRESNE ako v load_law_texts.py
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
                    
                    # Používame PRESNE ROVNAKÝ model ako v databáze
                    self.embedding_function = MultilingualEmbeddingFunction("paraphrase-multilingual-MiniLM-L12-v2")
                    
                    self.client = chromadb.PersistentClient(path="data/vector_db")
                    print("✅ Enhanced Vector Search s multilingual embedding modelom")
                    
                except ImportError:
                    print("❌ Sentence transformers nie sú dostupné")
                    self.client = None
                    self.embedding_function = None
                
                self._init_collection()
            except Exception as e:
                print(f"❌ Chyba pri inicializácii Enhanced Vector Search: {e}")
                self.client = None
                self.collection = None
        else:
            self.client = None
            self.collection = None
    
    def _init_collection(self):
        """Inicializuje existujúcu vector collection"""
        if not self.client:
            return
            
        try:
            collections = self.client.list_collections()
            collection_names = [col.name for col in collections]
            
            if self.collection_name not in collection_names:
                print(f"❌ Collection '{self.collection_name}' neexistuje")
                print(f"📋 Dostupné kolekcie: {collection_names}")
                self.collection = None
                return
            
            self.collection = self.client.get_collection(name=self.collection_name)
            count = self.collection.count()
            
            if count > 0:
                print(f"✅ Enhanced search pripravený s {count} dokumentmi")
            else:
                print("⚠️ Collection je prázdna")
                
        except Exception as e:
            print(f"❌ Chyba pri načítavaní collection: {e}")
            self.collection = None
    
    def _parse_query(self, query: str) -> Dict[str, Any]:
        """Parsuje pokročilé query príkazy"""
        parsed = {
            'semantic_query': None,
            'where_filters': {},
            'where_document': {},
            'search_type': 'semantic'
        }
        
        # Rozpoznaj rôzne typy dotazov
        query = query.strip()
        
        # 1. Fulltext search patterns
        if query.startswith('contains:'):
            parsed['search_type'] = 'fulltext'
            text = query[9:]  # Odstráň 'contains:'
            parsed['where_document'] = {'$contains': text}
            return parsed
        
        if query.startswith('not_contains:'):
            parsed['search_type'] = 'fulltext'
            text = query[13:]  # Odstráň 'not_contains:'
            parsed['where_document'] = {'$not_contains': text}
            return parsed
        
        if query.startswith('regex:'):
            parsed['search_type'] = 'fulltext'
            pattern = query[6:]  # Odstráň 'regex:'
            parsed['where_document'] = {'$regex': pattern}
            return parsed
        
        # 2. Kombinované queries (law:XXX contains:YYY)
        if ' ' in query and any(prefix in query for prefix in ['law:', 'contains:', 'regex:', 'not_contains:']):
            parts = query.split()
            for part in parts:
                if part.startswith('law:'):
                    parsed['where_filters']['law_id'] = part[4:]
                elif part.startswith('contains:'):
                    parsed['where_document']['$contains'] = part[9:]
                    parsed['search_type'] = 'combined'
                elif part.startswith('not_contains:'):
                    parsed['where_document']['$not_contains'] = part[13:]
                    parsed['search_type'] = 'combined'
                elif part.startswith('regex:'):
                    parsed['where_document']['$regex'] = part[6:]
                    parsed['search_type'] = 'combined'
                else:
                    # Zvyšné slová sú pre sémantické vyhľadávanie
                    if parsed['semantic_query'] is None:
                        parsed['semantic_query'] = part
                    else:
                        parsed['semantic_query'] += ' ' + part
            
            return parsed
        
        # 3. Čistý sémantický dotaz
        parsed['semantic_query'] = query
        return parsed
    
    def _fulltext_search(self, where_filters: Dict, where_document: Dict, limit: int = 5) -> List[Dict]:
        """Vykonaj fulltext search"""
        try:
            # Základný fulltext search
            kwargs = {'limit': limit, 'include': ['documents', 'metadatas']}
            
            if where_filters:
                kwargs['where'] = where_filters
            
            if where_document:
                kwargs['where_document'] = where_document
            
            results = self.collection.get(**kwargs)
            
            # Formátuj výsledky
            formatted = []
            for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
                law_id = metadata.get('law_id', 'N/A')
                paragraph = metadata.get('paragraph', 'N/A')
                title = metadata.get('title', '')
                
                formatted.append({
                    'rank': i + 1,
                    'law_id': law_id,
                    'paragraph': paragraph,
                    'title': title,
                    'text': doc,
                    'similarity': 'Fulltext match',
                    'search_type': 'fulltext'
                })
            
            return formatted
            
        except Exception as e:
            print(f"Chyba pri fulltext search: {e}")
            return []
    
    def _semantic_search(self, query: str, where_filters: Dict = None, limit: int = 5) -> List[Dict]:
        """Vykonaj sémantické vyhľadávanie"""
        try:
            if not self.embedding_function:
                return []
            
            # Vytvor embedding pre query
            query_embedding = self.embedding_function([query])
            
            # Query parameters
            kwargs = {
                'query_embeddings': query_embedding,
                'n_results': limit,
                'include': ['documents', 'metadatas', 'distances']
            }
            
            if where_filters:
                kwargs['where'] = where_filters
            
            results = self.collection.query(**kwargs)
            
            # Formátuj výsledky
            formatted = []
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                similarity = round((1 - distance) * 100, 1)
                law_id = metadata.get('law_id', 'N/A')
                paragraph = metadata.get('paragraph', 'N/A')
                title = metadata.get('title', '')
                
                formatted.append({
                    'rank': i + 1,
                    'law_id': law_id,
                    'paragraph': paragraph,
                    'title': title,
                    'text': doc,
                    'similarity': f"{similarity}%",
                    'search_type': 'semantic'
                })
            
            return formatted
            
        except Exception as e:
            print(f"Chyba pri semantic search: {e}")
            return []
    
    def _combined_search(self, parsed_query: Dict, limit: int = 5) -> List[Dict]:
        """Kombinuje sémantické a fulltext vyhľadávanie"""
        results = []
        
        # Ak máme sémantický dotaz, pridaj sémantické výsledky
        if parsed_query['semantic_query']:
            semantic_results = self._semantic_search(
                parsed_query['semantic_query'],
                parsed_query['where_filters'],
                limit // 2 + 1
            )
            results.extend(semantic_results)
        
        # Pridaj fulltext výsledky
        if parsed_query['where_document']:
            fulltext_results = self._fulltext_search(
                parsed_query['where_filters'],
                parsed_query['where_document'],
                limit // 2 + 1
            )
            results.extend(fulltext_results)
        
        # Odstráň duplikáty a obmedzi na limit
        seen_ids = set()
        unique_results = []
        for result in results:
            result_id = f"{result['law_id']}_{result['paragraph']}"
            if result_id not in seen_ids:
                seen_ids.add(result_id)
                unique_results.append(result)
                if len(unique_results) >= limit:
                    break
        
        return unique_results
    
    def _format_results(self, results: List[Dict]) -> str:
        """Formátuje výsledky do čitateľného formátu"""
        if not results:
            return "Nenašli sa žiadne relevantné dokumenty pre zadaný dotaz."
        
        formatted_results = []
        for result in results:
            formatted_results.append(
                f"**Výsledok {result['rank']}** (podobnosť: {result['similarity']}, typ: {result['search_type']})\n"
                f"Zákon: {result['law_id']} - {result['paragraph']}\n"
                f"Názov: {result['title']}\n"
                f"Text: {result['text'][:300]}{'...' if len(result['text']) > 300 else ''}\n"
            )
        
        return "\n".join(formatted_results)
    
    def _run(self, query: str) -> str:
        """Hlavná vyhľadávacia funkcia"""
        if not self.collection:
            return f"Enhanced vector search nie je dostupný - kolekcia '{self.collection_name}' neexistuje."
        
        try:
            # Parsuj dotaz
            parsed_query = self._parse_query(query)
            print(f"🔍 Parsed query: {parsed_query}")  # Debug info
            
            # Vykonaj vyhľadávanie podľa typu
            if parsed_query['search_type'] == 'semantic':
                results = self._semantic_search(parsed_query['semantic_query'])
            elif parsed_query['search_type'] == 'fulltext':
                results = self._fulltext_search(
                    parsed_query['where_filters'],
                    parsed_query['where_document']
                )
            elif parsed_query['search_type'] == 'combined':
                results = self._combined_search(parsed_query)
            else:
                return "Nerozoznaný typ dotazu."
            
            return self._format_results(results)
            
        except Exception as e:
            return f"Chyba pri enhanced vector search: {str(e)}"
    
    async def _arun(self, query: str) -> str:
        """Async verzia"""
        return self._run(query)


def get_enhanced_search_tool():
    """Vráti enhanced vector search tool"""
    return EnhancedVectorSearchTool()
