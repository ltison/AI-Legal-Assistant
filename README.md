# AI Právny Asistent

**Školský projekt pre kurz AI Agenti** - Inteligentný agent pre právo postavený na LangChain frameworku s ReAct pattern.

## 🎯 Zadanie
- **Agent:** ReAct pattern
- **Framework:** LangChain  
- **Zameranie:** Slovenské a české právo
- **Nástroje:** Tavily search, Wikipedia, ChromaDB, SQLite
- **Deadline:** 31.7.2025

## ✨ Funkcie
- 🔍 **Webové vyhľadávanie** zákonov cez Tavily API
- 📚 **Wikipedia integration** pre právne pojmy
- 💾 **SQLite databáza** slovenských/českých zákonov
- 🤖 **Enhanced Vector Search** s **3120 optimalizovanými chunkami**
- 🔎 **Fulltext search** s regex a kombinovanými dotazmi
- 🌐 **Streamlit web UI** pre interakciu

## 📊 Nahrané právne texty (optimalizované)
Systém obsahuje **3120 kontextových chunkov** (500+ tokenov) z týchto zákonov:
- **Občiansky zákonník** (40/1964) 
- **Obchodný zákonník** (513/1991)
- **Zákon o správnom súdnictve** (530/2003)
- **Trestný zákon** (300/2005)
- **Civilný sporový poriadok** (160/2015)
- **Civilný mimosporový poriadok** (161/2015)

*Pôvodne 5364 malých chunkov optimalizovaných na 3120 väčších kontextových chunkov pre lepšie výsledky vyhľadávania.*

## 🚀 Rýchly start

### 1. Virtuálne prostredie
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# alebo
venv\Scripts\activate     # Windows
```

### 2. Inštalácia
```bash
pip install -r requirements.txt
```

### 3. Generovanie databáz (prvé spustenie)
```bash
# Vygeneruje vector_db/ a legal_terms.db z textových súborov
python scripts/load_law_texts.py
python scripts/extract_legal_terms.py
```

### 4. Nastavenie API kľúčov (voliteľné)
Vytvorte `.env` súbor:
```
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key  
```

### 5. Spustenie
```bash
# Web aplikácia
streamlit run app.py

