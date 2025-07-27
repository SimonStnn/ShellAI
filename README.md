# ShellAI

Natural language to safe bash commands. ShellAI turns plain-text instructions into explainable, testable shell scripts and provides natural language querying of your system information.

## 🚀 Features

- **Natural Language System Queries**: Ask questions about your system in plain English
- **Comprehensive System Info Collection**: Automatically gather system information for AI analysis
- **LLM-Powered Responses**: Uses LlamaIndex + Ollama for intelligent responses
- **Command-Line Interface**: Easy-to-use CLI for all operations
- **Extensible**: Add custom system commands and queries

## 🧱 Project Structure

```
ShellAI/
├── shellai/                    # Main package
│   ├── __init__.py
│   ├── cli.py                  # Command-line interface
│   ├── collect_info.py         # System information collector
│   ├── ask.py                  # Natural language query engine
│   └── train.py                # Training utilities
├── examples/                   # Standalone examples
│   ├── collect_info.py         # Minimal info collector
│   └── ask.py                  # Minimal query interface
├── system_info/               # Generated system data (after running collect)
│   ├── os.txt
│   ├── disk.txt
│   ├── memory.txt
│   └── ...
├── requirements.txt
├── setup.py
└── README.md
```

## ✅ Requirements

- **Python 3.10+**
- **Ollama** (for LLM functionality)
- **LlamaIndex** (installed automatically)

## 🔧 Installation

### Option 1: Install from source (recommended)

```bash
# Clone the repository
git clone <repository-url>
cd ShellAI

# Install in development mode
pip install -e .[dev]

# Or install dependencies manually
pip install -r requirements.txt
```

### Option 2: Install Ollama

```bash
# Install Ollama (visit https://ollama.ai for installation instructions)
# Then pull a model:
ollama pull mistral
```

## 🚀 Quick Start

### 1. Check Setup

```bash
shellai setup
```

This will verify that all dependencies are installed and Ollama is running.

### 2. Collect System Information

```bash
shellai collect
```

This gathers comprehensive system information including:
- OS details (`uname -a`)
- Disk usage (`df -h`) 
- Memory info (`free -m`)
- Running processes (`ps aux`)
- Network configuration (`ip addr`)
- CPU information (`lscpu`)
- And more...

### 3. Ask Questions About Your System

```bash
shellai ask
```

Start an interactive session where you can ask natural language questions like:
- "How much free RAM do I have?"
- "What processes are using the most CPU?"
- "Show me disk usage"
- "What's my network configuration?"

### 4. Single Question Mode

```bash
shellai ask --question "How much free disk space do I have?"
```

## 📋 CLI Commands

### Core Commands

```bash
# Collect system information
shellai collect [--output-dir DIR] [--custom-command name:command]

# Ask questions (interactive)
shellai ask [--model MODEL] [--system-info-dir DIR]

# Ask single question
shellai ask --question "your question here"

# Check status of collected info
shellai status [--system-info-dir DIR]

# Verify setup
shellai setup
```

### Examples

```bash
# Collect info with custom commands
shellai collect --custom-command "docker:docker ps -a" --custom-command "logs:tail -100 /var/log/syslog"

# Use different Ollama model
shellai ask --model llama2

# Use different system info directory
shellai ask --system-info-dir /path/to/custom/info
```

## 🛠 Standalone Usage

If you prefer minimal standalone scripts, use the examples:

```bash
# Collect system info (minimal version)
python3 examples/collect_info.py

# Ask questions (minimal version)  
python3 examples/ask.py
```

## 🎯 Example Usage

```bash
$ shellai collect
🔍 Collecting system information...
  📋 Running: uname -a
  ✅ Saved: os.txt
  📋 Running: df -h
  ✅ Saved: disk.txt
  ...
✅ Collection complete!

$ shellai ask
🤖 Initializing with model: mistral
📚 Loading system information...
📄 Loaded 10 system info files
🔍 Creating search index...
✅ Ready to answer questions!

❓ Ask about your system: How much free RAM do I have?
🤔 Thinking about: How much free RAM do I have?

💡 Based on your system information, you have 2.1 GB of free RAM available 
out of 8.0 GB total memory. Your memory usage is currently at about 74%.

❓ Ask about your system: What processes are using the most CPU?
🤔 Thinking about: What processes are using the most CPU?

💡 According to your process list, the top CPU-consuming processes are:
1. python3 (12.5% CPU)
2. firefox (8.2% CPU) 
3. code (5.1% CPU)
...
```

## 🔧 Advanced Usage

### Custom System Commands

Add your own system information commands:

```bash
shellai collect --custom-command "docker:docker ps -a" \
                --custom-command "services:systemctl --failed" \
                --custom-command "logs:journalctl -n 50"
```

### Different Models

Use different Ollama models:

```bash
# List available models
ollama list

# Use specific model
shellai ask --model llama2
shellai ask --model codellama
```

### API Usage

Use ShellAI programmatically:

```python
from shellai import SystemInfoCollector, SystemQueryEngine

# Collect info
collector = SystemInfoCollector("my_system_info")
collector.collect_all()

# Query system
engine = SystemQueryEngine("my_system_info", model="mistral")
engine.initialize()
response = engine.query("How much disk space is available?")
print(response)
```

## 🐛 Troubleshooting

### Ollama Issues

```bash
# Check if Ollama is running
ollama list

# Start Ollama service
ollama serve

# Pull required model
ollama pull mistral
```

### Missing System Info

```bash
# Re-collect system information
shellai collect

# Check what was collected
shellai status
```

### Python Dependencies

```bash
# Reinstall dependencies
pip install -e .[dev]

# Or install manually
pip install llama-index llama-index-llms-ollama
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Format code: `black shellai tests`
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [LlamaIndex](https://github.com/jerryjliu/llama_index) for the RAG framework
- [Ollama](https://ollama.ai) for local LLM hosting
- The open-source community for inspiration and tools
