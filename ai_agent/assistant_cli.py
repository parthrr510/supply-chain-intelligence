import argparse
import logging
import os
import sys
import uuid

# Ensure the working directory is the project root so relative paths work
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv

from ai_agent.assistant.agent import AssistantAgent


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        stream=sys.stdout,
    )


def main():
    load_dotenv()
    setup_logging()

    parser = argparse.ArgumentParser(description="Supply Chain Assistant CLI")
    parser.add_argument(
        "--query", "-q", type=str, help="The query to ask the assistant"
    )
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="Run in interactive mode"
    )
    args = parser.parse_args()

    # Do not crash if API key is not in environment, genai client will error out when querying
    # unless it's available. We just initialize the agent here.
    try:
        agent = AssistantAgent()
    except Exception as e:
        print(f"Error initializing agent: {e}")
        print("Please make sure GEMINI_API_KEY is set in your environment.")
        sys.exit(1)

    session_id = str(uuid.uuid4())

    if args.query:
        print(agent.query(args.query, session_id=session_id))
    elif args.interactive:
        print("Supply Chain Assistant. Type 'exit' or 'quit' to stop.")
        while True:
            try:
                user_input = input("\nYou: ")
                if user_input.lower() in ("exit", "quit"):
                    break
                if not user_input.strip():
                    continue

                response = agent.query(user_input, session_id=session_id)
                print(f"\nAssistant: {response}")
            except EOFError:
                break
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\nError: {e}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
