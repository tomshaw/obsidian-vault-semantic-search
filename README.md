# Obsidian Vault Semantic Search

A powerful semantic search tool for Obsidian vaults using ChromaDB and sentence transformers. Index your markdown notes and search them using natural language queries with AI-powered semantic similarity.

## Features

- **Semantic Search**: Find notes based on meaning, not just keywords
- **Fast Indexing**: Efficiently processes large vaults with chunking and embeddings
- **Interactive Mode**: Real-time search with multiple query types
- **Flexible Output**: JSON export, customizable result formatting
- **Vault-Agnostic**: Works with any Obsidian vault structure
- **Smart Filtering**: Excludes system directories and supports pattern matching

## Installation

### Prerequisites

- Python 3.13.5 or higher
- [uv](https://docs.astral.sh/uv/) package manager

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd obsidian-vault-search
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

## Quick Start

### 1. Index Your Vault

```bash
# Provide vault path as argument
uv run index_notes.py /path/to/your/obsidian/vault

# Or run without arguments to be prompted
uv run index_notes.py
```

### 2. Search Your Notes

```bash
# Basic semantic search
uv run search_notes.py "machine learning algorithms"

# Interactive mode for multiple queries
uv run search_notes.py --interactive

# Search with more results
uv run search_notes.py "productivity tips" -n 20
```

## Usage

### Indexing Options

```bash
# Basic indexing
uv run index_notes.py /path/to/vault

# Custom database location
uv run index_notes.py /path/to/vault --db-path ./my_custom_db

# Don't clear existing data (append mode)
uv run index_notes.py /path/to/vault --no-clear

# Show statistics only
uv run index_notes.py /path/to/vault --stats-only
```

### Search Options

```bash
# Semantic search with custom result count
uv run search_notes.py "search query" -n 15

# Search by filename pattern
uv run search_notes.py --file-pattern "meeting"

# Search within specific directory
uv run search_notes.py --directory "projects" "status update"

# List all indexed files
uv run search_notes.py --list-files

# Export results as JSON
uv run search_notes.py "query" --json

# Hide content preview
uv run search_notes.py "query" --no-content
```

### Interactive Mode

Launch interactive mode for exploratory searching:

```bash
uv run search_notes.py --interactive
```

Interactive commands:
- `search <query>` - Semantic search
- `file <pattern>` - Find files by name pattern  
- `dir <directory>` - List files in directory
- `content <filepath>` - Show full content of file
- `list` - List all indexed files
- `quit` - Exit

## How It Works

1. **Content Extraction**: Strips markdown syntax while preserving meaning
2. **Intelligent Chunking**: Splits content into 500-word overlapping chunks
3. **Embedding Generation**: Uses `all-MiniLM-L6-v2` model for semantic embeddings
4. **Vector Storage**: Stores embeddings in ChromaDB for fast similarity search
5. **Smart Retrieval**: Groups results by file and ranks by semantic similarity

## Configuration

The system automatically:
- Excludes `System` directories from indexing
- Skips hidden directories (starting with `.`)
- Handles multiple text encodings (UTF-8, Latin-1)
- Creates overlapping chunks for better context preservation

## Development

This project uses modern Python tooling:

- **uv** for fast dependency management
- **ChromaDB** for vector database
- **sentence-transformers** for embeddings
- **pathlib** for cross-platform file handling

See `CLAUDE.md` for detailed development guidance.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License

Copyright (c) 2025 Tom Shaw

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Acknowledgments

- [Obsidian](https://obsidian.md/) for the amazing note-taking platform
- [ChromaDB](https://www.trychroma.com/) for the vector database
- [sentence-transformers](https://www.sbert.net/) for semantic embeddings