#!/usr/bin/env python3
"""
Obsidian Vault Search using ChromaDB
Search through indexed markdown files with semantic similarity.
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict, Any
import chromadb
from sentence_transformers import SentenceTransformer


class ObsidianVaultSearcher:
    def __init__(self, vault_path=None, db_path="./chroma_db"):
        if vault_path:
            self.vault_path = Path(vault_path).resolve()
        else:
            self.vault_path = None
        self.db_path = Path(db_path)
        
        # Initialize ChromaDB
        try:
            self.client = chromadb.PersistentClient(path=str(self.db_path))
            self.collection = self.client.get_collection("obsidian_vault")
            print(f"Connected to database: {self.db_path}")
            print(f"Collection contains {self.collection.count()} documents")
        except Exception as e:
            print(f"Error connecting to database: {e}")
            print("Make sure you've run index_notes.py first to create the database.")
            exit(1)
        
        # Initialize embedding model (same as indexer)
        print("Loading embedding model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Model loaded successfully")
    
    def search(self, query: str, n_results: int = 10, filter_metadata: Dict = None) -> Dict[str, Any]:
        """Search the indexed vault"""
        try:
            # Perform the search
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=filter_metadata
            )
            
            return results
        
        except Exception as e:
            print(f"Error during search: {e}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
    
    def format_results(self, results: Dict[str, Any], show_content: bool = True, 
                      max_content_length: int = 200) -> None:
        """Format and display search results"""
        documents = results.get('documents', [[]])[0]
        metadatas = results.get('metadatas', [[]])[0]
        distances = results.get('distances', [[]])[0]
        
        if not documents:
            print("No results found.")
            return
        
        print(f"\nFound {len(documents)} results:")
        print("=" * 80)
        
        # Group results by file
        file_results = {}
        for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances)):
            file_path = metadata['file_path']
            if file_path not in file_results:
                file_results[file_path] = []
            
            file_results[file_path].append({
                'content': doc,
                'metadata': metadata,
                'distance': distance,
                'rank': i + 1
            })
        
        # Display results grouped by file
        for file_path, file_chunks in file_results.items():
            print(f"\n📄 {file_path}")
            print(f"   Directory: {file_chunks[0]['metadata']['directory']}")
            print(f"   Chunks found: {len(file_chunks)}")
            
            # Show the best chunk for this file
            best_chunk = min(file_chunks, key=lambda x: x['distance'])
            print(f"   Best match (rank #{best_chunk['rank']}):")
            print(f"   Similarity: {1 - best_chunk['distance']:.3f}")
            
            if show_content:
                content = best_chunk['content']
                if len(content) > max_content_length:
                    content = content[:max_content_length] + "..."
                
                # Add some basic formatting
                lines = content.split('\n')
                for line in lines[:5]:  # Show first 5 lines
                    if line.strip():
                        print(f"   > {line.strip()}")
            
            print("-" * 40)
    
    def search_by_file_pattern(self, pattern: str, n_results: int = 20) -> Dict[str, Any]:
        """Search for files matching a pattern"""
        try:
            results = self.collection.query(
                query_texts=[""],  # Empty query for metadata-only search
                n_results=n_results,
                where={"file_path": {"$regex": f".*{pattern}.*"}}
            )
            return results
        except Exception as e:
            print(f"Error during pattern search: {e}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
    
    def search_by_directory(self, directory: str, query: str = "", n_results: int = 10) -> Dict[str, Any]:
        """Search within a specific directory"""
        filter_dict = {"directory": {"$regex": f".*{directory}.*"}}
        
        if query:
            return self.search(query, n_results, filter_dict)
        else:
            # List files in directory
            try:
                results = self.collection.get(
                    where=filter_dict,
                    limit=n_results
                )
                return {
                    "documents": [results["documents"]],
                    "metadatas": [results["metadatas"]], 
                    "distances": [[0.0] * len(results["documents"])]
                }
            except Exception as e:
                print(f"Error searching directory: {e}")
                return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
    
    def get_file_content(self, file_path: str) -> List[str]:
        """Get all chunks for a specific file"""
        try:
            results = self.collection.get(
                where={"file_path": file_path}
            )
            
            if not results["documents"]:
                print(f"No content found for: {file_path}")
                return []
            
            # Sort chunks by index
            chunks_with_metadata = list(zip(results["documents"], results["metadatas"]))
            chunks_with_metadata.sort(key=lambda x: x[1]["chunk_index"])
            
            return [chunk[0] for chunk in chunks_with_metadata]
        
        except Exception as e:
            print(f"Error retrieving file content: {e}")
            return []
    
    def list_files(self, limit: int = 50) -> None:
        """List all indexed files"""
        try:
            # Get unique files
            all_metadata = self.collection.get()["metadatas"]
            unique_files = set()
            
            for metadata in all_metadata:
                unique_files.add(metadata["file_path"])
            
            files = sorted(list(unique_files))
            
            print(f"\nIndexed files ({len(files)} total):")
            print("=" * 60)
            
            for i, file_path in enumerate(files[:limit], 1):
                print(f"{i:3d}. {file_path}")
            
            if len(files) > limit:
                print(f"\n... and {len(files) - limit} more files")
                print("Use --limit to see more files")
        
        except Exception as e:
            print(f"Error listing files: {e}")
    
    def interactive_search(self):
        """Interactive search mode"""
        print("\n🔍 Interactive Search Mode")
        print("Commands:")
        print("  search <query>     - Semantic search")
        print("  file <pattern>     - Find files by name pattern")
        print("  dir <directory>    - List files in directory")
        print("  content <filepath> - Show full content of file")
        print("  list              - List all indexed files")
        print("  quit              - Exit")
        print()
        
        while True:
            try:
                command = input("obsidian> ").strip()
                
                if not command:
                    continue
                
                if command.lower() in ['quit', 'exit', 'q']:
                    break
                
                parts = command.split(' ', 1)
                cmd = parts[0].lower()
                
                if cmd == 'search' and len(parts) > 1:
                    query = parts[1]
                    results = self.search(query)
                    self.format_results(results)
                
                elif cmd == 'file' and len(parts) > 1:
                    pattern = parts[1]
                    results = self.search_by_file_pattern(pattern)
                    self.format_results(results, show_content=False)
                
                elif cmd == 'dir' and len(parts) > 1:
                    directory = parts[1]
                    results = self.search_by_directory(directory)
                    self.format_results(results, show_content=False)
                
                elif cmd == 'content' and len(parts) > 1:
                    file_path = parts[1]
                    chunks = self.get_file_content(file_path)
                    if chunks:
                        print(f"\n📄 Content of {file_path}:")
                        print("=" * 60)
                        for i, chunk in enumerate(chunks):
                            print(f"\n--- Chunk {i+1} ---")
                            print(chunk)
                
                elif cmd == 'list':
                    self.list_files()
                
                else:
                    print("Unknown command. Type 'quit' to exit.")
            
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(description='Search Obsidian vault with ChromaDB')
    parser.add_argument('query', nargs='?', help='Search query')
    parser.add_argument('--vault-path', 
                       help='Path to Obsidian vault directory (will prompt if not provided)')
    parser.add_argument('--db-path', default='./chroma_db',
                       help='Path to ChromaDB database (default: ./chroma_db)')
    parser.add_argument('-n', '--results', type=int, default=10,
                       help='Number of results to return (default: 10)')
    parser.add_argument('--no-content', action='store_true',
                       help='Do not show content preview')
    parser.add_argument('--max-length', type=int, default=200,
                       help='Maximum content preview length (default: 200)')
    parser.add_argument('--file-pattern', 
                       help='Search for files matching pattern')
    parser.add_argument('--directory',
                       help='Search within specific directory')
    parser.add_argument('--list-files', action='store_true',
                       help='List all indexed files')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Start interactive search mode')
    parser.add_argument('--json', action='store_true',
                       help='Output results as JSON')
    
    args = parser.parse_args()
    
    # Get vault path from argument or prompt user (only needed for reference, not functionality)
    vault_path = args.vault_path
    if not vault_path and args.interactive:
        vault_path = input("Enter path to your Obsidian vault (for reference): ").strip()
    
    searcher = ObsidianVaultSearcher(vault_path=vault_path, db_path=args.db_path)
    
    if args.interactive:
        searcher.interactive_search()
        return
    
    if args.list_files:
        searcher.list_files()
        return
    
    if args.file_pattern:
        results = searcher.search_by_file_pattern(args.file_pattern, args.results)
    elif args.directory:
        if args.query:
            results = searcher.search_by_directory(args.directory, args.query, args.results)
        else:
            results = searcher.search_by_directory(args.directory, "", args.results)
    elif args.query:
        results = searcher.search(args.query, args.results)
    else:
        parser.print_help()
        return
    
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        searcher.format_results(results, 
                              show_content=not args.no_content,
                              max_content_length=args.max_length)


if __name__ == "__main__":
    main()