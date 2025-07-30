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
from .config import get_config


@click.group()
@click.version_option()
@click.option("--config", help="Path to configuration file")
@click.pass_context
def cli(ctx: click.Context, config: str):
    """ShellAI - Natural language system queries and shell commands."""
    # Store config path in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config


@cli.command()
@click.option("--show", is_flag=True, help="Show current configuration")
@click.option("--reset", is_flag=True, help="Reset to default configuration")
@click.option("--set", "settings", multiple=True, help="Set config value (key=value)")
@click.pass_context
def config(ctx: click.Context, show: bool, reset: bool, settings: Tuple[str, ...]):
    """Manage ShellAI configuration."""
    config_path = ctx.obj.get("config_path") if ctx.obj else None
    cfg = get_config(config_path)

    if reset:
        if cfg.config_path.exists():
            cfg.config_path.unlink()
            click.echo(f"🗑️ Deleted config file: {cfg.config_path}")
        cfg.create_default_config()
        click.echo("✅ Configuration reset to defaults")
        return

    if settings:
        for setting in settings:
            if "=" not in setting:
                click.echo(f"❌ Invalid setting format: {setting}")
                click.echo("Use format: key=value (e.g., ollama.default_model=gemma2:2b)")
                continue

            key, value = setting.split("=", 1)
            # Try to convert value to appropriate type
            if value.lower() in ("true", "false"):
                value = value.lower() == "true"
            elif value.isdigit():
                value = int(value)
            elif value.replace(".", "").isdigit():
                value = float(value)

            cfg.set(key, value)
            click.echo(f"✅ Set {key} = {value}")

        if cfg.save():
            click.echo("💾 Configuration saved")
        else:
            click.echo("❌ Failed to save configuration")
        return

    if show or not (reset or settings):
        click.echo(f"📁 Config file: {cfg.config_path}")
        click.echo("\n🔧 Current configuration:")
        click.echo(f"  Ollama URL: {cfg.ollama_base_url}")
        click.echo(f"  Default model: {cfg.default_model}")
        click.echo(f"  Request timeout: {cfg.get('ollama.request_timeout', 60.0)}s")
        click.echo(f"  Embedding model: {cfg.embedding_model}")
        click.echo(f"  System info dir: {cfg.system_info_dir}")
        click.echo(f"  Storage dir: {cfg.storage_dir}")


@cli.command()
@click.option(
    "--output-dir",
    help="Directory to save system information files (overrides config)",
)
@click.option("--custom-command", multiple=True, help="Add custom command as 'name:command'")
@click.pass_context
def collect(ctx: click.Context, output_dir: str, custom_command: Tuple[str, ...]):
    """Collect system information for querying."""
    config_path = ctx.obj.get("config_path") if ctx.obj else None
    cfg = get_config(config_path)

    # Use config default if not specified
    output_dir = output_dir or cfg.system_info_dir
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
    help="Directory containing system info files (overrides config)",
)
@click.option("--model", help="Ollama model to use (overrides config)")
@click.option("--question", help="Single question to ask (non-interactive mode)")
@click.option("--refresh", is_flag=True, help="Refresh the index before querying")
@click.pass_context
def ask(ctx: click.Context, system_info_dir: str, model: str, question: str, refresh: bool):
    """Ask natural language questions about your system."""
    config_path = ctx.obj.get("config_path") if ctx.obj else None

    engine = SystemQueryEngine(
        system_info_dir=system_info_dir, model=model, config_path=config_path
    )

    if not engine.initialize():
        sys.exit(1)

    # Refresh index if requested
    if refresh:
        if not engine.refresh_index():
            click.echo("❌ Failed to refresh index.")
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
    help="Directory containing system info files (overrides config)",
)
@click.option("--force", is_flag=True, help="Force cleanup without confirmation")
@click.pass_context
def cleanup(ctx: click.Context, system_info_dir: str, force: bool):
    """Clean up text files after successful indexing (optional optimization)."""
    config_path = ctx.obj.get("config_path") if ctx.obj else None
    cfg = get_config(config_path)

    # Use config default if not specified
    system_info_dir = system_info_dir or cfg.system_info_dir
    system_path = Path(system_info_dir)
    storage_path = system_path / cfg.storage_dir

    # Check if index exists
    if not storage_path.exists():
        click.echo(
            "❌ No LlamaIndex storage found. Run 'shellai collect' and 'shellai refresh' first."
        )
        return

    # Check for text files
    text_files = list(system_path.glob("*.txt"))
    if not text_files:
        click.echo("✅ No text files found - already cleaned up!")
        return

    click.echo(f"📁 Found {len(text_files)} text files in {system_path}")
    click.echo("💾 LlamaIndex storage exists and contains all document data")
    click.echo("\n📄 Text files that can be removed:")
    for file in text_files:
        click.echo(f"  • {file.name} ({file.stat().st_size} bytes)")

    if not force:
        click.echo("\n⚠️  Important:")
        click.echo("   • Text files are only needed for initial indexing")
        click.echo("   • All document content is preserved in LlamaIndex storage")
        click.echo("   • You can always re-collect system info if needed")

        if not click.confirm("Remove text files to save space?"):
            click.echo("Cancelled.")
            return

    # Remove text files
    removed_size = 0
    for file in text_files:
        removed_size += file.stat().st_size
        file.unlink()

    click.echo(f"✅ Removed {len(text_files)} text files")
    click.echo(f"💾 Freed {removed_size:,} bytes of disk space")
    click.echo("🔍 Query functionality preserved in LlamaIndex storage")


