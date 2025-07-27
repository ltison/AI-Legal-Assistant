"""
AI Právny Asistent - ReAct Agent
"""

import os
from typing import List, Dict, Any
from dotenv import load_dotenv

# Imports pre LangChain
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory

# Import nástrojov
from agent.tools.search_tools import get_search_tools
from agent.tools.database_tools import get_database_tools  
from agent.tools.legal_tools import get_legal_tools
from agent.tools.enhanced_vector_search import get_enhanced_search_tool

load_dotenv()


class LegalAssistantAgent:
    """AI Agent pre právne poradenstvo s ReAct pattern"""
    
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.1):
        """
        Inicializácia agenta
        
        Args:
            model: OpenAI model na použitie
            temperature: Teplota pre generovanie (nižšia = konzistentnejšie odpovede)
        """
        self.model_name = model
        self.temperature = temperature
        
        # Skontroluj API kľúč
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY nie je nastavený v .env súbore")
        
        # Inicializuj LLM  
        self.llm = ChatOpenAI(
            model_name=model,
            temperature=temperature,
            max_tokens=4000
        )
        
        # Načítaj nástroje
        self.tools = self._load_tools()
        
        # Nastav memory pre konverzáciu - používame jednoduchší prístup
        self.conversation_history = []
        
        # Vytvor agenta
        self.agent_executor = self._create_agent()
    
    def _load_tools(self) -> List:
        """Načíta všetky nástroje pre agenta"""
        all_tools = []
        
        try:
            # Vyhľadávacie nástroje
            all_tools.extend(get_search_tools())
            print("✅ Načítané vyhľadávacie nástroje")
        except Exception as e:
            print(f"⚠️ Chyba pri načítaní vyhľadávacích nástrojov: {e}")
        
        try:
            # Databázové nástroje (základný vector search)
            all_tools.extend(get_database_tools())
            print("✅ Načítané databázové nástroje")
        except Exception as e:
            print(f"⚠️ Chyba pri načítaní databázových nástrojov: {e}")
        
        try:
            # Enhanced vector search s fulltext možnosťami
            all_tools.append(get_enhanced_search_tool())
            print("✅ Načítaný enhanced vector search")
        except Exception as e:
            print(f"⚠️ Chyba pri načítaní enhanced vector search: {e}")
        
        try:
            # Právne nástroje
            all_tools.extend(get_legal_tools())
            print("✅ Načítané právne nástroje")
        except Exception as e:
            print(f"⚠️ Chyba pri načítaní právnych nástrojov: {e}")
        
        print(f"🔧 Celkovo načítaných {len(all_tools)} nástrojov")
        return all_tools
    
    def _create_agent(self) -> AgentExecutor:
        """Vytvor ReAct agenta s prompt template"""
        
        # Slovenský prompt pre právneho asistenta
        prompt_template = """
Ste AI asistent špecializovaný na slovenské a české právo. Vaša úloha je pomáhať používateľom s právnymi otázkami a poskytovať relevantné informácie.

DÔLEŽITÉ UPOZORNENIE: Nie ste náhradou za profesionálne právne poradenstvo. Vždy odporúčajte konzultáciu s advokátom pri zložitých prípadoch.

K dispozícii máte tieto nástroje:
{tools}

Názvy nástrojov: {tool_names}

DÔLEŽITÉ PRAVIDLÁ PRE ACTION INPUT:
- Ak používateľ poskytol konkrétny text (zmluva, paragraf, dokument), VŽDY použite presne tento text ako Action Input
- NIKDY nepoužívajte opisy ako "text poskytnutý používateľom" - použite skutočný obsah
- Pre vyhľadávanie použite konkrétne kľúčové slová z otázky používateľa

Postupujte podľa ReAct (Reasoning-Action) vzoru:
1. **Thought**: Analyzujte otázku a rozhodnite, aký nástroj použiť
2. **Action**: Vyberte vhodný nástroj  
3. **Action Input**: SKUTOČNÝ obsah/text/kľúčové slová (nie popis!)
4. **Observation**: Vyhodnoťte výsledky nástroja
5. **Opakujte** kým nemáte dostatok informácií na odpoveď

Formát odpovede:
Thought: [vaše uvažovanie]
Action: [názov_nástroja]
Action Input: [SKUTOČNÝ text alebo konkrétne kľúčové slová]
Observation: [výsledok nástroja]
... (opakujte podľa potreby)
Thought: Mám dostatok informácií na odpoveď
Final Answer: [finálna odpoveď používateľovi]

História konverzácie: {chat_history}

Otázka používateľa: {input}

Váš postup:
{agent_scratchpad}
"""

        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["input", "tools", "tool_names", "agent_scratchpad", "chat_history"],
            partial_variables={
                "tools": "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools]),
                "tool_names": ", ".join([tool.name for tool in self.tools])
            }
        )
        
        # Vytvor ReAct agenta
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # Vytvor AgentExecutor s lepším error handling
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,  # Pre debugging
            max_iterations=10,  # Zvýšený počet iterácií
            handle_parsing_errors="Check your output and make sure it conforms to the expected format! Use the exact text provided by the user as Action Input.",
            return_intermediate_steps=True,
            early_stopping_method="force"  # Opravená hodnota
        )
    
    def ask(self, question: str) -> Dict[str, Any]:
        """
        Položi otázku agentovi
        
        Args:
            question: Otázka používateľa
            
        Returns:
            Slovník s odpoveďou a metadátami
        """
        try:
            print(f"\n🤔 Otázka: {question}")
            print("=" * 50)
            
            # Priprav chat history ako string
            chat_history = "\n".join([
                f"Používateľ: {msg['question']}\nAsistent: {msg['answer']}"
                for msg in self.conversation_history[-3:]  # Posledné 3 výmeny
            ])
            
            result = self.agent_executor.invoke({
                "input": question,
                "chat_history": chat_history
            })
            
            # Ulož do histórie
            self.conversation_history.append({
                "question": question,
                "answer": result["output"]
            })
            
            return {
                "answer": result["output"],
                "intermediate_steps": result.get("intermediate_steps", []),
                "success": True
            }
            
        except Exception as e:
            print(f"❌ Chyba pri ReAct agente: {e}")
            print("🔄 Skúšam fallback riešenie...")
            
            # Fallback - pokus o priame použitie nástrojov
            try:
                fallback_result = self._fallback_response(question)
                return {
                    "answer": fallback_result,
                    "intermediate_steps": ["Použité fallback riešenie"],
                    "success": True
                }
            except Exception as fallback_error:
                error_msg = f"Chyba pri spracovaní otázky: {str(e)}"
                print(f"❌ {error_msg}")
                
                return {
                    "answer": f"Ospravedlňujem sa, ale vyskytla sa chyba: {error_msg}",
                    "intermediate_steps": [],
                    "success": False,
                    "error": str(e)
                }
    
    def _fallback_response(self, question: str) -> str:
        """
        Fallback riešenie ak ReAct agent zlyháva
        Pokúsi sa priamo použiť nástroje na zodpovedanie otázky
        """
        question_lower = question.lower()
        
        # Rozpoznanie typu otázky a priame použitie vhodného nástroja
        if any(keyword in question_lower for keyword in ['vyhľadaj', 'nájdi', 'hľadám', 'pojem', 'definícia']):
            # Pokus o vyhľadávanie v databáze pojmov
            print("� Detekované vyhľadávanie - skúšam search nástroje")
            for tool in self.tools:
                if "search" in tool.name.lower() or "term" in tool.name.lower():
                    try:
                        result = tool.invoke(question)
                        return result
                    except Exception as e:
                        print(f"⚠️ Chyba nástroja {tool.name}: {e}")
        
        elif any(keyword in question_lower for keyword in ['analyzuj', 'analýza', 'zmluva', 'dokument', 'paragraf']):
            # Pre analýzy použijeme vektorové vyhľadávanie
            print("� Detekovaná analýza textu - používam vector search")
            for tool in self.tools:
                if "vector" in tool.name.lower():
                    try:
                        result = tool.invoke(question)
                        return result
                    except Exception as e:
                        print(f"⚠️ Chyba nástroja {tool.name}: {e}")
        
        else:
            # Pokus o vyhľadávanie
            print("🔍 Všeobecná otázka - skúšam search nástroje")
            for tool in self.tools:
                if "search" in tool.name.lower():
                    try:
                        result = tool.invoke(question)
                        if result and "Nenašli sa" not in result:
                            return result
                    except Exception as e:
                        print(f"⚠️ Chyba nástroja {tool.name}: {e}")
        
        # Ak žiadny špecifický nástroj nezafungoval, skús všetky postupne
        print("🔄 Skúšam všetky dostupné nástroje...")
        for tool in self.tools:
            try:
                result = tool.invoke(question)
                if result and len(result.strip()) > 10:  # Základná kontrola kvality odpovede
                    return f"**Odpoveď z nástroja {tool.name}:**\n{result}"
            except Exception as e:
                continue  # Pokračuj s ďalším nástrojom
        
        # Ak nič nezafungovalo, vráť základnú odpoveď
        return """
        **Všeobecné právne poradenstvo k otázke:**
        "{question}"
        
        **Základné odporúčania:**
        1. **Dokumentácia** - zachovajte všetky relevantné dokumenty
        2. **Právna pomoc** - pri zložitých prípadoch kontaktujte advokáta  
        3. **Lehoty** - pozor na zákonné lehoty (premlčanie, námietky)
        4. **Doklady** - majte pripravené všetky potrebné doklady
        
        **Poznámka:** Pre presné informácie týkajúce sa vašej konkrétnej situácie 
        odporúčam konzultáciu s kvalifikovaným advokátom.
        """.format(question=question)

    def reset_memory(self):
        """Vynuluje pamäť konverzácie"""
        self.conversation_history = []
        print("🔄 Pamäť konverzácie bola vynulovaná")
    
    def get_conversation_history(self) -> List[Dict]:
        """Vráti históriu konverzácie"""
        return self.conversation_history
    
    def list_available_tools(self) -> List[Dict[str, str]]:
        """Vráti zoznam dostupných nástrojov"""
        return [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in self.tools
        ]


def create_legal_assistant(model: str = "gpt-4o-mini") -> LegalAssistantAgent:
    """
    Factory funkcia pre vytvorenie právneho asistenta
    
    Args:
        model: OpenAI model na použitie
        
    Returns:
        Inicializovaný LegalAssistantAgent
    """
    try:
        agent = LegalAssistantAgent(model=model)
        print("🎉 AI Právny Asistent je pripravený!")
        print(f"📊 Dostupných nástrojov: {len(agent.tools)}")
        return agent
        
    except Exception as e:
        print(f"❌ Chyba pri vytváraní agenta: {e}")
        raise


if __name__ == "__main__":
    # Test agenta
    try:
        agent = create_legal_assistant()
        
        # Testovacia otázka
        test_question = "Aké sú podmienky pre založenie s.r.o. na Slovensku?"
        result = agent.ask(test_question)
        
        print("\n" + "="*50)
        print("📋 VÝSLEDOK:")
        print("="*50)
        print(result["answer"])
        
    except Exception as e:
        print(f"❌ Chyba pri testovaní: {e}")
