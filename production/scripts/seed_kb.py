#!/usr/bin/env python3
"""
Seed Knowledge Base Script for Customer Success FTE
Loads product documentation into the knowledge base with embeddings.

Usage:
    python seed_kb.py [--file PATH] [--batch-size N]

Options:
    --file PATH         Path to product docs file (default: context/product-docs.md)
    --batch-size N      Number of entries to insert at once (default: 10)
"""

import asyncio
import asyncpg
import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict
import hashlib

# Database configuration
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "database": os.getenv("POSTGRES_DB", "fte_db"),
    "user": os.getenv("POSTGRES_USER", "fte_user"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
}

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


async def get_connection():
    """Get database connection."""
    return await asyncpg.connect(**DB_CONFIG)


def parse_product_docs(file_path: str) -> List[Dict[str, str]]:
    """Parse product documentation into knowledge base entries."""
    file = Path(file_path)
    
    if not file.exists():
        print(f"File not found: {file_path}")
        sys.exit(1)
    
    content = file.read_text()
    
    # Parse markdown into sections
    entries = []
    current_title = None
    current_content = []
    
    for line in content.split('\n'):
        if line.startswith('## Feature '):
            # Save previous entry
            if current_title and current_content:
                entries.append({
                    "title": current_title,
                    "content": '\n'.join(current_content).strip(),
                    "category": "features"
                })
            
            # Start new entry
            current_title = line.replace('## ', '').strip()
            current_content = []
        elif line.startswith('## '):
            # Save previous entry
            if current_title and current_content:
                entries.append({
                    "title": current_title,
                    "content": '\n'.join(current_content).strip(),
                    "category": "general"
                })
            
            current_title = line.replace('## ', '').strip()
            current_content = []
        else:
            if current_title:
                current_content.append(line)
    
    # Save last entry
    if current_title and current_content:
        entries.append({
            "title": current_title,
            "content": '\n'.join(current_content).strip(),
            "category": "general"
        })
    
    return entries


async def generate_embedding(text: str) -> List[float]:
    """Generate embedding for text using OpenAI API."""
    if not OPENAI_API_KEY:
        print("Warning: OPENAI_API_KEY not set. Using placeholder embeddings.")
        # Return placeholder embedding (1536 dimensions for text-embedding-ada-002)
        import random
        random.seed(hashlib.md5(text.encode()).hexdigest())
        return [random.uniform(-0.1, 0.1) for _ in range(1536)]
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        
        return response.data[0].embedding
    
    except Exception as e:
        print(f"Error generating embedding: {e}")
        # Return placeholder on error
        import random
        random.seed(hashlib.md5(text.encode()).hexdigest())
        return [random.uniform(-0.1, 0.1) for _ in range(1536)]


async def insert_knowledge_base(entries: List[Dict[str, str]], batch_size: int = 10):
    """Insert knowledge base entries into database."""
    conn = await get_connection()
    
    try:
        print(f"Inserting {len(entries)} knowledge base entries...")
        
        for i in range(0, len(entries), batch_size):
            batch = entries[i:i + batch_size]
            
            for idx, entry in enumerate(batch, start=i+1):
                title = entry["title"]
                content = entry["content"]
                category = entry["category"]
                
                # Check if entry already exists
                exists = await conn.fetchval("""
                    SELECT id FROM knowledge_base WHERE title = $1
                """, title)
                
                if exists:
                    print(f"  [{idx}/{len(entries)}] Skipping (exists): {title}")
                    continue
                
                # Generate embedding
                print(f"  [{idx}/{len(entries)}] Generating embedding: {title}")
                embedding = await generate_embedding(f"{title}\n{content}")
                
                # Insert into database
                await conn.execute("""
                    INSERT INTO knowledge_base (title, content, category, embedding)
                    VALUES ($1, $2, $3, $4::vector)
                """, title, content, category, embedding)
                
                print(f"  [{idx}/{len(entries)}] ✓ Inserted: {title}")
            
            print(f"  → Batch complete ({min(i + batch_size, len(entries))}/{len(entries)})")
        
        print(f"\n✓ Knowledge base seeding complete!")
        print(f"  Total entries: {len(entries)}")
        
    finally:
        await conn.close()


async def clear_knowledge_base():
    """Clear all knowledge base entries."""
    conn = await get_connection()
    
    try:
        print("Clearing knowledge base...")
        deleted = await conn.fetchval("DELETE FROM knowledge_base")
        print(f"✓ Cleared {deleted} entries")
        
    finally:
        await conn.close()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Seed knowledge base with product documentation")
    parser.add_argument("--file", default="context/product-docs.md", 
                        help="Path to product docs file")
    parser.add_argument("--batch-size", type=int, default=10,
                        help="Batch size for inserts")
    parser.add_argument("--clear", action="store_true",
                        help="Clear knowledge base before seeding")
    
    args = parser.parse_args()
    
    if args.clear:
        await clear_knowledge_base()
    
    # Parse product docs
    print(f"Parsing product docs from: {args.file}")
    entries = parse_product_docs(args.file)
    print(f"Found {len(entries)} knowledge base entries\n")
    
    # Insert into database
    await insert_knowledge_base(entries, batch_size=args.batch_size)


if __name__ == "__main__":
    asyncio.run(main())
