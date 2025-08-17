# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Obsidian vault indexing and search system using ChromaDB and semantic embeddings. The project enables semantic search across markdown files in an Obsidian vault, excluding the System directory.

## Commands

### Dependencies Management
```bash
uv sync                    # Install dependencies using uv
```

### Core Operations
```bash
uv run index_notes.py /path/to/vault           # Index vault at specified path
uv run index_notes.py                          # Prompts for vault path
uv run search_notes.py "search query"          # Search indexed content
uv run search_notes.py --interactive           # Interactive search mode (prompts for vault path)
uv run main.py                                 # Run basic hello world (placeholder)
```

### Indexing Options
```bash
uv run index_notes.py /path/to/vault --db-path ./custom_db    # Use custom database path
uv run index_notes.py /path/to/vault --no-clear               # Don't clear existing data
uv run index_notes.py /path/to/vault --stats-only             # Show statistics only
```

### Search Options
```bash
uv run search_notes.py "query" -n 20                    # Return 20 results
uv run search_notes.py --file-pattern "filename"        # Search by filename
uv run search_notes.py --directory "folder"             # Search in directory
uv run search_notes.py --list-files                     # List all indexed files
uv run search_notes.py --json                           # Output as JSON
```

## Architecture

### Core Components

- **ObsidianVaultIndexer** (`index_notes.py`): Processes markdown files, extracts content, creates text chunks, and stores embeddings in ChromaDB
- **ObsidianVaultSearcher** (`search_notes.py`): Provides semantic search capabilities over the indexed content
- **ChromaDB Database**: Persistent vector database stored in `./chroma_db/`

### Key Design Patterns

1. **Semantic Chunking**: Content is split into overlapping 500-word chunks with 50-word overlap for better search granularity
2. **Markdown Processing**: Strips markdown syntax while preserving content structure
3. **Embedding Model**: Uses `all-MiniLM-L6-v2` from sentence-transformers for consistent embeddings
4. **Vault Structure**: Automatically excludes System directory and hidden directories from indexing

### Data Flow

1. **Indexing**: Markdown files → Content extraction → Text chunking → Embedding generation → ChromaDB storage
2. **Searching**: Query → Embedding generation → Similarity search → Result formatting → Display

### Database Schema

Each document chunk includes metadata:
- `file_path`: Relative path from vault root
- `chunk_index`: Position within the file
- `file_name`: Base filename
- `directory`: Parent directory path
- `total_chunks`: Total chunks for the file

## Development Notes

- The vault path must be provided as a command line argument or entered when prompted
- Database path defaults to `./chroma_db` but can be customized
- Interactive mode supports multiple search types: semantic search, file pattern matching, directory browsing
- Content extraction handles multiple encodings (UTF-8, Latin-1) for compatibility