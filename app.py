"""
Streamlit web aplikácia pre AI Právneho Asistenta
"""

import streamlit as st
import os
from dotenv import load_dotenv
import sys

# Pridaj project root do Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from agent.legal_agent import create_legal_assistant
except ImportError as e:
    st.error(f"Chyba pri importovaní agenta: {e}")
    st.stop()

load_dotenv()


def main():
    """Hlavná funkcia Streamlit aplikácie"""
    
    # Konfigurácia stránky
    st.set_page_config(
        page_title="AI Právny Asistent",
        page_icon="⚖️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Hlavný nadpis
    st.title("⚖️ AI Právny Asistent")
    st.markdown("*Inteligentný pomocník pre slovenské a české právo*")
    
    # Upozornenie
    st.warning("""
    🚨 **DÔLEŽITÉ UPOZORNENIE**: Tento AI asistent poskytuje len základné informácie 
    a nie je náhradou za profesionálne právne poradenstvo. Pri zložitých právnych 
    otázkach vždy kontaktujte kvalifikovaného advokáta.
    """)
    
    # Sidebar s konfiguráciou
    with st.sidebar:
        st.header("⚙️ Nastavenia")
        
        # Model selection
        model_options = {
            "GPT-4o": "gpt-4o-2024-08-06",
            "GPT-4o-mini": "gpt-4o-mini"
        }
        selected_model = st.selectbox(
            "Vyberte AI model:",
            options=list(model_options.keys()),
            index=0
        )
        
        # API kľúče - len status, nie hodnoty
        st.subheader("🔑 API Kľúče")
        
        # Načítaj API kľúče z environment (z .env súboru)
        openai_key = os.getenv("OPENAI_API_KEY", "")
        tavily_key = os.getenv("TAVILY_API_KEY", "")
        
        # Zobrazenie stavu API kľúčov (bez hodnôt)
        if openai_key:
            st.success("✅ OpenAI API kľúč: Nastavený")
        else:
            st.error("❌ OpenAI API kľúč: Chýba v .env súbore")
            
        if tavily_key:
            st.success("✅ Tavily API kľúč: Nastavený")
        else:
            st.warning("⚠️ Tavily API kľúč: Chýba v .env súbore (voliteľný)")
        
        st.info("💡 **Tip:** API kľúče nastavte v súbore `.env` v root priečinku projektu")
        
        # Informácie o nástrojoch
        st.subheader("🔧 Dostupné nástroje")
        st.info("""
        - 🔍 **Tavily Search**: Webové vyhľadávanie
        - 📚 **Wikipedia**: Právne pojmy
        - 💾 **SQL Databáza**: Slovník právnych pojmov
        - 🤖 **ChromaDB**: vyhľadávanie v predpisoch
        """)
    
    # Hlavná oblasť
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Header s počítadlom správ
        col_header, col_counter = st.columns([3, 1])
        with col_header:
            st.header("💬 Rozhovor s asistentom")
        with col_counter:
            if 'messages' in st.session_state and st.session_state.messages:
                st.metric("Počet správ", len(st.session_state.messages))
        
        # Inicializácia session state
        if "messages" not in st.session_state:
            st.session_state.messages = []
            st.session_state.agent = None
        
        # Status agenta
        if not openai_key:
            st.warning("🔑 Vložte OpenAI API kľúč v bočnom paneli pre fungovanie asistenta")
        elif st.session_state.agent is None:
            st.info("⏳ Počkajte na inicializáciu AI asistenta...")
        else:
            st.success("🤖 AI asistent je pripravený!")
        
        # Vytvorenie agenta ak ešte neexistuje
        if st.session_state.agent is None and openai_key:
            with st.spinner("Inicializujem AI asistenta..."):
                try:
                    st.session_state.agent = create_legal_assistant(
                        model=model_options[selected_model]
                    )
                    st.success("✅ AI asistent je pripravený!")
                except Exception as e:
                    st.error(f"❌ Chyba pri inicializácii: {e}")
                    st.stop()
        
        # Zobrazenie histórie konverzácie
        chat_container = st.container()
        with chat_container:
            for i, message in enumerate(st.session_state.messages):
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                    
                    # Zobraz expander pre intermediate steps ak existujú
                    if message["role"] == "assistant" and message.get("intermediate_steps"):
                        with st.expander("🔍 Postup riešenia", expanded=False):
                            for j, step in enumerate(message["intermediate_steps"]):
                                # Formátované zobrazenie kroku
                                st.markdown(f"**Krok {j+1}:**")
                                
                                # Ak je step tuple/list s (action, observation)
                                if isinstance(step, (tuple, list)) and len(step) >= 2:
                                    action, observation = step[0], step[1]
                                    
                                    # Zobraz akciu a thought ak existuje
                                    if hasattr(action, 'tool'):
                                        st.markdown(f"🔧 **Nástroj:** {action.tool}")
                                    if hasattr(action, 'tool_input'):
                                        st.markdown(f"📝 **Vstup:** {action.tool_input}")
                                    if hasattr(action, 'log') and action.log:
                                        st.markdown(f"🧠 **Úvaha:** {action.log}")
                                    
                                    # Zobraz výsledok - vždy celý, bez ďalšieho expandéra
                                    if observation:
                                        st.markdown(f"📋 **Výsledok:**")
                                        st.text(str(observation))
                                else:
                                    # Fallback pre iné formáty
                                    st.text(str(step))
                                
                                st.divider()  # Oddeľovač medzi krokmi
                    
                    # Pridaj timestamp pre posledné správy
                    if i >= len(st.session_state.messages) - 2:  # Posledné 2 správy
                        st.caption(f"Správa #{i+1}")
        
        # Input pre novú otázku
        if prompt := st.chat_input(
            "Napíšte vašu právnu otázku...", 
            disabled=not openai_key or st.session_state.agent is None
        ):
            # Pridaj používateľskú správu
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Získaj odpoveď od agenta
            with st.spinner("Premýšľam..."):
                try:
                    # Type check pre Pylance
                    if st.session_state.agent is not None:
                        result = st.session_state.agent.ask(prompt)
                    else:
                        raise Exception("Agent nie je inicializovaný")
                    
                    if result["success"]:
                        response = result["answer"]
                        
                        # Ulož intermediate steps oddelene pre expander
                        intermediate_steps = result.get("intermediate_steps", [])
                    else:
                        response = f"❌ {result['answer']}"
                        intermediate_steps = []
                    
                    # Pridaj odpoveď do histórie s intermediate steps
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response,
                        "intermediate_steps": intermediate_steps
                    })
                    
                except Exception as e:
                    error_msg = f"Chyba pri spracovaní otázky: {str(e)}"
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })
            
            # Spusti rerun aby sa zobrazila nová správa
            st.rerun()
        
        # Tlačidlá pre správu konverzácie
        col_clear, col_export = st.columns(2)
        
        with col_clear:
            if st.button("🗑️ Vymazať históriu", type="secondary"):
                st.session_state.messages = []
                if st.session_state.agent:
                    st.session_state.agent.reset_memory()
                st.rerun()
        
        with col_export:
            if st.button("📋 Exportovať konverzáciu", type="secondary"):
                if st.session_state.messages:
                    export_lines = []
                    for msg in st.session_state.messages:
                        export_lines.append(f"{msg['role'].upper()}: {msg['content']}")
                        
                        # Pridaj intermediate steps do exportu ak existujú
                        if msg.get("intermediate_steps"):
                            export_lines.append("\nPOSTUP RIEŠENIA:")
                            export_lines.append("=" * 50)
                            for i, step in enumerate(msg["intermediate_steps"]):
                                export_lines.append(f"\nKrok {i+1}:")
                                export_lines.append("-" * 20)
                                
                                # Formátovaný export krokov
                                if isinstance(step, (tuple, list)) and len(step) >= 2:
                                    action, observation = step[0], step[1]
                                    
                                    if hasattr(action, 'tool'):
                                        export_lines.append(f"Nástroj: {action.tool}")
                                    if hasattr(action, 'tool_input'):
                                        export_lines.append(f"Vstup: {action.tool_input}")
                                    if observation:
                                        export_lines.append(f"Výsledok: {str(observation)[:1000]}...")
                                else:
                                    export_lines.append(str(step))
                            export_lines.append("")  # Prázdny riadok
                    
                    export_text = "\n".join(export_lines)
                    st.download_button(
                        label="💾 Stiahnuť ako TXT",
                        data=export_text,
                        file_name="legal_conversation.txt",
                        mime="text/plain"
                    )
                else:
                    st.info("Žiadna konverzácia na export")
    
    with col2:
        st.header("📚 Príklady otázok")
        
        example_questions = [
            "Aké sú podmienky pre založenie s.r.o. na Slovensku?",
            "Vysvetli mi § 40 Občianskeho zákonníka",
            "Aké sú výpovedné dôvody v pracovnom práve?",
            "Ako funguje dedenie podľa zákona?",
            "Čo robiť pri krádeži auta?",
            "Aké sú základné náležitosti kúpnej zmluvy?",
            "Môžem vypovědať nájomníkovi bez udania dôvodu?",
            "Aká je daň z prevodu nehnuteľnosti?"
        ]
        
        for question in example_questions:
            if st.button(
                question, 
                key=f"example_{hash(question)}",
                disabled=not openai_key or st.session_state.agent is None,
                use_container_width=True
            ):
                # Pridaj otázku do správ
                st.session_state.messages.append({"role": "user", "content": question})
                
                # Získaj odpoveď
                with st.spinner("Premýšľam..."):
                    try:
                        # Type check pre Pylance
                        if st.session_state.agent is not None:
                            result = st.session_state.agent.ask(question)
                        else:
                            raise Exception("Agent nie je inicializovaný")
                        
                        if result["success"]:
                            response = result["answer"]
                            
                            # Ulož intermediate steps oddelene pre expander
                            intermediate_steps = result.get("intermediate_steps", [])
                        else:
                            response = f"❌ {result['answer']}"
                            intermediate_steps = []
                        
                        # Pridaj odpoveď do histórie s intermediate steps
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": response,
                            "intermediate_steps": intermediate_steps
                        })
                        
                    except Exception as e:
                        error_msg = f"Chyba pri spracovaní otázky: {str(e)}"
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_msg
                        })
                
                # Spusti rerun pre zobrazenie novej konverzácie
                st.rerun()
        
        # Informácie o projekte
        st.header("ℹ️ O projekte")
        st.info("""
        **AI Právny Asistent v1.0**
        
        📋 **Technológie:**
        - LangChain ReAct Agent
        - OpenAI GPT modely
        - Streamlit UI
        - ChromaDB Vector + Fulltext
        - SQLite databáza
        
        🎯 **Účel:**
        Školský projekt pre kurz AI Agenti
        
        👨‍💻 **Autor:** Lukáš Tisoň
        📅 **Rok:** 2025
        """)
        
        # Link na GitHub
        st.markdown("""
        🔗 **GitHub repozitár:**
        [AI-Legal-Assistant](https://github.com/your-username/ai-legal-assistant)
        """)


if __name__ == "__main__":
    main()
