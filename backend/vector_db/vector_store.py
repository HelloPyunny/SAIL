from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from typing import List, Dict, Any
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class VectorStore:
    def __init__(self):
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.pinecone_environment = os.getenv("PINECONE_ENVIRONMENT", "us-east-1-aws")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.pinecone_api_key or not self.openai_api_key:
            raise ValueError("PINECONE_API_KEY and OPENAI_API_KEY are required.")
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=self.pinecone_api_key)
        
        # Initialize embedding model
        self.embeddings = OpenAIEmbeddings(openai_api_key=self.openai_api_key)
        
        # Index name
        self.index_name = "game-context"
        
        # If the index does not exist, create it
        self._create_index_if_not_exists()
        
        # Connect to the index
        self.index = self.pc.Index(self.index_name)
    
    def _create_index_if_not_exists(self):
        """If the index does not exist, create it."""
        if self.index_name not in self.pc.list_indexes().names():
            self.pc.create_index(
                name=self.index_name,
                dimension=1536,  # Dimension of OpenAI text-embedding-ada-002
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            # Wait for the index to be ready
            import time
            while not self.pc.describe_index(self.index_name).status['ready']:
                time.sleep(1)
    
    def add_player_context(self, player_id: str, context_data: Dict[str, Any]):
        """Adds player context to the vector database."""
        # Convert the context to text
        context_text = self._dict_to_text(context_data)
        
        # Create embedding
        embedding = self.embeddings.embed_query(context_text)
        
        # Create metadata and convert to Pinecone compatible format
        metadata = self._convert_metadata_for_pinecone({
            "player_id": player_id,
            "type": "player_context",
            "timestamp": str(datetime.now()),
            "text": context_text,
            **context_data
        })
        
        # Create vector ID
        vector_id = f"context_{player_id}_{datetime.now().timestamp()}"
        
        # Save to Pinecone
        self.index.upsert(
            vectors=[{
                "id": vector_id,
                "values": embedding,
                "metadata": metadata
            }]
        )
    
    def add_conversation(self, player_id: str, conversation: Dict[str, str]):
        """Adds conversation to the vector database."""
        conversation_text = f"{conversation['speaker']}: {conversation['message']}"
        
        # Create embedding
        embedding = self.embeddings.embed_query(conversation_text)
        
        # Create metadata
        metadata = {
            "player_id": player_id,
            "type": "conversation",
            "speaker": conversation["speaker"],
            "timestamp": conversation.get("timestamp", str(datetime.now())),
            "message": conversation["message"],
            "text": conversation_text
        }
        
        # Create vector ID
        vector_id = f"conv_{player_id}_{datetime.now().timestamp()}"
        
        # Save to Pinecone
        self.index.upsert(
            vectors=[{
                "id": vector_id,
                "values": embedding,
                "metadata": metadata
            }]
        )
    
    def search_similar_context(self, query: str, player_id: str, top_k: int = 5) -> List[Dict]:
        """Searches for similar contexts."""
        # Create query embedding
        query_embedding = self.embeddings.embed_query(query)
        
        # Search in Pinecone
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            filter={"player_id": player_id},
            include_metadata=True
        )
        
        # Format results
        formatted_results = []
        for match in results.matches:
            formatted_results.append({
                "content": match.metadata.get("text", ""),
                "metadata": match.metadata,
                "score": match.score
            })
        
        return formatted_results
    
    def get_player_history(self, player_id: str, limit: int = 20) -> List[Dict]:
        """Gets the entire history of a player."""
        # Search for all player-related data (full search with empty query)
        dummy_embedding = [0.0] * 1536  # 1536-dimensional 0 vector
        
        results = self.index.query(
            vector=dummy_embedding,
            top_k=limit,
            filter={"player_id": player_id},
            include_metadata=True
        )
        
        # Sort by timestamp
        history = []
        for match in results.matches:
            history.append({
                "content": match.metadata.get("text", ""),
                "metadata": match.metadata,
                "score": match.score
            })
        
        # Sort by timestamp
        history.sort(key=lambda x: x["metadata"].get("timestamp", ""))
        
        return history
    
    def _convert_metadata_for_pinecone(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Converts metadata to Pinecone compatible format."""
        converted_metadata = {}
        
        for key, value in metadata.items():
            if value is None:
                continue
            elif isinstance(value, (str, int, float, bool)):
                converted_metadata[key] = value
            elif isinstance(value, list):
                # Convert all list elements to strings for Pinecone compatibility
                converted_metadata[key] = [str(item) for item in value]
            else:
                # Convert other types (dict, objects) to strings
                converted_metadata[key] = str(value)
        
        return converted_metadata
    
    def _dict_to_text(self, data: Dict[str, Any]) -> str:
        """Converts a dictionary to text."""
        text_parts = []
        
        for key, value in data.items():
            if isinstance(value, list):
                text_parts.append(f"{key}: {', '.join(map(str, value))}")
            elif isinstance(value, dict):
                text_parts.append(f"{key}: {str(value)}")
            else:
                text_parts.append(f"{key}: {value}")
        
        return " | ".join(text_parts) 