"""
Natural language query interface for system information.

This module provides an interactive way to ask questions about your system
using natural language, powered by LlamaIndex and Ollama.
"""

import sys
from pathlib import Path
from typing import Optional
from llama_index.core.embeddings import resolve_embed_model  # type: ignore

try:
    from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
    from llama_index.llms.ollama import Ollama
except ImportError:
    print("❌ Error: LlamaIndex dependencies not installed.")
    print("Run: pip install llama-index llama-index-llms-ollama")
    sys.exit(1)


class SystemQueryEngine:
    """Natural language query engine for system information."""

    def __init__(self, system_info_dir: str = "system_info", model: str = "mistral"):
        """Initialize the query engine."""
        self.system_info_dir = Path(system_info_dir)
        self.model = model
        self.index: Optional[VectorStoreIndex] = None
        self.query_engine = None

        if not self.system_info_dir.exists():
            print(f"❌ System info directory '{system_info_dir}' not found.")
            print("Run collect_info.py first to gather system data.")
            sys.exit(1)

    def initialize(self) -> bool:
        """Initialize the LLM and create the index."""
        try:
            print(f"🤖 Initializing with model: {self.model}")

            Settings.embed_model = resolve_embed_model("local:BAAI/bge-small-en")

            # Load system information documents
            print("📚 Loading system information...")
            documents = SimpleDirectoryReader(str(self.system_info_dir)).load_data()

            if not documents:
                print("❌ No system information files found.")
                return False

            print(f"📄 Loaded {len(documents)} system info files")

            # Create vector index
            print("🔍 Creating search index...")
            self.index = VectorStoreIndex.from_documents(documents)

            # Initialize Ollama LLM
            llm = Ollama(model=self.model)

            # Create query engine
            self.query_engine = self.index.as_query_engine(llm=llm)  # type: ignore

            print("✅ Query engine initialized successfully!")
            return True

        except Exception as e:
            print(f"❌ Failed to initialize: {e}")
            print("Make sure Ollama is running and the model is available.")
            print(f"Try: ollama pull {self.model}")
            return False

    def query(self, question: str) -> Optional[str]:
        """Query the system information with natural language."""
        if not self.query_engine:
            print("❌ Query engine not initialized.")
            return None

        try:
            print(f"🤔 Thinking about: {question}")
            response = self.query_engine.query(question)
            return str(response)
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return None

    def interactive_session(self):
        """Start an interactive query session."""
        print("\n🎯 Welcome to ShellAI System Query!")
        print("Ask questions about your system in natural language.")
        print("Type 'exit', 'quit', or 'q' to stop.\n")

        while True:
            try:
                question = input("❓ Ask about your system: ").strip()

                if question.lower() in ["exit", "quit", "q"]:
                    print("👋 Goodbye!")
                    break

                if not question:
                    continue

                response = self.query(question)
                if response:
                    print(f"\n💡 {response}\n")
                    print("-" * 50)

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except EOFError:
                print("\n👋 Goodbye!")
                break


def main():
    """Main function for the interactive query system."""
    import argparse

    parser = argparse.ArgumentParser(description="Ask natural language questions about your system")
    parser.add_argument("--model", default="mistral", help="Ollama model to use (default: mistral)")
    parser.add_argument(
        "--system-info-dir",
        default="system_info",
        help="Directory containing system info files",
    )
    parser.add_argument("--question", help="Single question to ask (non-interactive mode)")

    args = parser.parse_args()

    # Initialize query engine
    engine = SystemQueryEngine(system_info_dir=args.system_info_dir, model=args.model)

    if not engine.initialize():
        sys.exit(1)

    # Single question mode
    if args.question:
        response = engine.query(args.question)
        if response:
            print(f"\n💡 {response}")
        sys.exit(0)

    # Interactive mode
    engine.interactive_session()


if __name__ == "__main__":
    main()
