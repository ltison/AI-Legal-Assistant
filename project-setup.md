# AI Právny Asistent

AI agent pre slovenské a české právo postavený na LangChain frameworku.

## Požiadavky

- Python 3.8+
- Virtuálne prostredie (venv)
- API kľúče: OpenAI (povinný), Tavily (voliteľný)

## Inštalácia a spustenie

### 1. Klónovanie a setup
```bash
git clone <repo-url>
cd AI_Kurz_Ulohy
```

### 2. Vytvorenie virtuálneho prostredia
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# alebo
venv\Scripts\activate     # Windows
```

### 3. Inštalácia závislostí
```bash
pip install -r requirements.txt
```

### 4. Konfigurácia API kľúčov
```bash
cp .env.example .env
# Upravte .env súbor s vašimi API kľúčmi
```

### 5. Spustenie aplikácie
```bash
# Aktivujte venv ak nie je aktívne
source venv/bin/activate

# Spustite Streamlit
streamlit run app.py
```

## Štruktúra projektu

- `app.py` - Streamlit webové rozhranie
- `agent/` - LangChain agent a nástroje
- `data/` - Databázy a právne texty
- `scripts/` - Skripty pre inicializáciu
- `.env` - API kľúče (vytvorte z .env.example)

## Technológie

- **LangChain**: ReAct agent pattern
- **Streamlit**: Webové UI
- **ChromaDB**: Vector databáza
- **SQLite**: Relačná databáza
- **OpenAI**: GPT modely

## Poznámky pre vývojárov

- **Vždy používajte virtuálne prostredie!**
- Python interpreter: `./venv/bin/python`
- Terminal s venv: `source venv/bin/activate`
- API kľúče len v `.env` súbore, nie v UI