@cli.command()
@click.option(
    "--system-info-dir",
    help="Directory containing system info files (overrides config)",
)
@click.pass_context
def status(ctx: click.Context, system_info_dir: str):
    """Show status of collected system information."""
    config_path = ctx.obj.get("config_path") if ctx.obj else None
    cfg = get_config(config_path)

    # Use config default if not specified
    system_info_dir = system_info_dir or cfg.system_info_dir
    info_dir = Path(system_info_dir)

    if not info_dir.exists():
        click.echo(f"❌ Directory '{system_info_dir}' does not exist.")
        click.echo("Run 'shellai collect' first.")
        return

    # Check text files
    text_files = list(info_dir.glob("*.txt"))

    # Check LlamaIndex storage
    storage_dir = info_dir / cfg.storage_dir
    has_storage = storage_dir.exists()

    click.echo(f"📁 System info directory: {info_dir.absolute()}")

    if text_files:
        total_size = sum(f.stat().st_size for f in text_files)
        click.echo(f"📄 Text files: {len(text_files)} files ({total_size:,} bytes)")
        for file in sorted(text_files):
            click.echo(f"  • {file.name} ({file.stat().st_size} bytes)")
    else:
        click.echo("📄 Text files: None (cleaned up)")

    if has_storage:
        storage_files = list(storage_dir.glob("*.json"))
        storage_size = sum(f.stat().st_size for f in storage_files) if storage_files else 0
        click.echo(f"💾 LlamaIndex storage: ✅ ({storage_size:,} bytes)")
        click.echo("🔍 Ready for queries!")

        if text_files:
            click.echo("\n💡 Tip: Run 'shellai cleanup' to remove redundant text files")
    else:
        click.echo("💾 LlamaIndex storage: ❌ Missing")
        if text_files:
            click.echo("Run 'shellai refresh' to create index from text files")
        else:
            click.echo("Run 'shellai collect' first to gather system data")


@cli.command()
@click.option(
    "--system-info-dir",
    help="Directory containing system info files (overrides config)",
)
@click.option("--model", help="Ollama model to use (overrides config)")
@click.pass_context
def refresh(ctx: click.Context, system_info_dir: str, model: str):
    """Refresh the LlamaIndex vector store with updated system information."""
    config_path = ctx.obj.get("config_path") if ctx.obj else None

    engine = SystemQueryEngine(
        system_info_dir=system_info_dir, model=model, config_path=config_path
    )

    if not engine.initialize():
        sys.exit(1)

    if engine.refresh_index():
        click.echo("✅ Index refreshed successfully!")
    else:
        click.echo("❌ Failed to refresh index.")
        sys.exit(1)


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
        import llama_index.core  # type: ignore # noqa: F401

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
    click.echo("  shellai refresh    # Refresh the vector index")
    click.echo("  shellai status     # Check collected info status")
    click.echo("  shellai config     # Manage configuration")


def main():
    """Main entry point for the CLI application."""
    cli()


if __name__ == "__main__":
    main()
