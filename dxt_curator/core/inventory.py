"""
Simple AI-friendly inventory system for DXT repositories.

This module provides a natural language approach to repository tracking that leverages
AI's ability to understand and process unstructured text rather than fighting it with
rigid schemas.

Key Design Principles:
1. Natural Language First: Instead of enums and structured data, use human-readable text
2. AI-Friendly: All data is stored in formats that AI can easily understand and process
3. Flexible Schema: Free-form text fields allow for any type of information
4. Complete Audit Trail: Every decision and change is recorded with reasoning

Why This Works:
- AI excels at processing natural language, not rigid structures
- Human-readable format makes debugging and maintenance easier
- Flexible schema adapts to new use cases without code changes
- AI can search, analyze, and make decisions based on natural language context
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RepoEntry:
    """
    Repository entry with natural language fields.
    
    This dataclass represents a single repository in our inventory. Unlike traditional
    database schemas with rigid types, we use natural language fields that AI can
    understand and process.
    
    Design Philosophy:
    - Use descriptive field names that explain their purpose
    - Store reasoning and decisions in human-readable format
    - Allow for flexible evolution of data without schema changes
    """
    full_name: str              # GitHub repo name (owner/repo)
    clone_url: str              # URL for cloning the repository
    description: str            # Repository description from GitHub
    stars: int                  # Star count (useful for popularity ranking)
    language: str               # Primary programming language
    discovered_date: str        # When we first found this repository
    status: str                 # Current status: "discovered", "evaluating", "mirrored", "rejected", "check_later"
    notes: str = ""             # Human-readable notes about the repository
    evaluation_notes: str = ""  # AI evaluation results and reasoning
    decision_reason: str = ""   # Why we made the current decision
    future_actions: str = ""    # What should be done next (in natural language)
    last_updated: str = ""      # When this entry was last modified
    metadata: Dict[str, Any] = None  # JSON blob for any additional structured data


class SimpleInventory:
    """
    AI-friendly repository inventory system.
    
    This class manages a SQLite database that stores repository information in a way
    that's optimized for AI processing. Instead of complex relational schemas, we use
    a simple table with natural language fields.
    
    Why SQLite:
    - Serverless, single-file database
    - Excellent for read-heavy workloads
    - Built-in full-text search capabilities
    - Easy backup and portability
    
    Why Natural Language Fields:
    - AI can understand context and nuance
    - Human-readable for debugging and maintenance
    - Flexible schema that evolves with use
    - Easy to search and analyze
    """
    
    def __init__(self, db_path: str = "dxt_inventory.db"):
        """
        Initialize the inventory system.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """
        Initialize the SQLite database with our simple schema.
        
        We use a single table approach because:
        1. Simplicity: Easy to understand and maintain
        2. Flexibility: Natural language fields can contain any information
        3. AI-Friendly: No complex joins or relationships to confuse AI
        4. Performance: Simple queries are fast
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create the main repositories table
        # Note: We use TEXT for most fields to allow natural language content
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS repos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT UNIQUE NOT NULL,       -- GitHub repo identifier
                clone_url TEXT NOT NULL,              -- URL for cloning
                description TEXT,                     -- Repository description
                stars INTEGER,                        -- Star count for popularity
                language TEXT,                        -- Primary programming language
                discovered_date TEXT NOT NULL,        -- When we found this repo
                status TEXT NOT NULL,                 -- Current processing status
                notes TEXT,                           -- Human-readable notes
                evaluation_notes TEXT,                -- AI evaluation results
                decision_reason TEXT,                 -- Why we made this decision
                future_actions TEXT,                  -- What to do next
                last_updated TEXT,                    -- Last modification time
                metadata TEXT                         -- JSON blob for extra data
            )
        ''')
        
        # Create indexes for common queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON repos(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_full_name ON repos(full_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_discovered_date ON repos(discovered_date)')
        
        conn.commit()
        conn.close()
    
    def add_repo(self, repo_data: Dict[str, Any], notes: str = "") -> bool:
        """
        Add a new repository to the inventory.
        
        This method takes repository data from GitHub API and stores it in our
        natural language format. We preserve the original structured data in
        the metadata field while extracting key information into searchable fields.
        
        Args:
            repo_data: Dictionary containing repository information from GitHub API
            notes: Optional human-readable notes about why this repo was added
            
        Returns:
            bool: True if successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        try:
            # Determine initial status based on fork analysis
            initial_status = 'discovered'
            fork_notes = ""
            
            # Check if this is a fork with minimal changes
            if repo_data.get('is_fork', False):
                fork_analysis = repo_data.get('fork_analysis', '')
                if 'minimal changes' in fork_analysis.lower():
                    initial_status = 'fork_ignored'
                    fork_notes = f"Fork of {repo_data.get('parent_repo', 'unknown')} - {fork_analysis}"
                elif 'significant changes' in fork_analysis.lower():
                    fork_notes = f"Fork of {repo_data.get('parent_repo', 'unknown')} with substantial modifications - {fork_analysis}"
                else:
                    fork_notes = f"Fork of {repo_data.get('parent_repo', 'unknown')} - {fork_analysis}"
            
            # Combine notes
            combined_notes = f"{notes}. {fork_notes}" if fork_notes else notes
            
            cursor.execute('''
                INSERT OR REPLACE INTO repos (
                    full_name, clone_url, description, stars, language,
                    discovered_date, status, notes, evaluation_notes,
                    decision_reason, future_actions, last_updated, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                repo_data['full_name'],
                repo_data['clone_url'],
                repo_data.get('description', ''),
                repo_data.get('stars', 0),
                repo_data.get('language', ''),
                now,
                initial_status,
                combined_notes,
                '',  # No evaluation yet
                '',  # No decision yet
                '',  # No future actions yet
                now,
                json.dumps(repo_data)  # Preserve original data
            ))
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            print(f"Database error adding repo {repo_data.get('full_name', 'unknown')}: {e}")
            return False
        finally:
            conn.close()
    
    def update_repo(self, full_name: str, status: str = None, notes: str = None,
                   evaluation_notes: str = None, decision_reason: str = None,
                   future_actions: str = None) -> bool:
        """
        Update repository information with AI-generated content.
        
        This method allows updating any of the natural language fields. It's designed
        to be called by AI evaluation systems that want to record their decisions
        and reasoning in human-readable format.
        
        Args:
            full_name: Repository identifier (owner/repo)
            status: New status if changing
            notes: Additional notes to record
            evaluation_notes: AI evaluation results
            decision_reason: Why this decision was made
            future_actions: What should be done next
            
        Returns:
            bool: True if update successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build dynamic update query
        # This allows us to update only the fields that are provided
        updates = []
        params = []
        
        if status:
            updates.append("status = ?")
            params.append(status)
        if notes:
            updates.append("notes = ?")
            params.append(notes)
        if evaluation_notes:
            updates.append("evaluation_notes = ?")
            params.append(evaluation_notes)
        if decision_reason:
            updates.append("decision_reason = ?")
            params.append(decision_reason)
        if future_actions:
            updates.append("future_actions = ?")
            params.append(future_actions)
        
        # Always update the last_updated timestamp
        updates.append("last_updated = ?")
        params.append(datetime.now().isoformat())
        params.append(full_name)
        
        if not updates:
            return False  # Nothing to update
        
        query = f"UPDATE repos SET {', '.join(updates)} WHERE full_name = ?"
        
        try:
            cursor.execute(query, params)
            success = cursor.rowcount > 0
            conn.commit()
            return success
        except sqlite3.Error as e:
            print(f"Database error updating repo {full_name}: {e}")
            return False
        finally:
            conn.close()
    
    def get_repo(self, full_name: str) -> Optional[RepoEntry]:
        """
        Retrieve a specific repository entry.
        
        Args:
            full_name: Repository identifier (owner/repo)
            
        Returns:
            RepoEntry object if found, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM repos WHERE full_name = ?', (full_name,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_entry(row)
            return None
            
        except sqlite3.Error as e:
            print(f"Database error retrieving repo {full_name}: {e}")
            return None
        finally:
            conn.close()
    
    def get_repos_by_status(self, status: str) -> List[RepoEntry]:
        """
        Get all repositories with a specific status.
        
        This is useful for finding repositories that need specific actions:
        - "discovered": Newly found repositories awaiting evaluation
        - "mirror": Repositories approved for mirroring
        - "rejected": Repositories determined to be irrelevant
        - "check_later": Repositories that need future review
        
        Args:
            status: Status to filter by
            
        Returns:
            List of RepoEntry objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM repos WHERE status = ?', (status,))
            rows = cursor.fetchall()
            return [self._row_to_entry(row) for row in rows]
            
        except sqlite3.Error as e:
            print(f"Database error getting repos by status {status}: {e}")
            return []
        finally:
            conn.close()
    
    def get_all_repos(self) -> List[RepoEntry]:
        """Get all repositories in the inventory."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM repos ORDER BY discovered_date DESC')
            rows = cursor.fetchall()
            return [self._row_to_entry(row) for row in rows]
            
        except sqlite3.Error as e:
            print(f"Database error getting all repos: {e}")
            return []
        finally:
            conn.close()
    
    def search_repos(self, query: str) -> List[RepoEntry]:
        """
        Search repositories by text content.
        
        This method demonstrates the power of natural language storage:
        we can search across all text fields to find repositories that match
        any aspect of our query. This is much more flexible than searching
        structured data.
        
        Args:
            query: Search terms to look for
            
        Returns:
            List of matching RepoEntry objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Search across all text fields
            # This is possible because we store everything in natural language
            cursor.execute('''
                SELECT * FROM repos 
                WHERE full_name LIKE ? OR description LIKE ? OR notes LIKE ? 
                   OR evaluation_notes LIKE ? OR decision_reason LIKE ? OR future_actions LIKE ?
                ORDER BY stars DESC
            ''', (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
            
            rows = cursor.fetchall()
            return [self._row_to_entry(row) for row in rows]
            
        except sqlite3.Error as e:
            print(f"Database error searching repos: {e}")
            return []
        finally:
            conn.close()
    
    def export_for_ai(self, status: str = None) -> List[Dict[str, Any]]:
        """
        Export repository data in AI-friendly format.
        
        This method exports our inventory in a format that's optimized for AI
        processing. All the natural language fields are preserved, allowing AI
        to understand context and make intelligent decisions.
        
        Args:
            status: Optional status filter
            
        Returns:
            List of dictionaries suitable for AI processing
        """
        if status:
            repos = self.get_repos_by_status(status)
        else:
            repos = self.get_all_repos()
        
        # Convert to AI-friendly format
        # We include all the natural language fields that AI can understand
        ai_data = []
        for repo in repos:
            ai_data.append({
                'repo_name': repo.full_name,
                'description': repo.description,
                'stars': repo.stars,
                'language': repo.language,
                'status': repo.status,
                'notes': repo.notes,
                'evaluation_notes': repo.evaluation_notes,
                'decision_reason': repo.decision_reason,
                'future_actions': repo.future_actions,
                'clone_url': repo.clone_url,
                'last_updated': repo.last_updated,
                'discovered_date': repo.discovered_date,
                'is_fork': self._get_metadata_field(repo.metadata, 'is_fork', False),
                'parent_repo': self._get_metadata_field(repo.metadata, 'parent_repo', None),
                'fork_analysis': self._get_metadata_field(repo.metadata, 'fork_analysis', '')
            })
        
        return ai_data
    
    def _get_metadata_field(self, metadata: str, field: str, default: Any) -> Any:
        """
        Safely extract a field from JSON metadata.
        
        Args:
            metadata: JSON string containing metadata
            field: Field name to extract
            default: Default value if field not found
            
        Returns:
            Field value or default
        """
        if not metadata:
            return default
        
        try:
            data = json.loads(metadata)
            return data.get(field, default)
        except (json.JSONDecodeError, TypeError):
            return default
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current inventory state.
        
        Returns:
            Dictionary with summary statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get status counts
            cursor.execute('SELECT status, COUNT(*) FROM repos GROUP BY status')
            status_counts = dict(cursor.fetchall())
            
            # Get total count
            cursor.execute('SELECT COUNT(*) FROM repos')
            total = cursor.fetchone()[0]
            
            return {
                'total_repos': total,
                'by_status': status_counts,
                'last_updated': datetime.now().isoformat()
            }
            
        except sqlite3.Error as e:
            print(f"Database error getting summary: {e}")
            return {'total_repos': 0, 'by_status': {}, 'last_updated': datetime.now().isoformat()}
        finally:
            conn.close()
    
    def _row_to_entry(self, row) -> RepoEntry:
        """
        Convert a database row to a RepoEntry object.
        
        This method handles the conversion from SQLite row format to our
        Python dataclass, including proper handling of optional fields.
        """
        return RepoEntry(
            full_name=row[1],
            clone_url=row[2],
            description=row[3] or '',
            stars=row[4] or 0,
            language=row[5] or '',
            discovered_date=row[6],
            status=row[7],
            notes=row[8] or '',
            evaluation_notes=row[9] or '',
            decision_reason=row[10] or '',
            future_actions=row[11] or '',
            last_updated=row[12] or '',
            metadata=json.loads(row[13]) if row[13] else {}
        )


def main():
    """
    CLI interface for inventory management.
    
    This provides basic command-line access to inventory functionality,
    useful for debugging and manual operations.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='DXT Curator Inventory Management')
    parser.add_argument('--summary', action='store_true', help='Show inventory summary')
    parser.add_argument('--export', help='Export to JSON file')
    parser.add_argument('--status', help='Filter by status')
    parser.add_argument('--search', help='Search repositories')
    parser.add_argument('--db', default='dxt_inventory.db', help='Database path')
    
    args = parser.parse_args()
    
    inventory = SimpleInventory(args.db)
    
    if args.summary:
        summary = inventory.get_summary()
        print(f"Total repositories: {summary['total_repos']}")
        print("By status:")
        for status, count in summary['by_status'].items():
            print(f"  {status}: {count}")
    
    elif args.export:
        data = inventory.export_for_ai(args.status)
        with open(args.export, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Exported {len(data)} repositories to {args.export}")
    
    elif args.search:
        repos = inventory.search_repos(args.search)
        print(f"Found {len(repos)} repositories matching '{args.search}':")
        for repo in repos:
            print(f"\n{repo.full_name} ({repo.status}) - {repo.stars} stars")
            if repo.description:
                print(f"  Description: {repo.description}")
            if repo.notes:
                print(f"  Notes: {repo.notes}")
            if repo.evaluation_notes:
                print(f"  AI Evaluation: {repo.evaluation_notes}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()