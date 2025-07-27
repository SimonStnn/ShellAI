"""
Command-line interface for ShellAI.

Provides easy-to-use commands for collecting system information
and querying it with natural language.
"""

import sys
from pathlib import Path
from typing import Tuple

import click

from .ask import SystemQueryEngine
from .collect_info import SystemInfoCollector


@click.group()
@click.version_option()
def cli():
    """ShellAI - Natural language system queries and shell commands."""


@cli.command()
@click.option(
    "--output-dir",
    default="system_info",
    help="Directory to save system information files",
)
@click.option("--custom-command", multiple=True, help="Add custom command as 'name:command'")
def collect(output_dir: str, custom_command: Tuple[str, ...]):
    """Collect system information for querying."""
    collector = SystemInfoCollector(output_dir)

    # Collect standard system info
    results = collector.collect_all()

    # Collect custom commands
    for cmd in custom_command:
        if ":" not in cmd:
            click.echo(f"❌ Invalid custom command format: {cmd}")
            click.echo("Use format: name:command")
            continue

        name, command = cmd.split(":", 1)
        collector.collect_custom(name.strip(), command.strip())

    successful = sum(results.values())
    total = len(results)

    click.echo("\n✅ Collection complete!")
    click.echo(f"📊 Successfully collected {successful}/{total} items")
    click.echo(f"📁 Files saved to: {Path(output_dir).absolute()}")


@cli.command()
@click.option(
    "--system-info-dir",
    default="system_info",
    help="Directory containing system info files",
)
@click.option("--model", default="mistral", help="Ollama model to use")
@click.option("--question", help="Single question to ask (non-interactive mode)")
def ask(system_info_dir: str, model: str, question: str):
    """Ask natural language questions about your system."""
    engine = SystemQueryEngine(system_info_dir=system_info_dir, model=model)

    if not engine.initialize():
        sys.exit(1)

    if question:
        # Single question mode
        response = engine.query(question)
        if response:
            click.echo(f"\n💡 {response}")
    else:
        # Interactive mode
        engine.interactive_session()


@cli.command()
@click.option(
    "--system-info-dir",
    default="system_info",
    help="Directory containing system info files",
)
def status(system_info_dir: str):
    """Show status of collected system information."""
    info_dir = Path(system_info_dir)

    if not info_dir.exists():
        click.echo(f"❌ Directory '{system_info_dir}' does not exist.")
        click.echo("Run 'shellai collect' first.")
        return

    files = list(info_dir.glob("*.txt"))

    if not files:
        click.echo(f"❌ No system info files found in '{system_info_dir}'.")
        click.echo("Run 'shellai collect' first.")
        return

    click.echo(f"📁 System info directory: {info_dir.absolute()}")
    click.echo(f"📄 Found {len(files)} info files:")

    for file in sorted(files):
        size = file.stat().st_size
        click.echo(f"  • {file.name} ({size} bytes)")


@cli.command()
def setup():
    """Check and setup requirements for ShellAI."""
    click.echo("🔍 Checking ShellAI setup...")

    # Check Python version
    if sys.version_info < (3, 10):
        click.echo("❌ Python 3.10+ required")
        return
    else:
        click.echo(f"✅ Python {sys.version.split()[0]}")

    # Check LlamaIndex
    try:
        import llama_index  # type: ignore

        click.echo("✅ LlamaIndex installed")
    except ImportError:
        click.echo("❌ LlamaIndex not installed")
        click.echo("Run: pip install llama-index llama-index-llms-ollama")
        return

    # Check if Ollama is available
    import subprocess

    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=False)
        if result.returncode == 0:
            click.echo("✅ Ollama is available")
            models = [
                line.split()[0]
                for line in result.stdout.split("\n")
                if line and not line.startswith("NAME")
            ]
            if models:
                click.echo(f"📦 Available models: {', '.join(models)}")
            else:
                click.echo("⚠️  No models installed")
                click.echo("Try: ollama pull mistral")
        else:
            click.echo("❌ Ollama not available")
            click.echo("Install from: https://ollama.ai")
    except FileNotFoundError:
        click.echo("❌ Ollama not found")
        click.echo("Install from: https://ollama.ai")

    click.echo("\n🎯 Setup complete! Try:")
    click.echo("  shellai collect    # Collect system info")
    click.echo("  shellai ask        # Ask questions about your system")


def main():
    """Main entry point for the CLI application."""
    cli()


if __name__ == "__main__":
    main()
