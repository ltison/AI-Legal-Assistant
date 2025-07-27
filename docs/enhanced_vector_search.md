# Enhanced Vector Search - Dokumentácia

## Prehľad

Enhanced Vector Search je pokročilý vyhľadávací nástroj, ktorý kombinuje sémantické a fulltext vyhľadávanie v databáze slovenských zákonov. Nahradil pôvodný `VectorSearchTool` a poskytuje rozšírené možnosti vyhľadávania.

## Kľúčové funkcie

### ✅ Podporované typy vyhľadávania:

1. **Sémantické vyhľadávanie** - tradičné vector search
2. **Fulltext search** - textové vyhľadávanie v dokumentoch  
3. **Regex vyhľadávanie** - pattern matching
4. **Kombinované dotazy** - metadáta + text
5. **Negácia** - vylučovanie textu

## Formáty dotazov

### 1. Sémantické vyhľadávanie (predvolené)
```python
"povinnosti konateľa"
"práva vlastníka"
"zmluva o dielo"
```

### 2. Fulltext search
```python
# Obsahuje text
"contains:spoločnosť"
"contains:súdne konanie"

# Neobsahuje text
"not_contains:fyzická osoba"
"not_contains:trestný čin"
```

### 3. Regex vyhľadávanie
```python
# Paragrafové čísla
"regex:§\\s*135[a-z]*"

# Právne predpisy
"regex:[0-9]+/[0-9]+ Zb"

# Dátumy
"regex:[0-9]{1,2}\\.[0-9]{1,2}\\.[0-9]{4}"
```

### 4. Kombinované dotazy
```python
# Filter podľa zákona + text
"law:513/1991 contains:súd"
"law:40/1964 contains:vlastníctvo"

# Filter + sémantické vyhľadávanie  
"law:300/2005 trestný čin"

# Filter + regex
"law:513/1991 regex:§\\s*[0-9]+"
```

## Dostupné zákony

- **40/1964** - Občianský zákonník
- **513/1991** - Obchodný zákonník  
- **530/2003** - Zákon o správnom súdnictve
- **300/2005** - Trestný zákon
- **160/2015** - Civilný sporový poriadok
- **161/2015** - Civilný mimosporový poriadok

## Technické detaily

### Embedding Model
- **Model:** `paraphrase-multilingual-MiniLM-L12-v2`
- **Jazyk:** Optimalizovaný pre slovenčinu
- **Normalizácia:** L2 normalizácia vektorov
- **Dimenzie:** 384

### Chunking Strategy
- **Veľkosť:** 2000 znakov s 400 znakmi prekrytia
- **Minimum:** 500 tokenov na chunk
- **Kontextové:** Zachováva súvislosti medzi paragrafmi
- **Spolu:** 3120 optimalizovaných chunkov

### Výkonnosť
- **Sémantické vyhľadávanie:** ~50-60% podobnosť pre relevanté výsledky
- **Fulltext search:** Presné zhody v texte
- **Kombinované:** Deduplication a ranking

## Príklady použitia

### Základné vyhľadávanie
```python
from agent.tools.enhanced_vector_search import EnhancedVectorSearchTool

tool = EnhancedVectorSearchTool()

# Sémantické
result = tool._run("povinnosti konateľa s.r.o.")

# Fulltext  
result = tool._run("contains:spoločnosť")

# Kombinované
result = tool._run("law:513/1991 contains:konateľ")
```

### V rámci agenta
```python
from agent.legal_agent import LegalAssistantAgent

agent = LegalAssistantAgent()
response = agent.ask("Nájdi všetky spomienky slova 'súd' v obchodnom zákonníku")
```

## Porovnanie s pôvodným VectorSearchTool

| Funkcia | VectorSearchTool | EnhancedVectorSearchTool |
|---------|------------------|-------------------------|
| Sémantické vyhľadávanie | ✅ | ✅ |
| Fulltext search | ❌ | ✅ |
| Regex vyhľadávanie | ❌ | ✅ |
| Kombinované dotazy | ❌ | ✅ |
| Metadáta filtering | ❌ | ✅ |
| Query parsing | ❌ | ✅ |
| Deduplication | ❌ | ✅ |

## Obmedzenia

### ChromaDB limitácie:
- Žiadne fuzzy matching
- Žiadne stemming/lemmatizácia
- Žiadne automatické OR/AND operátory
- Case-sensitive vyhľadávanie
- Žiadne ranking podľa textovej relevantnosti

### Možné riešenia:
Pre pokročilejšie fulltext funkcie odporúčame:
- **Elasticsearch** - pokročilé fulltext možnosti
- **PostgreSQL FTS** - full-text search s podporou slovenčiny
- **Solr** - enterprise search platform

## Migrácia z VectorSearchTool

Enhanced Vector Search je **plne kompatibilný** s pôvodným nástrojom:

```python
# Pôvodný kód
vector_search = VectorSearchTool()
result = vector_search._run("povinnosti konateľa")

# Nový kód - identické výsledky
enhanced_search = EnhancedVectorSearchTool()  
result = enhanced_search._run("povinnosti konateľa")
```

Dodatočne získate všetky nové fulltext možnosti bez zmeny existujúceho kódu!
