#!/usr/bin/env python3
"""
Obsidian Vault Indexer using ChromaDB
Indexes all markdown files in the vault excluding the System directory.
"""

import os
import re
import hashlib
import argparse
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer


class ObsidianVaultIndexer:
    def __init__(self, vault_path, db_path="./chroma_db"):
        self.vault_path = Path(vault_path).resolve()
        self.db_path = Path(db_path)
        
        # Validate vault path exists
        if not self.vault_path.exists():
            raise FileNotFoundError(f"Vault path does not exist: {self.vault_path}")
        if not self.vault_path.is_dir():
            raise NotADirectoryError(f"Vault path is not a directory: {self.vault_path}")
        
        print(f"Vault path: {self.vault_path}")
        print(f"Database path: {self.db_path}")
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path=str(self.db_path))
        self.collection = self.client.get_or_create_collection(
            name="obsidian_vault",
            metadata={"description": "Obsidian vault notes collection"}
        )
        
        # Initialize embedding model
        print("Loading embedding model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Model loaded successfully")
    
    def extract_content(self, file_path):
        """Extract and clean markdown content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encoding if UTF-8 fails
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        # Remove markdown syntax
        content = re.sub(r'#{1,6}\s+', '', content)  # Headers
        content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)  # Bold
        content = re.sub(r'\*(.*?)\*', r'\1', content)  # Italic
        content = re.sub(r'__(.*?)__', r'\1', content)  # Underline
        content = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', content)  # Links
        content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)  # Code blocks
        content = re.sub(r'`([^`]+)`', r'\1', content)  # Inline code
        content = re.sub(r'^\s*[-*+]\s+', '', content, flags=re.MULTILINE)  # List items
        content = re.sub(r'^\s*\d+\.\s+', '', content, flags=re.MULTILINE)  # Numbered lists
        content = re.sub(r'>\s+', '', content)  # Blockquotes
        
        # Clean up extra whitespace
        content = re.sub(r'\n\s*\n', '\n\n', content)
        content = content.strip()
        
        return content
    
    def chunk_content(self, content, chunk_size=500, overlap=50):
        """Split content into overlapping chunks"""
        if not content.strip():
            return []
        
        words = content.split()
        if len(words) <= chunk_size:
            return [content]
        
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks
    
    def get_markdown_files(self):
        """Get all markdown files excluding System directory"""
        markdown_files = []
        
        for root, dirs, files in os.walk(self.vault_path):
            # Skip System directory
            if 'System' in dirs:
                dirs.remove('System')
            
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if file.endswith('.md'):
                    file_path = Path(root) / file
                    markdown_files.append(file_path)
        
        return markdown_files
    
    def clear_collection(self):
        """Clear all documents from the collection"""
        try:
            # Get all document IDs
            all_docs = self.collection.get()
            if all_docs['ids']:
                self.collection.delete(ids=all_docs['ids'])
                print(f"Cleared {len(all_docs['ids'])} existing documents")
        except Exception as e:
            print(f"Error clearing collection: {e}")
    
    def index_vault(self, clear_existing=True):
        """Index all markdown files in the vault"""
        if clear_existing:
            self.clear_collection()
        
        markdown_files = self.get_markdown_files()
        print(f"Found {len(markdown_files)} markdown files to index")
        
        total_chunks = 0
        failed_files = []
        
        for i, file_path in enumerate(markdown_files, 1):
            try:
                relative_path = file_path.relative_to(self.vault_path)
                print(f"[{i}/{len(markdown_files)}] Indexing: {relative_path}")
                
                content = self.extract_content(file_path)
                if not content.strip():
                    print(f"  Skipping empty file: {relative_path}")
                    continue
                
                chunks = self.chunk_content(content)
                if not chunks:
                    print(f"  No chunks generated for: {relative_path}")
                    continue
                
                # Prepare batch data
                documents = []
                ids = []
                metadatas = []
                
                for j, chunk in enumerate(chunks):
                    doc_id = hashlib.md5(f"{relative_path}_{j}".encode()).hexdigest()
                    
                    documents.append(chunk)
                    ids.append(doc_id)
                    metadatas.append({
                        "file_path": str(relative_path),
                        "chunk_index": j,
                        "file_name": file_path.name,
                        "directory": str(relative_path.parent),
                        "total_chunks": len(chunks)
                    })
                
                # Add to collection
                self.collection.add(
                    documents=documents,
                    ids=ids,
                    metadatas=metadatas
                )
                
                total_chunks += len(chunks)
                print(f"  Added {len(chunks)} chunks")
                
            except Exception as e:
                print(f"  Error indexing {file_path}: {e}")
                failed_files.append(str(file_path))
        
        print(f"\nIndexing complete!")
        print(f"Total files processed: {len(markdown_files) - len(failed_files)}")
        print(f"Total chunks indexed: {total_chunks}")
        
        if failed_files:
            print(f"Failed files ({len(failed_files)}):")
            for file in failed_files:
                print(f"  {file}")
        
        # Verify collection count
        collection_count = self.collection.count()
        print(f"Collection now contains: {collection_count} documents")
    
    def get_stats(self):
        """Get collection statistics"""
        try:
            count = self.collection.count()
            print(f"Total documents in collection: {count}")
            
            if count > 0:
                # Sample some metadata
                sample = self.collection.get(limit=5)
                print("\nSample documents:")
                for i, metadata in enumerate(sample['metadatas']):
                    print(f"  {i+1}. {metadata['file_path']} (chunk {metadata['chunk_index']})")
        
        except Exception as e:
            print(f"Error getting stats: {e}")


def main():
    parser = argparse.ArgumentParser(description='Index Obsidian vault with ChromaDB')
    parser.add_argument('vault_path', nargs='?',
                       help='Path to Obsidian vault directory')
    parser.add_argument('--db-path', default='./chroma_db', 
                       help='Path to ChromaDB database (default: ./chroma_db)')
    parser.add_argument('--no-clear', action='store_true',
                       help='Do not clear existing collection before indexing')
    parser.add_argument('--stats-only', action='store_true',
                       help='Only show collection statistics, do not index')
    
    args = parser.parse_args()
    
    # Get vault path from argument or prompt user
    vault_path = args.vault_path
    if not vault_path:
        vault_path = input("Enter path to your Obsidian vault: ").strip()
        if not vault_path:
            print("Error: Vault path is required")
            return
    
    try:
        indexer = ObsidianVaultIndexer(vault_path=vault_path, db_path=args.db_path)
    except (FileNotFoundError, NotADirectoryError) as e:
        print(f"Error: {e}")
        return
    
    if args.stats_only:
        indexer.get_stats()
    else:
        indexer.index_vault(clear_existing=not args.no_clear)
        indexer.get_stats()


if __name__ == "__main__":
    main()