# Alebo použite helper script
./run.sh
```

## 📁 Štruktúra projektu

```
AI_Kurz_Ulohy/
├── agent/                   # Hlavný agent a nástroje
│   ├── legal_agent.py       # ReAct agent s LangChain
│   └── tools/               # Nástroje pre agenta
│       ├── search_tools.py      # Tavily + Wikipedia
│       ├── database_tools.py    # Legal terms DB + Vector DB  
│       └── legal_tools.py       # (prázdny - nástroje odstránené)
├── data/                    # Databázy a dáta
│   ├── law_texts/              # Zdrojové texty zákonov (*.txt)
│   ├── legal_terms.db*         # SQLite s právnymi pojmami (regenerovateľný)
│   └── vector_db/*             # ChromaDB pre sémantické vyhľadávanie (regenerovateľný)
├── app.py                   # Streamlit web aplikácia
├── run.sh                   # Helper script pre spustenie
├── scripts/
│   ├── load_law_texts.py    # Načítanie textov do ChromaDB
│   └── extract_legal_terms.py # AI extrahovanie pojmov do SQL
├── data/
│   ├── law_texts/           # Súbory so zákonmi (ZZ_YYYY_XXX_YYYYMMDD.txt)
│   ├── legal_terms.db       # SQLite s 6692 právnymi pojmami
│   └── vector_db/           # ChromaDB databáza (6523 chunkov)
├── requirements.txt         # Python závislosti
├── .env.example            # Príklad API kľúčov
└── README.md               # Dokumentácia
```

## � Práca s právnymi textmi

### Načítanie textov do ChromaDB
```bash
# Načítaj súbory zo zoznamu data/law_texts/files_list.txt
python scripts/load_law_texts.py
```

### Formát súborov
```
ZZ_YYYY_CISLO_DATUM.txt
Príklad: ZZ_1964_40_20241101.txt = Zákon 40/1964 z 1.11.2024
```

### Test vyhľadávania
```bash
# Otestujte databázu príkazmi v aplikácii
streamlit run app.py
```

## �🛠️ Technické detaily

### Agent Architecture
- **Pattern:** ReAct (Reasoning + Acting)
- **Framework:** LangChain 0.1.x
- **LLM:** OpenAI GPT (gpt-4o-mini)
- **Memory:** Conversation history buffer

### Nástroje (Tools)
1. **TavilySearchTool** - Webové vyhľadávanie právnych info
2. **LegalWikipediaTool** - Wikipedia pre SK/CZ právne pojmy  
3. **LegalTermSearchTool** - SQL databáza s právnymi pojmami
4. **EnhancedVectorSearchTool** - ChromaDB s pokročilým vyhľadávaním
   - ✅ Sémantické vyhľadávanie
   - ✅ Fulltext search (`contains:`, `not_contains:`)
   - ✅ Regex vyhľadávanie (`regex:pattern`)
   - ✅ Kombinované dotazy (`law:513/1991 contains:súd`)
   - ✅ Metadáta filtering

### Databázy
- **SQLite legal_terms.db:** Extrahované právne pojmy s definíciami
- **ChromaDB:** Vector store s **3120 optimalizovanými chunkami**
- **Embedding model:** `paraphrase-multilingual-MiniLM-L12-v2` (slovenčina)
- **Chunking:** Kontextové chunks (2000 znakov, 400 overlap, min 500 tokenov)

## 💡 Príklady použitia

### Otázky ktoré agent zvládne:
- *"Aké sú podmienky pre založenie s.r.o. na Slovensku?"*
- *"Vysvetli mi § 40 Občianskeho zákonníka"*  
- *"Nájdi súdne rozhodnutia o pracovnom práve"*
- *"Analyzuj tento právny text: 'Podľa § 123...'"*
- *"Aké sú výpovedné dôvody v pracovnom práve?"*
- *"Čo robiť pri krádeži auta?"*

### Pokročilé vyhľadávacie možnosti:
```
# Sémantické vyhľadávanie
"povinnosti konateľa s.r.o."

# Fulltext vyhľadávanie
"contains:spoločnosť"
"not_contains:fyzická osoba" 

# Regex vyhľadávanie
"regex:§\\s*135[a-z]*"

# Kombinované dotazy  
"law:513/1991 contains:súd"
"law:40/1964 regex:§\\s*[0-9]+"
```

### Demo konverzácia:
```
**Otázka:** "Ako sa zakladá s.r.o.?"

Thought: Používateľ sa pýta na založenie s.r.o. Použijem enhanced_vector_search.
Action: enhanced_vector_search
Action Input: založenie spoločnosti s ručením obmedzeným

**Otázka:** "Nájdi všetky paragrafy o súdoch v obchodnom zákonníku"

Action: enhanced_vector_search  
Action Input: law:513/1991 contains:súd
```

## 🧪 Testovanie

### Test cez web aplikáciu:
```bash
streamlit run app.py
# alebo
./run.sh
```
Otestuje: Enhanced Vector Search, databázu, fulltext možnosti, kontextové chunky cez webové rozhranie

## ⚠️ Obmedzenia a upozornenia

### Dôležité upozornenie:
**Tento AI asistent NENÍ náhradou za profesionálne právne poradenstvo!** 
Poskytuje len základné informácie a odporúčania. Pri zložitých právnych 
otázkach vždy kontaktujte kvalifikovaného advokáta.

### Technické obmedzenia:
- Vector search pracuje s 3120 optimalizovanými kontextovými chunkami
- Chunking strategy zameraná na zachovanie kontextu (min 500 tokenov)  
- Enhanced Vector Search podporuje len základné fulltext operácie
- Webové vyhľadávanie závisí od dostupnosti Tavily API
- Kvalita odpovedí závisí od kvality OpenAI modelu

### Náklady:
- OpenAI API: ~$0.004 za 1K tokenov (GPT-4o-mini)
- Tavily API: Freemium plán disponibilný
- ChromaDB: Lokálne, bez nákladov

## 🚀 Budúce rozšírenia

### Možné vylepšenia:
- [ ] Integrácia s oficiálnymi právnymi databázami (Slov-Lex, Zákony pre ľudí)
- [ ] Podpora pre viac krajín (AT, HU, PL)
- [ ] RAG s aktuálnymi súdnymi rozhodnutiami
- [ ] Export konzultácií do PDF
- [ ] Multi-agent architektúra (špecializovaní agenti pre rôzne oblasti)
- [ ] Voice interface
- [ ] Slack/Teams integrácia
- [x] **Enhanced Vector Search s fulltext možnosťami**
- [x] **Optimalizované chunking (kontextové chunks)**

### Technické vylepšenia:
- [ ] Pokročilejší fulltext search (Elasticsearch/PostgreSQL FTS)
- [ ] Async spracovanie pre rýchlejšie odpovede
- [ ] Caching pre často kladené otázky  
- [ ] Monitoring a logging
- [ ] Docker kontainerizácia
- [ ] CI/CD pipeline
- [x] **Multilingual embedding model pre slovenčinu**

## 📚 Zdroje a referencie

### Použité technológie:
- [LangChain](https://python.langchain.com/) - AI agent framework
- [OpenAI API](https://openai.com/api/) - Large Language Models
- [Streamlit](https://streamlit.io/) - Web aplikácia  
- [ChromaDB](https://www.trychroma.com/) - Vector databáza
- [Tavily](https://tavily.com/) - Search API

### Právne zdroje:
- [Slov-Lex](https://www.slov-lex.sk/) - Zbierka zákonov SR
- [Zákony pro lidi](https://www.zakonyprolidi.cz/) - České právo
- [Portál Justice.gov.sk](https://www.justice.gov.sk/) - Ministerstvo spravodlivosti

## 👨‍💻 Autor

**Projekt pre kurz AI Agenti**
- **Autor:** Lukáš Tisoň
- **Rok:** 2025  
- **Inštitúcia:** Robot_Dreams
- **Kurz:** AI Agenti - Lekce 7

## 📄 Licencia

Tento projekt je vytvorený len na vzdelávacie účely v rámci školského zadania.

---

**⚖️ Disclaimer:** AI Právny Asistent je experimentálny nástroj určený na vzdelávacie 
a demonštračné účely. Nie je certifikovaný pre profesionálne právne poradenstvo.
