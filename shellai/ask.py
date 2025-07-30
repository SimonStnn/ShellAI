"""
Natural language query interface for system information.

This module provides an interactive way to ask questions about your system
using natural language, powered by LlamaIndex and Ollama.
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

from llama_index.core.embeddings import resolve_embed_model  # type: ignore

from .config import get_config

try:
    from llama_index.core import (
        Settings,
        SimpleDirectoryReader,
        StorageContext,
        VectorStoreIndex,
        load_index_from_storage,  # type: ignore
    )
    from llama_index.llms.ollama import Ollama
except ImportError:
    print("❌ Error: LlamaIndex dependencies not installed.")
    print("Run: pip install llama-index llama-index-llms-ollama")
    sys.exit(1)


class SystemQueryEngine:
    """Natural language query engine for system information."""

    def __init__(
        self,
        system_info_dir: Optional[str] = None,
        model: Optional[str] = None,
        config_path: Optional[str] = None,
    ):
        """Initialize the query engine."""
        self.config = get_config(config_path)

        # Use config values with CLI overrides
        self.system_info_dir = Path(system_info_dir or self.config.system_info_dir)
        self.storage_dir = self.system_info_dir / self.config.storage_dir
        self.model = model or self.config.default_model

        self.index: Optional[VectorStoreIndex] = None
        self.query_engine = None

        if not self.system_info_dir.exists():
            print(f"❌ System info directory '{self.system_info_dir}' not found.")
            print("Run collect_info.py first to gather system data.")
            sys.exit(1)

        # Create storage directory if it doesn't exist
        self.storage_dir.mkdir(exist_ok=True)

    def initialize(self) -> bool:
        """Initialize the LLM and create or load the index."""
        try:
            print(f"🤖 Initializing with model: {self.model}")

            # Configure embedding model from config
            Settings.embed_model = resolve_embed_model(self.config.embedding_model)

            # Initialize Ollama LLM with config settings
            llm = Ollama(
                model=self.model,
                base_url=self.config.ollama_base_url,
                request_timeout=self.config.get("ollama.request_timeout", 60.0),
            )
            Settings.llm = llm

            # Try to load existing index from storage
            if self._storage_exists():
                print("📚 Loading existing index from storage...")
                try:
                    storage_context = StorageContext.from_defaults(
                        persist_dir=str(self.storage_dir)
                    )
                    # Load index and cast to VectorStoreIndex
                    loaded_index = load_index_from_storage(storage_context)
                    if isinstance(loaded_index, VectorStoreIndex):
                        self.index = loaded_index
                        print("✅ Index loaded from storage!")
                    else:
                        print("⚠️ Loaded index is not a VectorStoreIndex, creating new one...")
                        self.index = self._create_new_index()
                except Exception as e:
                    print(f"⚠️ Failed to load existing index: {e}")
                    print("📚 Creating new index...")
                    self.index = self._create_new_index()
            else:
                print("� Creating new index...")
                self.index = self._create_new_index()

            if not self.index:
                return False

            # Create query engine
            self.query_engine = self.index.as_query_engine(llm=llm)

            print("✅ Query engine initialized successfully!")
            return True

        except Exception as e:
            print(f"❌ Failed to initialize: {e}")
            print("Make sure Ollama is running and the model is available.")
            print(f"Try: ollama pull {self.model}")
            return False

    def _storage_exists(self) -> bool:
        """Check if persistent storage exists and is valid."""
        required_files = ["index_store.json", "docstore.json", "vector_store.json"]
        return all((self.storage_dir / file).exists() for file in required_files)

    def _create_new_index(self) -> Optional[VectorStoreIndex]:
        """Create a new vector index from system information documents."""
        # Load system information documents
        print("📄 Loading system information documents...")

        # Check if text files exist
        text_files = list(self.system_info_dir.glob("*.txt"))
        if not text_files:
            print("❌ No system information text files found.")
            print("💡 Run 'shellai collect' first to gather system data.")
            return None

        documents = SimpleDirectoryReader(
            str(self.system_info_dir),
            recursive=False,  # Don't include storage directory
            exclude=["storage"],
        ).load_data()

        if not documents:
            print("❌ No system information files found.")
            return None

        print(f"📄 Loaded {len(documents)} system info files")

        # Create vector index
        print("🔍 Creating search index...")
        index = VectorStoreIndex.from_documents(documents)

        # Persist the index
        print("💾 Saving index to storage...")
        index.storage_context.persist(persist_dir=str(self.storage_dir))

        print("✅ Index created and persisted to storage")
        print("💡 Text files are now optional - all data is stored in the index")

        return index

    def refresh_index(self) -> bool:
        """Refresh the index with updated system information."""
        try:
            print("🔄 Refreshing index with latest system information...")
            self.index = self._create_new_index()

            if not self.index:
                return False

            # Update query engine with new index
            if Settings.llm:
                self.query_engine = self.index.as_query_engine(llm=Settings.llm)
                print("✅ Index refreshed successfully!")
                return True
            else:
                print("❌ LLM not initialized.")
                return False

        except Exception as e:
            print(f"❌ Failed to refresh index: {e}")
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
