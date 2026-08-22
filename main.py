import os
import sys
from dotenv import load_dotenv
from agent.core import AgentCore
from skills.calculator import CalculatorSkill

# Load environment variables
load_dotenv()

def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[Error] GEMINI_API_KEY environment variable not found in environment or .env file.")
        print("Please create a .env file in the root directory with: GEMINI_API_KEY=your_api_key_here")
        sys.exit(1)

    # 1. Initialize Agent Core
    agent = AgentCore(api_key=api_key)

    # 2. Register Skills
    agent.register_skill(CalculatorSkill())
    print("\n=======================================================")
    print("         Personal AI Agent (ReAct CLI Prototype)        ")
    print("=======================================================")
    print("Type your query (or 'exit' / 'q' to quit):")
    
    # 3. Interactive CLI loop
    while True:
        try:
            prompt = input("\nYou > ")
            if prompt.strip().lower() in ["exit", "quit", "q"]:
                print("Goodbye!")
                break
                
            if not prompt.strip():
                continue
                
            # Execute Agent Core Loop
            response = agent.execute(prompt)
            print(f"\nAgent > {response}")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\n[System Error] Unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
