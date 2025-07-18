"""
AI-powered repository evaluation using natural language processing.

This module represents a paradigm shift from traditional rule-based evaluation to
AI-powered natural language analysis. Instead of trying to encode human judgment
into rigid rules, we leverage AI's ability to understand context, nuance, and
intent in the same way humans do.

Key Design Principles:
1. AI-First Approach: Let AI read and understand repositories like humans do
2. Natural Language Decisions: Store all reasoning in human-readable format
3. Context-Aware Analysis: Consider repository content, not just metadata
4. Flexible Decision Framework: Support nuanced decisions beyond binary choices

Why This Works:
- AI excels at understanding context and intent from natural language
- Repository evaluation is inherently subjective and context-dependent
- Human-readable decisions enable better debugging and learning
- Flexible framework adapts to new evaluation criteria without code changes

The evaluation process mimics human repository evaluation:
1. Read the repository description and README
2. Examine the file structure and code samples
3. Make a judgment about relevance and quality
4. Document the reasoning in natural language
5. Recommend appropriate actions
"""

import os
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests

from .file_inventory import FileInventory
from ..utils.security import get_sanitizer, get_security_logger


class AIEvaluator:
    """
    AI-powered repository evaluation system.
    
    This class uses OpenAI or Anthropic APIs to evaluate repositories in a way
    that mimics human judgment. Instead of rule-based evaluation, it uses AI's
    natural language processing capabilities to understand repository content
    and context.
    
    The evaluation process:
    1. Clone the repository for analysis
    2. Extract key information (README, config files, file structure)
    3. Use AI to analyze the information and make decisions
    4. Store all reasoning in natural language format
    5. Clean up temporary files
    
    This approach is powerful because:
    - AI can understand context and nuance
    - Decisions are explainable and human-readable
    - No need to encode complex rules or edge cases
    - Adapts to new types of repositories automatically
    """
    
    def __init__(self, api_key: str = None, api_provider: str = "openai"):
        """
        Initialize the AI evaluator.
        
        Args:
            api_key: API key for the AI service (optional, can use environment variables)
            api_provider: Either "openai" or "anthropic"
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
        self.api_provider = api_provider.lower()
        self.inventory = FileInventory()
        self.work_dir = Path("./temp_clones")
        self.work_dir.mkdir(exist_ok=True)
        
        # Initialize security components
        self.sanitizer = get_sanitizer()
        self.security_logger = get_security_logger()
        
        if not self.api_key:
            raise ValueError("No API key found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable.")
        
        print(f"🤖 AI Evaluator initialized with {api_provider.upper()} API")
        print("🛡️  Security measures enabled")
    
    def call_ai(self, prompt: str, max_tokens: int = 1000) -> str:
        """
        Call the AI API with a prompt.
        
        This method abstracts the differences between AI providers, allowing
        us to use either OpenAI or Anthropic APIs with the same interface.
        
        Args:
            prompt: The prompt to send to the AI
            max_tokens: Maximum number of tokens in the response
            
        Returns:
            AI response as a string
        """
        if self.api_provider == "openai":
            return self._call_openai(prompt, max_tokens)
        elif self.api_provider == "anthropic":
            return self._call_anthropic(prompt, max_tokens)
        else:
            raise ValueError(f"Unsupported API provider: {self.api_provider}")
    
    def _call_openai(self, prompt: str, max_tokens: int) -> str:
        """
        Call OpenAI API.
        
        Uses the GPT-3.5-turbo model for cost-effective evaluation.
        The temperature is set low (0.1) to ensure consistent, focused responses.
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'gpt-3.5-turbo',
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': max_tokens,
            'temperature': 0.1  # Low temperature for consistent, focused responses
        }
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
    
    def _call_anthropic(self, prompt: str, max_tokens: int) -> str:
        """
        Call Anthropic API.
        
        Uses Claude-3-sonnet for high-quality evaluation.
        """
        headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        
        data = {
            'model': 'claude-3-sonnet-20240229',
            'max_tokens': max_tokens,
            'messages': [{'role': 'user', 'content': prompt}]
        }
        
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            return response.json()['content'][0]['text']
        else:
            raise Exception(f"Anthropic API error: {response.status_code} - {response.text}")
    
    def clone_repo(self, repo_url: str, repo_name: str) -> Optional[str]:
        """
        Clone a repository for analysis.
        
        We use shallow cloning (--depth 1) to minimize bandwidth and storage
        requirements. This gives us access to the current state of the repository
        without the full history, which is sufficient for evaluation purposes.
        
        Args:
            repo_url: URL to clone from
            repo_name: Repository name for directory naming
            
        Returns:
            Path to cloned repository or None if clone failed
        """
        # Create a safe directory name from the repository name
        safe_name = repo_name.replace('/', '_').replace(' ', '_')
        repo_dir = self.work_dir / safe_name
        
        # Remove existing directory if it exists
        if repo_dir.exists():
            shutil.rmtree(repo_dir)
        
        try:
            # Shallow clone with timeout to prevent hanging
            result = subprocess.run([
                'git', 'clone', '--depth', '1', repo_url, str(repo_dir)
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                return str(repo_dir)
            else:
                print(f"Clone failed for {repo_name}: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print(f"Clone timeout for {repo_name}")
            return None
        except Exception as e:
            print(f"Clone error for {repo_name}: {e}")
            return None
    
    def read_key_files(self, repo_dir: str) -> Dict[str, str]:
        """
        Read key files from the repository for AI analysis.
        
        This method extracts the most important information from a repository
        that an AI (or human) would need to understand its purpose and quality.
        
        Key files we examine:
        1. README: Primary documentation and project description
        2. Config files: Dependencies, build configuration, project metadata
        3. File structure: Overall organization and content overview
        
        We limit the amount of content to avoid overwhelming the AI and
        to stay within API token limits.
        
        Args:
            repo_dir: Path to the cloned repository
            
        Returns:
            Dictionary with extracted file contents
        """
        files = {}
        repo_path = Path(repo_dir)
        
        # Read README file
        # README is usually the most important file for understanding a project
        readme_files = ['README.md', 'README.rst', 'README.txt', 'README']
        for readme in readme_files:
            readme_path = repo_path / readme
            if readme_path.exists():
                try:
                    with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
                        # Limit to first 3000 characters to avoid token limits
                        files['readme'] = f.read()[:3000]
                    break
                except Exception as e:
                    print(f"Error reading README: {e}")
                    continue
        
        # Read configuration files
        # These files provide insight into the project's dependencies and setup
        config_files = ['package.json', 'setup.py', 'pyproject.toml', 'Cargo.toml', 'go.mod']
        for config in config_files:
            config_path = repo_path / config
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8', errors='ignore') as f:
                        # Limit to first 1000 characters
                        files['config'] = f.read()[:1000]
                    break
                except Exception as e:
                    print(f"Error reading config file: {e}")
                    continue
        
        # Generate file structure overview
        # This gives the AI a sense of the repository's organization
        file_list = []
        try:
            for file_path in repo_path.rglob('*'):
                if file_path.is_file():
                    rel_path = file_path.relative_to(repo_path)
                    file_list.append(str(rel_path))
                    
                    # Limit to first 50 files to avoid overwhelming the AI
                    if len(file_list) >= 50:
                        break
        except Exception as e:
            print(f"Error listing files: {e}")
        
        files['file_list'] = '\\n'.join(file_list)
        
        return files
    
    def evaluate_repo(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a repository using AI analysis.
        
        This is the core evaluation method that:
        1. Clones the repository
        2. Extracts key information
        3. Uses AI to analyze and make decisions
        4. Returns structured results with natural language reasoning
        
        The AI evaluation mimics human repository evaluation by considering:
        - Project description and documentation quality
        - Code structure and organization
        - Dependencies and technical stack
        - Evidence of DXT relevance
        - Overall project maturity and quality
        
        Args:
            repo_data: Dictionary containing repository metadata
            
        Returns:
            Dictionary with evaluation results and reasoning
        """
        repo_name = repo_data['full_name']
        print(f"🔍 Evaluating: {repo_name}")
        
        # Clone the repository
        repo_dir = self.clone_repo(repo_data['clone_url'], repo_name)
        
        if not repo_dir:
            return {
                'decision': 'reject',
                'reason': 'Could not clone repository',
                'notes': 'Repository clone failed - may be private, deleted, or have connectivity issues',
                'future_actions': 'None - repository not accessible'
            }
        
        try:
            # Extract key information from the repository
            files = self.read_key_files(repo_dir)
            
            # Create secure AI prompt for evaluation
            prompt = self.sanitizer.create_safe_prompt(repo_data, files)
            
            # Log any security warnings
            for file_type, content in files.items():
                sanitized = self.sanitizer.sanitize_content(content)
                if sanitized['is_suspicious']:
                    self.security_logger.log_suspicious_content(
                        repo_name, file_type, sanitized['suspicious_matches']
                    )
            
            # Get AI evaluation
            ai_response = self.call_ai(prompt)
            
            # Validate AI response for potential manipulation using UUID validation
            session_uuid = self.sanitizer.get_current_session_uuid()
            validation = self.sanitizer.validate_ai_response(ai_response, session_uuid)
            if not validation['is_valid']:
                self.security_logger.log_evaluation_anomaly(
                    repo_name, 'invalid_response', str(validation['warnings'])
                )
                # Still proceed but log the anomaly
            
            # Parse AI response into structured format
            decision = self._parse_ai_response(ai_response, validation.get('parsed_response'))
            
            return decision
        
        except Exception as e:
            return {
                'decision': 'reject',
                'reason': f'Evaluation error: {str(e)}',
                'notes': 'Technical error during evaluation process',
                'future_actions': 'Review evaluation system or retry later'
            }
        
        finally:
            # Always clean up cloned repository
            if Path(repo_dir).exists():
                shutil.rmtree(repo_dir)
    
    
    def _parse_ai_response(self, response: str, parsed_response: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Parse AI response into structured format.
        
        This method extracts the structured information from the AI's response.
        It handles both JSON format (with UUID security) and legacy format.
        
        Args:
            response: Raw AI response text
            parsed_response: Pre-parsed JSON response (if available)
            
        Returns:
            Dictionary with parsed evaluation results
        """
        # Use pre-parsed JSON response if available
        if parsed_response:
            return {
                'decision': parsed_response.get('decision', 'reject'),
                'reason': parsed_response.get('reason', 'AI evaluation failed to parse'),
                'notes': parsed_response.get('notes', ''),
                'future_actions': parsed_response.get('future_actions', '')
            }
        
        # Fallback to legacy format parsing
        lines = response.strip().split('\\n')
        
        # Default values
        decision = 'reject'
        reason = 'AI evaluation failed to parse'
        notes = ''
        future_actions = ''
        
        # Parse response line by line
        for line in lines:
            line = line.strip()
            if line.startswith('DECISION:'):
                decision = line.split(':', 1)[1].strip().lower()
            elif line.startswith('REASON:'):
                reason = line.split(':', 1)[1].strip()
            elif line.startswith('NOTES:'):
                notes = line.split(':', 1)[1].strip()
            elif line.startswith('FUTURE_ACTIONS:'):
                future_actions = line.split(':', 1)[1].strip()
        
        # Validate decision
        if decision not in ['mirror', 'reject', 'check_later']:
            decision = 'reject'
            reason = f'Invalid decision format: {decision}. ' + reason
        
        return {
            'decision': decision,
            'reason': reason,
            'notes': notes,
            'future_actions': future_actions
        }
    
    def process_discovered_repos(self, repos_file: str) -> Dict[str, Any]:
        """
        Process a batch of discovered repositories.
        
        This method orchestrates the evaluation of multiple repositories,
        handling inventory updates and result aggregation.
        
        Args:
            repos_file: JSON file containing discovered repositories
            
        Returns:
            Dictionary with evaluation results summary
        """
        with open(repos_file, 'r') as f:
            repos = json.load(f)
        
        print(f"📊 Processing {len(repos)} repositories with AI...")
        
        results = {
            'mirror': [],
            'reject': [],
            'check_later': []
        }
        
        for i, repo_data in enumerate(repos):
            print(f"[{i+1}/{len(repos)}] Processing: {repo_data['full_name']}")
            
            # Check if repository is already in inventory
            repo_url = repo_data['clone_url']
            existing = self.inventory.get_repository(repo_url)
            if existing:
                status = existing.get('curation', {}).get('status', 'unknown')
                print(f"  ⏭️  Already in inventory: {status}")
                continue
            
            # Add to inventory as discovered
            self.inventory.add_repository(repo_data, "Discovered from GitHub search")
            
            # Evaluate with AI
            try:
                evaluation = self.evaluate_repo(repo_data)
                
                # Update inventory with evaluation results
                repo_url = repo_data['clone_url']
                self.inventory.update_repository(
                    repo_url,
                    status=evaluation['decision'],
                    evaluation_notes=evaluation['reason'],
                    notes=evaluation['notes'],
                    future_actions=evaluation['future_actions']
                )
                
                # Track results
                results[evaluation['decision']].append(repo_data['full_name'])
                
                print(f"  {evaluation['decision'].upper()}: {evaluation['reason']}")
                
            except Exception as e:
                print(f"  ❌ Error evaluating: {e}")
                # Record the error in inventory
                repo_url = repo_data['clone_url']
                self.inventory.update_repository(
                    repo_url,
                    status='reject',
                    evaluation_notes=f"Evaluation failed: {str(e)}"
                )
        
        return results
    
    def recheck_repos(self) -> Dict[str, Any]:
        """
        Recheck repositories marked for later review.
        
        This method finds repositories with "check_later" status and
        re-evaluates them to see if they've evolved enough to warrant
        mirroring or should be rejected.
        
        Returns:
            Dictionary with recheck results
        """
        check_later_repos = self.inventory.get_repositories_by_status('check_later')
        
        if not check_later_repos:
            print("No repositories marked for rechecking")
            return {'rechecked': 0, 'results': {}}
        
        print(f"🔄 Rechecking {len(check_later_repos)} repositories...")
        
        results = {
            'mirror': [],
            'reject': [],
            'check_later': []
        }
        
        for repo in check_later_repos:
            metadata = repo.get('metadata', {})
            full_name = metadata.get('full_name', 'Unknown')
            print(f"Rechecking: {full_name}")
            
            # Convert inventory entry back to evaluation format
            repo_data = {
                'full_name': metadata.get('full_name', ''),
                'clone_url': metadata.get('clone_url', repo.get('repository_url', '')),
                'description': metadata.get('description', ''),
                'stars': metadata.get('stars', 0),
                'language': metadata.get('language', ''),
                'forks': metadata.get('forks', 0),
                'size': metadata.get('size', 0),
                'topics': metadata.get('topics', [])
            }
            
            try:
                evaluation = self.evaluate_repo(repo_data)
                
                # Update inventory with new evaluation
                repo_url = repo_data['clone_url']
                self.inventory.update_repository(
                    repo_url,
                    status=evaluation['decision'],
                    evaluation_notes=evaluation['reason'],
                    notes=evaluation['notes'],
                    future_actions=evaluation['future_actions']
                )
                
                results[evaluation['decision']].append(full_name)
                
                print(f"  {evaluation['decision'].upper()}: {evaluation['reason']}")
                
            except Exception as e:
                print(f"  ❌ Error rechecking: {e}")
        
        return {'rechecked': len(check_later_repos), 'results': results}


def main():
    """
    CLI interface for AI evaluation.
    
    This provides command-line access to the AI evaluation functionality,
    useful for testing and manual evaluation operations.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Repository Evaluator')
    parser.add_argument('--process', help='Process discovered repos from JSON file')
    parser.add_argument('--recheck', action='store_true', help='Recheck repos marked for later')
    parser.add_argument('--api', choices=['openai', 'anthropic'], default='openai', help='API provider')
    parser.add_argument('--single', help='Evaluate single repo (owner/repo)')
    
    args = parser.parse_args()
    
    try:
        evaluator = AIEvaluator(api_provider=args.api)
        
        if args.process:
            if not Path(args.process).exists():
                print(f"❌ File {args.process} not found")
                return
            
            results = evaluator.process_discovered_repos(args.process)
            
            print(f"\\n📊 Results:")
            print(f"Mirror: {len(results['mirror'])}")
            print(f"Reject: {len(results['reject'])}")
            print(f"Check Later: {len(results['check_later'])}")
        
        elif args.recheck:
            results = evaluator.recheck_repos()
            print(f"\\n📊 Recheck Results:")
            print(f"Rechecked: {results['rechecked']}")
            for decision, repos in results['results'].items():
                print(f"{decision.title()}: {len(repos)}")
        
        elif args.single:
            # Evaluate single repository
            repo_data = {
                'full_name': args.single,
                'clone_url': f"https://github.com/{args.single}.git",
                'description': '',
                'stars': 0,
                'language': ''
            }
            
            evaluation = evaluator.evaluate_repo(repo_data)
            print(f"\\nEvaluation for {args.single}:")
            print(f"Decision: {evaluation['decision']}")
            print(f"Reason: {evaluation['reason']}")
            print(f"Notes: {evaluation['notes']}")
            print(f"Future Actions: {evaluation['future_actions']}")
        
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()