#!/bin/bash

# Helper script pre spustenie AI Právneho Asistenta
# Autor: Lukáš Tisoň
# Použitie: ./run.sh

echo "🚀 Spúšťam AI Právny Asistent..."

# Skontroluj či existuje venv
if [ ! -d "venv" ]; then
    echo "❌ Virtuálne prostredie 'venv' neexistuje!"
    echo "💡 Vytvorte ho príkazom: python -m venv venv"
    exit 1
fi

# Skontroluj či existuje .env
if [ ! -f ".env" ]; then
    echo "⚠️  Súbor .env neexistuje!"
    echo "💡 Skopírujte .env.example na .env a nastavte API kľúče"
    read -p "Pokračovať aj tak? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Aktivuj venv a spusť aplikáciu
echo "🔧 Aktivujem virtuálne prostredie..."
source venv/bin/activate

echo "📦 Kontrolujem závislosti..."
pip list | grep streamlit > /dev/null
if [ $? -ne 0 ]; then
    echo "❌ Streamlit nie je nainštalovaný!"
    echo "💡 Nainštalujte závislosti: pip install -r requirements.txt"
    exit 1
fi

echo "🌐 Spúšťam Streamlit server..."
echo "📱 Aplikácia bude dostupná na: http://localhost:8501"
echo "🛑 Pre zastavenie stlačte Ctrl+C"
echo ""

streamlit run app.py
