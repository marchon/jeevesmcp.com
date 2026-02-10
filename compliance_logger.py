#!/usr/bin/env python3
"""
Government Compliance Logging Module for Jeeves

Captures EVERY command, request, processing step, and response
for audit trail and compliance requirements.

Features:
- Immutable audit logs with hash chaining
- User/session tracking
- Complete request/response capture
- Processing step logging
- Tamper detection
- Export capabilities for audits
"""

import json
import hashlib
import os
import socket
import getpass
import uuid
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import threading


class ComplianceLevel(Enum):
    """Compliance logging levels"""
    MINIMAL = "minimal"      # Basic request/response only
    STANDARD = "standard"    # Request/response + routing decisions
    FULL = "full"           # Everything including internal processing
    GOVERNMENT = "government"  # Maximum audit trail with chain of custody


@dataclass
class AuditEntry:
    """Single audit log entry with chain of custody"""
    timestamp: str
    sequence_id: int
    session_id: str
    user: str
    hostname: str
    pid: int
    command: str
    raw_request: str
    processing_steps: List[Dict[str, Any]]
    routing_decision: str
    destination: str
    response: str
    execution_time_ms: float
    metadata: Dict[str, Any]
    previous_hash: str
    entry_hash: str


class ComplianceLogger:
    """
    Government-grade compliance logging system.
    
    Captures complete audit trail with:
    - Immutable hash chaining (tamper detection)
    - Complete request/response lifecycle
    - User and session tracking
    - Processing step details
    - Export for external audit systems
    """
    
    def __init__(self, compliance_level: ComplianceLevel = ComplianceLevel.GOVERNMENT):
        self.compliance_level = compliance_level
        self.log_dir = Path.home() / ".local/share/jeeves/compliance"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Session tracking
        self.session_id = str(uuid.uuid4())
        self.sequence_counter = 0
        self.user = getpass.getuser()
        self.hostname = socket.gethostname()
        self.pid = os.getpid()
        
        # Chain of custody (hash chaining for tamper detection)
        self.previous_hash = "0" * 64  # Genesis hash
        self.chain_file = self.log_dir / f"audit-chain-{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Initialize chain
        self._init_chain()
        
    def _init_chain(self):
        """Initialize or load existing audit chain"""
        if self.chain_file.exists():
            # Load last hash for continuity
            try:
                with open(self.chain_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        last_entry = json.loads(lines[-1])
                        self.previous_hash = last_entry.get('entry_hash', self.previous_hash)
                        self.sequence_counter = last_entry.get('sequence_id', 0) + 1
            except:
                pass
    
    def _calculate_hash(self, entry_data: Dict[str, Any]) -> str:
        """Calculate SHA-256 hash of entry data"""
        # Remove hash fields before calculating
        data_to_hash = {k: v for k, v in entry_data.items() 
                       if k not in ('entry_hash', 'previous_hash')}
        json_str = json.dumps(data_to_hash, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def log_command(
        self,
        raw_command: str,
        processed_request: str,
        processing_steps: List[Dict[str, Any]],
        routing_decision: str,
        destination: str,
        response: str,
        execution_time_ms: float,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log a complete command lifecycle for compliance.
        
        Returns the entry hash for verification.
        """
        with self._lock:
            self.sequence_counter += 1
            
            # Build entry data
            entry_data = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'sequence_id': self.sequence_counter,
                'session_id': self.session_id,
                'user': self.user,
                'hostname': self.hostname,
                'pid': self.pid,
                'command': raw_command,
                'raw_request': processed_request,
                'processing_steps': processing_steps if self.compliance_level in 
                    (ComplianceLevel.FULL, ComplianceLevel.GOVERNMENT) else [],
                'routing_decision': routing_decision,
                'destination': destination,
                'response': response[:10000] if len(response) > 10000 else response,  # Limit size
                'execution_time_ms': execution_time_ms,
                'metadata': additional_metadata or {},
                'previous_hash': self.previous_hash
            }
            
            # Calculate hash for this entry
            entry_hash = self._calculate_hash(entry_data)
            entry_data['entry_hash'] = entry_hash
            
            # Write to audit chain
            with open(self.chain_file, 'a') as f:
                f.write(json.dumps(entry_data, default=str) + '\n')
            
            # Update previous hash for next entry
            self.previous_hash = entry_hash
            
            # Also write to detailed log if FULL or GOVERNMENT
            if self.compliance_level in (ComplianceLevel.FULL, ComplianceLevel.GOVERNMENT):
                self._write_detailed_log(entry_data)
            
            return entry_hash
    
    def _write_detailed_log(self, entry_data: Dict[str, Any]):
        """Write detailed log for government compliance"""
        detailed_file = self.log_dir / f"detailed-{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        # Expand processing steps with full details
        detailed_entry = {
            **entry_data,
            'environment': {
                'pwd': os.getcwd(),
                'path': os.environ.get('PATH', ''),
                'home': os.environ.get('HOME', ''),
                'shell': os.environ.get('SHELL', ''),
            } if self.compliance_level == ComplianceLevel.GOVERNMENT else {},
            'system_info': {
                'platform': os.uname().sysname if hasattr(os, 'uname') else 'unknown',
                'release': os.uname().release if hasattr(os, 'uname') else 'unknown',
                'version': os.uname().version if hasattr(os, 'uname') else 'unknown',
            } if self.compliance_level == ComplianceLevel.GOVERNMENT else {}
        }
        
        with open(detailed_file, 'a') as f:
            f.write(json.dumps(detailed_entry, default=str) + '\n')
    
    def log_processing_step(self, step_name: str, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Log an individual processing step.
        Returns step data with timestamp.
        """
        if self.compliance_level not in (ComplianceLevel.FULL, ComplianceLevel.GOVERNMENT):
            return step_data
        
        step_record = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'step': step_name,
            'data': step_data
        }
        return step_record
    
    def verify_chain_integrity(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify the integrity of the audit chain.
        Returns verification report.
        """
        if date_str is None:
            date_str = datetime.now().strftime('%Y%m%d')
        
        chain_file = self.log_dir / f"audit-chain-{date_str}.jsonl"
        
        if not chain_file.exists():
            return {'valid': False, 'error': 'No chain file found'}
        
        violations = []
        previous_hash = "0" * 64
        entry_count = 0
        
        with open(chain_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    entry = json.loads(line)
                    entry_count += 1
                    
                    # Check previous hash linkage
                    if entry.get('previous_hash') != previous_hash:
                        violations.append({
                            'line': line_num,
                            'type': 'hash_chain_break',
                            'expected': previous_hash,
                            'found': entry.get('previous_hash')
                        })
                    
                    # Verify entry hash
                    stored_hash = entry.pop('entry_hash', None)
                    calculated_hash = self._calculate_hash(entry)
                    entry['entry_hash'] = stored_hash  # Restore
                    
                    if stored_hash != calculated_hash:
                        violations.append({
                            'line': line_num,
                            'type': 'tampered_entry',
                            'expected': calculated_hash,
                            'found': stored_hash
                        })
                    
                    previous_hash = stored_hash
                    
                except json.JSONDecodeError:
                    violations.append({'line': line_num, 'type': 'invalid_json'})
                except Exception as e:
                    violations.append({'line': line_num, 'type': 'error', 'message': str(e)})
        
        return {
            'valid': len(violations) == 0,
            'entries_checked': entry_count,
            'violations': violations,
            'date': date_str
        }
    
    def export_audit_log(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        format: str = 'json',
        output_file: Optional[str] = None
    ) -> str:
        """
        Export audit log for external review.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            format: 'json' or 'csv'
            output_file: Output file path
            
        Returns:
            Path to exported file
        """
        if output_file is None:
            output_file = self.log_dir / f"export-{datetime.now().strftime('%Y%m%d-%H%M%S')}.{format}"
        
        # Collect all entries in date range
        entries = []
        for chain_file in sorted(self.log_dir.glob("audit-chain-*.jsonl")):
            # Parse date from filename
            try:
                file_date = chain_file.stem.split('-')[-1]
                
                # Check date range
                if start_date and file_date < start_date.replace('-', ''):
                    continue
                if end_date and file_date > end_date.replace('-', ''):
                    continue
                
                with open(chain_file, 'r') as f:
                    for line in f:
                        entries.append(json.loads(line))
            except:
                continue
        
        # Export
        if format == 'json':
            with open(output_file, 'w') as f:
                json.dump({
                    'export_timestamp': datetime.utcnow().isoformat() + 'Z',
                    'exported_by': self.user,
                    'entry_count': len(entries),
                    'entries': entries
                }, f, indent=2, default=str)
        
        elif format == 'csv':
            import csv
            with open(output_file, 'w', newline='') as f:
                if entries:
                    writer = csv.DictWriter(f, fieldnames=entries[0].keys())
                    writer.writeheader()
                    writer.writerows(entries)
        
        return str(output_file)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get compliance logging statistics"""
        total_entries = 0
        total_size = 0
        date_range = {'earliest': None, 'latest': None}
        
        for chain_file in self.log_dir.glob("audit-chain-*.jsonl"):
            total_size += chain_file.stat().st_size
            
            with open(chain_file, 'r') as f:
                for line in f:
                    total_entries += 1
                    try:
                        entry = json.loads(line)
                        ts = entry.get('timestamp', '')
                        if date_range['earliest'] is None or ts < date_range['earliest']:
                            date_range['earliest'] = ts
                        if date_range['latest'] is None or ts > date_range['latest']:
                            date_range['latest'] = ts
                    except:
                        pass
        
        return {
            'total_entries': total_entries,
            'total_size_bytes': total_size,
            'date_range': date_range,
            'session_id': self.session_id,
            'compliance_level': self.compliance_level.value
        }


# Global compliance logger instance
_compliance_logger: Optional[ComplianceLogger] = None


def get_compliance_logger(
    level: ComplianceLevel = ComplianceLevel.GOVERNMENT
) -> ComplianceLogger:
    """Get or create global compliance logger"""
    global _compliance_logger
    if _compliance_logger is None:
        _compliance_logger = ComplianceLogger(level)
    return _compliance_logger


def enable_government_compliance():
    """Enable maximum compliance logging"""
    global _compliance_logger
    _compliance_logger = ComplianceLogger(ComplianceLevel.GOVERNMENT)
    return _compliance_logger


# Shell integration wrapper
class ShellComplianceWrapper:
    """
    Wrapper for shell commands to ensure ALL commands are logged.
    
    Usage:
        eval "$(jeeves compliance --enable-shell-wrapper)"
    """
    
    @staticmethod
    def generate_wrapper() -> str:
        """Generate bash wrapper that logs all commands"""
        return '''
# Jeeves Government Compliance Shell Wrapper
# This ensures ALL commands are logged for audit trail

_jeeves_original_prompt="$PS1"

# Pre-command hook
jeeves_preexec() {
    local cmd="$1"
    # Log via jeeves (suppress output)
    python3 -c "
import sys
sys.path.insert(0, '\''/mnt/sdd1/MCP-Server-Clone/FROM-GIT/jeeves-repo'\''')
from compliance_logger import get_compliance_logger
logger = get_compliance_logger()
logger.log_command(
    raw_command='$cmd',
    processed_request='$cmd',
    processing_steps=[{'step': 'shell_wrapper', 'timestamp': '$(date -Iseconds)'}],
    routing_decision='SHELL_PASSTHROUGH',
    destination='shell',
    response='',
    execution_time_ms=0.0
)
" 2>/dev/null &
}

# Trap DEBUG to capture every command
trap '\''jeeves_preexec "$BASH_COMMAND"'\'' DEBUG

echo "✅ Government compliance logging enabled for this shell"
echo "   All commands will be logged to: ~/.local/share/jeeves/compliance/"
'''


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Jeeves Compliance Logger")
    parser.add_argument('--enable', action='store_true', help='Enable compliance logging')
    parser.add_argument('--verify', help='Verify chain integrity for date (YYYYMMDD)')
    parser.add_argument('--export', help='Export audit log to file')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--shell-wrapper', action='store_true', help='Output shell wrapper')
    
    args = parser.parse_args()
    
    if args.shell_wrapper:
        print(ShellComplianceWrapper.generate_wrapper())
    elif args.verify:
        logger = get_compliance_logger()
        result = logger.verify_chain_integrity(args.verify)
        print(json.dumps(result, indent=2))
    elif args.export:
        logger = get_compliance_logger()
        output = logger.export_audit_log(output_file=args.export)
        print(f"Exported to: {output}")
    elif args.stats:
        logger = get_compliance_logger()
        print(json.dumps(logger.get_statistics(), indent=2))
    else:
        parser.print_help()
