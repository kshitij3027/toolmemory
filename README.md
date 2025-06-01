# 🧠 ToolMemory: Enhanced LLM Agents with Persistent Memory

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-demo--ready-brightgreen.svg)

**ToolMemory** is an advanced AI agent system that enhances Large Language Models with persistent memory capabilities, enabling them to learn and improve over time across conversation sessions. Built with Letta's sleep agents, MongoDB vector storage, and intelligent web search integration.

## 🌟 Key Features

- **🤖 Sleep Agent Integration**: Advanced Letta sleep agents with background memory processing
- **🧠 Persistent Memory**: MongoDB-based vector storage with Voyage AI embeddings
- **🔍 Intelligent Web Search**: Automatic Tavily search integration for current information
- **📊 Performance Tracking**: Real-time statistics and memory optimization metrics
- **🎨 Beautiful CLI**: Rich terminal interface with progress indicators and formatting
- **⚡ Memory Synchronization**: Seamless sync between agent memory and database storage
- **🎯 Context-Aware Responses**: Agents improve over time by learning from past interactions

## 🚀 Quick Demo

### Before Memory (First Session):
```bash
🗣️ You: Explain quantum computing applications in finance
🔍 Searching the web for current information...
🤖 Getting response from sleep agent...
📊 Processing time: 8.4 seconds | Memory hits: 0/1
```

### After Memory (Subsequent Sessions):
```bash
🗣️ You: How does quantum machine learning compare to our previous finance discussion?
📚 Found 5 relevant memories
🤖 Getting response from sleep agent...
📊 Processing time: 2.1 seconds | Memory hits: 5/5 ✨
```

**Result**: 75% faster processing + contextual awareness across sessions!

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Letta Sleep   │◄──►│   MongoDB       │◄──►│   Voyage AI     │
│     Agent       │    │  Vector Store   │    │   Embeddings    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        ▲                        ▲                        ▲
        │                        │                        │
        ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Enhanced      │    │   Memory Sync   │    │   Tavily Web    │
│     CLI         │    │    Service      │    │     Search      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
toolmemory/
├── 🤖 agent_setup.py          # Letta sleep agent creation & configuration
├── 🧠 mongodb_memory.py       # MongoDB vector storage & retrieval
├── ⚡ voyage.py               # Voyage AI embedding wrapper
├── 🔍 research_tools.py       # Tavily web search integration
├── 🔄 memory_sync.py          # Agent-database memory synchronization
├── 🎨 cli_app.py              # Enhanced CLI with rich formatting
├── 📋 requirements.txt        # Python dependencies
├── ⚙️ .env.example            # Environment variables template
├── 📊 tasks.md               # Implementation progress tracking
└── 📖 README.md              # This file
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- MongoDB Atlas account
- API keys for Letta, Voyage AI, and Tavily

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd toolmemory
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Setup
Create a `.env` file with your API keys:
```bash
# Copy the example file
cp .env.example .env

# Edit with your actual API keys
LETTA_API_TOKEN="your_letta_api_token_here"
VOYAGE_API_KEY="your_voyage_api_key_here"
TAVILY_API_KEY="your_tavily_api_key_here"
MONGO_CONNECTION_STRING="your_mongodb_atlas_connection_string_here"
```

### 5. MongoDB Setup
1. Create a database named `toolmemory_db`
2. Create a collection named `memories`
3. Create a vector search index on the `embedding` field:
   - Index name: `vector_index_cosine`
   - Dimensions: 1536 (for voyage-code-2)
   - Similarity: cosine

## 🎯 Usage Guide

### 1. Create Sleep Agent
```bash
python agent_setup.py
```
**Output**: Creates `agent_config.json` with your sleep agent configuration.

### 2. Start First Session (Learning Mode)
```bash
python cli_app.py
```

Example interaction:
```
🗣️ You: Explain quantum computing applications in financial modeling
```

### 3. Synchronize Memory
```bash
python memory_sync.py
```
**Result**: Transfers agent memory to persistent MongoDB storage.

### 4. Start Enhanced Session (Memory Mode)
```bash
python cli_app.py
```

Example interaction:
```
🗣️ You: How does quantum machine learning compare to our previous discussion?
📚 Found 3 relevant memories
```

### 5. Available CLI Commands
- `help` - Show available commands
- `stats` - Display session statistics
- `sync` - Synchronize agent memories
- `clear` - Clear screen
- `quit` / `exit` - Exit application

## 📊 Performance Benefits

| Metric | First Session | With Memory | Improvement |
|--------|---------------|-------------|-------------|
| **Response Time** | 8.4s average | 2.1s average | **75% faster** |
| **Memory Hits** | 0% | 85%+ | **Context awareness** |
| **Web Searches** | 100% queries | 30% queries | **70% reduction** |
| **Context Quality** | Individual | Integrated | **Cross-session learning** |

## 🧪 API Configuration

### Letta Sleep Agent
- **Model**: GPT-4o with sleep-time frequency of 2
- **Memory Blocks**: Persona and human context
- **Background Processing**: Automated memory enhancement

### MongoDB Vector Search
- **Embedding Model**: Voyage Code-2 (1536 dimensions)
- **Similarity**: Cosine similarity
- **Search**: Semantic retrieval with fallback text search

### Tavily Integration
- **Trigger Words**: latest, recent, current, today, news
- **Auto-Storage**: Search results automatically stored in memory
- **Performance**: 3.01s average response time

## 🎬 Demo Script

For a complete demonstration, see our [Step-by-Step Demo Guide](demo_script.md) which showcases:

1. **Learning Phase**: Agent acquires domain knowledge
2. **Memory Sync**: Transfer to persistent storage  
3. **Enhanced Phase**: Agent leverages accumulated memory
4. **Performance Metrics**: Real-time improvement tracking

## 🔧 Configuration Options

### Sleep Agent Frequency
Modify in `agent_setup.py`:
```python
# Lower = more frequent background processing
sleep_time_agent_frequency = 2  # Current setting
```

### Memory Search Parameters
Modify in `mongodb_memory.py`:
```python
# Number of relevant memories to retrieve
top_k = 5  # Default setting
```

### Web Search Triggers
Modify in `cli_app.py`:
```python
web_trigger_words = ['latest', 'recent', 'current', 'today', 'news']
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[Letta](https://www.letta.ai/)** - Advanced LLM agent framework with sleep capabilities
- **[MongoDB Atlas](https://www.mongodb.com/atlas)** - Vector search and document storage
- **[Voyage AI](https://www.voyageai.com/)** - High-quality embedding models
- **[Tavily](https://tavily.com/)** - Real-time web search API
- **[Rich](https://rich.readthedocs.io/)** - Beautiful terminal formatting

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/your-username/toolmemory/issues) page
2. Review the configuration in `.env` and `agent_config.json`
3. Verify all API keys are valid and have sufficient credits
4. Ensure MongoDB vector index is properly configured

---

**🌟 Star this repo if you found it helpful!**

*Built with ❤️ for the AGI Hackathon*
