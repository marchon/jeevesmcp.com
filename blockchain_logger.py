#!/usr/bin/env python3
"""
Blockchain Audit Logger for Jeeves

Implements a local blockchain that tracks all prompts with:
- SHA256 hashing of block contents
- Linked block structure (each block contains previous hash)
- Periodic external API publishing
- API receipt storage in blockchain
- Hash-based filename format: SHA256-{hash}-{timestamp}.json

Usage:
    from blockchain_logger import BlockchainLogger, get_blockchain_logger
    logger = get_blockchain_logger()
    logger.add_block(command_data)
"""

import json
import hashlib
import os
import time
import threading
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid


@dataclass
class Block:
    """A single block in the blockchain"""
    index: int                          # Block sequence number
    timestamp: str                      # ISO format timestamp
    previous_hash: str                  # Hash of previous block
    data: Dict[str, Any]                # Command/prompt data
    nonce: int                          # For proof of work (optional)
    hash: str                           # This block's hash
    api_receipt: Optional[Dict] = None  # External API receipt if published
    api_publish_time: Optional[str] = None  # When published to API


class BlockchainLogger:
    """
    Blockchain-based audit logger for government compliance.
    
    Features:
    - Immutable blockchain structure with SHA256 hashing
    - Each block linked to previous via hash
    - Automatic periodic publishing to external API
    - API receipts stored in blockchain
    - Hash-based filenames for content verification
    """
    
    def __init__(
        self,
        chain_dir: Optional[Path] = None,
        api_endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        publish_interval_seconds: int = 300,  # 5 minutes default
        auto_publish: bool = True
    ):
        """
        Initialize blockchain logger.
        
        Args:
            chain_dir: Directory to store blockchain files
            api_endpoint: External API URL for publishing
            api_key: API authentication key
            publish_interval_seconds: How often to publish to API
            auto_publish: Whether to auto-publish periodically
        """
        self.chain_dir = chain_dir or Path.home() / ".local/share/jeeves/blockchain"
        self.chain_dir.mkdir(parents=True, exist_ok=True)
        
        self.api_endpoint = api_endpoint or os.environ.get('JEEVES_BLOCKCHAIN_API')
        self.api_key = api_key or os.environ.get('JEEVES_BLOCKCHAIN_API_KEY')
        self.publish_interval = publish_interval_seconds
        self.auto_publish = auto_publish and self.api_endpoint
        
        # Chain state
        self.chain: List[Block] = []
        self.pending_blocks: List[Block] = []
        self.chain_id = str(uuid.uuid4())[:8]
        
        # Thread safety
        self._lock = threading.Lock()
        self._publish_timer = None
        
        # Load existing chain or create genesis
        self._load_or_create_chain()
        
        # Start auto-publisher if enabled
        if self.auto_publish:
            self._start_auto_publisher()
    
    def _calculate_hash(self, block_data: Dict[str, Any]) -> str:
        """Calculate SHA256 hash of block data"""
        # Create consistent string representation
        block_string = json.dumps(block_data, sort_keys=True, default=str)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def _create_genesis_block(self) -> Block:
        """Create the first block in the chain"""
        genesis_data = {
            "message": "Jeeves Blockchain Genesis",
            "chain_id": self.chain_id,
            "version": "1.0"
        }
        
        block_data = {
            "index": 0,
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "previous_hash": "0" * 64,
            "data": genesis_data,
            "nonce": 0
        }
        
        block_hash = self._calculate_hash(block_data)
        
        return Block(
            index=0,
            timestamp=block_data["timestamp"],
            previous_hash="0" * 64,
            data=genesis_data,
            nonce=0,
            hash=block_hash
        )
    
    def _load_or_create_chain(self):
        """Load existing blockchain or create new one"""
        # Look for existing chain files
        chain_files = list(self.chain_dir.glob("SHA256-*.json"))
        
        if chain_files:
            # Load existing chain
            print(f"🔗 Loading existing blockchain from {len(chain_files)} files...")
            loaded_blocks = []
            for chain_file in chain_files:
                try:
                    with open(chain_file, 'r') as f:
                        block_data = json.load(f)
                        block = Block(**block_data)
                        loaded_blocks.append(block)
                except Exception as e:
                    print(f"⚠️  Error loading {chain_file}: {e}")
            
            # Sort by index
            loaded_blocks.sort(key=lambda b: b.index)
            self.chain = loaded_blocks
            
            if self.chain:
                print(f"   Loaded {len(self.chain)} blocks")
                self.chain_id = self.chain[0].data.get('chain_id', self.chain_id)
        else:
            # Create genesis block
            print(f"🔗 Creating new blockchain (ID: {self.chain_id})...")
            genesis = self._create_genesis_block()
            self.chain.append(genesis)
            self._save_block(genesis)
    
    def _save_block(self, block: Block):
        """Save block to file with hash-based filename"""
        # Format: SHA256-{hash}-{timestamp}.json
        timestamp_str = block.timestamp.replace(':', '-').replace('.', '_')
        filename = f"SHA256-{block.hash[:16]}-{timestamp_str}.json"
        filepath = self.chain_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(asdict(block), f, indent=2, default=str)
        
        return filepath
    
    def add_block(self, data: Dict[str, Any]) -> Block:
        """
        Add a new block to the chain.
        
        Args:
            data: Command/prompt data to store
            
        Returns:
            The created Block
        """
        with self._lock:
            # Get previous block
            previous_block = self.chain[-1] if self.chain else None
            previous_hash = previous_block.hash if previous_block else "0" * 64
            index = len(self.chain)
            
            # Create block data (without hash first)
            timestamp = datetime.utcnow().isoformat() + 'Z'
            block_data = {
                "index": index,
                "timestamp": timestamp,
                "previous_hash": previous_hash,
                "data": data,
                "nonce": 0  # Could implement proof-of-work here
            }
            
            # Calculate hash
            block_hash = self._calculate_hash(block_data)
            
            # Create block
            block = Block(
                index=index,
                timestamp=timestamp,
                previous_hash=previous_hash,
                data=data,
                nonce=0,
                hash=block_hash
            )
            
            # Add to chain
            self.chain.append(block)
            self.pending_blocks.append(block)
            
            # Save to file
            filepath = self._save_block(block)
            
            return block
    
    def verify_chain(self) -> Dict[str, Any]:
        """
        Verify blockchain integrity.
        
        Returns:
            Verification report
        """
        with self._lock:
            errors = []
            
            for i in range(1, len(self.chain)):
                current = self.chain[i]
                previous = self.chain[i-1]
                
                # Check index continuity
                if current.index != i:
                    errors.append(f"Block {i}: Invalid index {current.index}")
                
                # Check previous hash linkage
                if current.previous_hash != previous.hash:
                    errors.append(f"Block {i}: Hash chain broken")
                
                # Verify current block hash
                block_data = {
                    "index": current.index,
                    "timestamp": current.timestamp,
                    "previous_hash": current.previous_hash,
                    "data": current.data,
                    "nonce": current.nonce
                }
                calculated_hash = self._calculate_hash(block_data)
                if calculated_hash != current.hash:
                    errors.append(f"Block {i}: Hash mismatch (tampering detected)")
            
            return {
                "valid": len(errors) == 0,
                "blocks_checked": len(self.chain),
                "errors": errors,
                "chain_id": self.chain_id
            }
    
    def publish_to_api(self, force: bool = False) -> Optional[Dict]:
        """
        Publish pending blocks to external API.
        
        Args:
            force: Publish even if no pending blocks
            
        Returns:
            API receipt if successful
        """
        if not self.api_endpoint:
            print("⚠️  No API endpoint configured")
            return None
        
        with self._lock:
            if not self.pending_blocks and not force:
                return None
            
            # Prepare data to publish
            publish_data = {
                "chain_id": self.chain_id,
                "timestamp": datetime.utcnow().isoformat() + 'Z',
                "block_count": len(self.chain),
                "pending_blocks": len(self.pending_blocks),
                "latest_hash": self.chain[-1].hash if self.chain else None,
                "blocks": [asdict(b) for b in (self.pending_blocks if self.pending_blocks else [self.chain[-1]])]
            }
            
            try:
                # Call external API
                headers = {"Content-Type": "application/json"}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                
                response = requests.post(
                    self.api_endpoint,
                    json=publish_data,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    # Create API receipt
                    receipt = {
                        "api_endpoint": self.api_endpoint,
                        "published_at": datetime.utcnow().isoformat() + 'Z',
                        "http_status": response.status_code,
                        "response_hash": hashlib.sha256(response.text.encode()).hexdigest()[:16],
                        "blocks_published": len(self.pending_blocks) if self.pending_blocks else 1,
                        "api_response": response.json() if response.text else None
                    }
                    
                    # Add receipt block
                    receipt_block = self.add_block({
                        "type": "API_PUBLISH_RECEIPT",
                        "receipt": receipt,
                        "published_blocks": [b.index for b in (self.pending_blocks or [self.chain[-2]])]
                    })
                    
                    # Clear pending
                    self.pending_blocks = []
                    
                    print(f"✅ Published to API: {receipt['response_hash']}")
                    return receipt
                else:
                    print(f"❌ API publish failed: HTTP {response.status_code}")
                    return None
                    
            except Exception as e:
                print(f"❌ API publish error: {e}")
                return None
    
    def _start_auto_publisher(self):
        """Start background thread for periodic publishing"""
        def publish_loop():
            while self.auto_publish:
                time.sleep(self.publish_interval)
                if self.pending_blocks:
                    self.publish_to_api()
        
        self._publish_timer = threading.Thread(target=publish_loop, daemon=True)
        self._publish_timer.start()
        print(f"🔄 Auto-publisher started ({self.publish_interval}s interval)")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get blockchain statistics"""
        with self._lock:
            total_size = sum(
                (self.chain_dir / f"SHA256-{b.hash[:16]}-{b.timestamp.replace(':', '-').replace('.', '_')}.json").stat().st_size
                for b in self.chain
                if (self.chain_dir / f"SHA256-{b.hash[:16]}-{b.timestamp.replace(':', '-').replace('.', '_')}.json").exists()
            )
            
            return {
                "chain_id": self.chain_id,
                "total_blocks": len(self.chain),
                "pending_blocks": len(self.pending_blocks),
                "genesis_timestamp": self.chain[0].timestamp if self.chain else None,
                "latest_timestamp": self.chain[-1].timestamp if self.chain else None,
                "latest_hash": self.chain[-1].hash if self.chain else None,
                "total_size_bytes": total_size,
                "api_endpoint": self.api_endpoint,
                "auto_publish": self.auto_publish,
                "publish_interval_seconds": self.publish_interval
            }
    
    def export_chain(self, output_file: Optional[str] = None) -> str:
        """Export entire chain to file"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            output_file = self.chain_dir / f"chain-export-{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump({
                "chain_id": self.chain_id,
                "export_timestamp": datetime.utcnow().isoformat() + 'Z',
                "block_count": len(self.chain),
                "blocks": [asdict(b) for b in self.chain]
            }, f, indent=2, default=str)
        
        return str(output_file)
    
    def find_block_by_hash(self, hash_prefix: str) -> Optional[Block]:
        """Find block by hash prefix"""
        for block in self.chain:
            if block.hash.startswith(hash_prefix):
                return block
        return None
    
    def get_chain_files(self) -> List[Path]:
        """Get list of all blockchain files sorted by block index"""
        files = list(self.chain_dir.glob("SHA256-*.json"))
        # Sort by reading the index from each file
        def get_index(f):
            try:
                with open(f, 'r') as fp:
                    data = json.load(fp)
                    return data.get('index', 0)
            except:
                return 0
        return sorted(files, key=get_index)


# Global instance
_blockchain_logger: Optional[BlockchainLogger] = None


def get_blockchain_logger(
    api_endpoint: Optional[str] = None,
    api_key: Optional[str] = None,
    auto_publish: bool = True
) -> BlockchainLogger:
    """Get or create global blockchain logger"""
    global _blockchain_logger
    if _blockchain_logger is None:
        _blockchain_logger = BlockchainLogger(
            api_endpoint=api_endpoint,
            api_key=api_key,
            auto_publish=auto_publish
        )
    return _blockchain_logger


# Shell integration for automatic logging
def enable_blockchain_logging():
    """Enable blockchain logging for all commands"""
    logger = get_blockchain_logger()
    print(f"🔗 Blockchain logging enabled")
    print(f"   Chain ID: {logger.chain_id}")
    print(f"   Directory: {logger.chain_dir}")
    if logger.api_endpoint:
        print(f"   API Endpoint: {logger.api_endpoint}")
        print(f"   Auto-publish: {logger.auto_publish}")
    return logger


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Jeeves Blockchain Logger")
    parser.add_argument('--enable', action='store_true', help='Enable blockchain logging')
    parser.add_argument('--status', action='store_true', help='Show blockchain status')
    parser.add_argument('--verify', action='store_true', help='Verify chain integrity')
    parser.add_argument('--export', help='Export chain to file')
    parser.add_argument('--publish', action='store_true', help='Publish to API now')
    parser.add_argument('--api', help='Set API endpoint')
    parser.add_argument('--api-key', help='Set API key')
    
    args = parser.parse_args()
    
    if args.enable:
        if args.api:
            os.environ['JEEVES_BLOCKCHAIN_API'] = args.api
        if args.api_key:
            os.environ['JEEVES_BLOCKCHAIN_API_KEY'] = args.api_key
        enable_blockchain_logging()
    elif args.status:
        logger = BlockchainLogger()
        print(json.dumps(logger.get_statistics(), indent=2))
    elif args.verify:
        logger = BlockchainLogger()
        result = logger.verify_chain()
        print(json.dumps(result, indent=2))
    elif args.export:
        logger = BlockchainLogger()
        output = logger.export_chain(args.export)
        print(f"Exported to: {output}")
    elif args.publish:
        logger = BlockchainLogger()
        receipt = logger.publish_to_api(force=True)
        if receipt:
            print(json.dumps(receipt, indent=2))
    else:
        parser.print_help()
