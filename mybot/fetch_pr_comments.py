#!/usr/bin/env python3
"""
Script to fetch comments from a GitHub Pull Request and implement fixes
"""
import os
import sys
import requests
from typing import Dict, List, Optional
import json

def get_github_token() -> Optional[str]:
    """Get GitHub token from environment variable"""
    return os.environ.get('GITHUB_TOKEN') or os.environ.get('GITHUB_API_TOKEN')

def fetch_pr_info(owner: str, repo: str, pr_number: int, token: Optional[str] = None) -> Dict:
    """Fetch PR information from GitHub API"""
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'PR-Comment-Extractor'
    }
    if token:
        headers['Authorization'] = f'token {token}'
    
    url = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}'
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Failed to fetch PR info: {response.status_code} - {response.text}")
    
    return response.json()

def fetch_pr_reviews(owner: str, repo: str, pr_number: int, token: Optional[str] = None) -> List[Dict]:
    """Fetch PR reviews from GitHub API"""
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'PR-Comment-Extractor'
    }
    if token:
        headers['Authorization'] = f'token {token}'
    
    url = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/reviews'
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Failed to fetch PR reviews: {response.status_code} - {response.text}")
    
    return response.json()

def fetch_pr_comments(owner: str, repo: str, pr_number: int, token: Optional[str] = None) -> List[Dict]:
    """Fetch PR comments from GitHub API"""
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'PR-Comment-Extractor'
    }
    if token:
        headers['Authorization'] = f'token {token}'
    
    url = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/comments'
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Failed to fetch PR comments: {response.status_code} - {response.text}")
    
    return response.json()

def fetch_pr_files(owner: str, repo: str, pr_number: int, token: Optional[str] = None) -> List[Dict]:
    """Fetch files modified in the PR from GitHub API"""
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'PR-Comment-Extractor'
    }
    if token:
        headers['Authorization'] = f'token {token}'
    
    url = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files'
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Failed to fetch PR files: {response.status_code} - {response.text}")
    
    return response.json()

def classify_comment(comment: Dict) -> str:
    """Classify comment by type: blocking, suggestion, or question"""
    body = comment.get('body', '').lower()
    
    # Check for blocking issues
    if any(word in body for word in ['must', 'required', 'error', 'bug', 'fix', 'broken']):
        return '🔴 Bloqueante'
    
    # Check for suggestions
    if any(word in body for word in ['consider', 'suggest', 'could', 'maybe', 'perhaps', 'should']):
        return '🟡 Sugerencia'
    
    # Check for questions
    if '?' in body or 'why' in body or 'how' in body:
        return '🔵 Pregunta'
    
    # Default to suggestion
    return '🟡 Sugerencia'

def analyze_pr_comments(owner: str, repo: str, pr_number: int) -> Dict:
    """Analyze PR comments and return classified results"""
    token = get_github_token()
    
    # Fetch all PR data
    pr_info = fetch_pr_info(owner, repo, pr_number, token)
    pr_reviews = fetch_pr_reviews(owner, repo, pr_number, token)
    pr_comments = fetch_pr_comments(owner, repo, pr_number, token)
    pr_files = fetch_pr_files(owner, repo, pr_number, token)
    
    # Classify comments
    classified_comments = []
    for comment in pr_comments:
        classified_comments.append({
            'file': comment.get('path'),
            'line': comment.get('line'),
            'reviewer': comment.get('user', {}).get('login'),
            'body': comment.get('body'),
            'type': classify_comment(comment),
            'url': comment.get('html_url')
        })
    
    # Classify reviews
    review_comments = []
    for review in pr_reviews:
        if review.get('body'):
            review_comments.append({
                'reviewer': review.get('user', {}).get('login'),
                'body': review.get('body'),
                'state': review.get('state'),
                'type': 'review'
            })
    
    return {
        'pr_info': pr_info,
        'comments': classified_comments,
        'reviews': review_comments,
        'files': pr_files
    }

def main():
    if len(sys.argv) != 2:
        print("Usage: python fetch_pr_comments.py <PR_NUMBER>")
        sys.exit(1)
    
    pr_number = int(sys.argv[1])
    owner = "bolt_ok"
    repo = "mybot"
    
    try:
        result = analyze_pr_comments(owner, repo, pr_number)
        
        # Print PR information
        pr_info = result['pr_info']
        print(f"## 🔍 Análisis del PR#{pr_number}")
        print(f"**Título:** {pr_info.get('title', 'N/A')}")
        print(f"**Autor:** {pr_info.get('user', {}).get('login', 'N/A')}")
        print(f"**Archivos modificados:** {len(result['files'])}")
        for file in result['files']:
            print(f"  - {file.get('filename')}")
        
        # Print classified comments
        print(f"\n## 📝 Comentarios extraídos")
        
        # Group by type
        blocking_comments = [c for c in result['comments'] if c['type'] == '🔴 Bloqueante']
        suggestion_comments = [c for c in result['comments'] if c['type'] == '🟡 Sugerencia']
        question_comments = [c for c in result['comments'] if c['type'] == '🔵 Pregunta']
        
        print(f"### 🔴 Bloqueantes ({len(blocking_comments)})")
        for i, comment in enumerate(blocking_comments, 1):
            print(f"{i}. **{comment['file']}:{comment['line']}** - @{comment['reviewer']} > {comment['body']}")
        
        print(f"\n### 🟡 Sugerencias ({len(suggestion_comments)})")
        for i, comment in enumerate(suggestion_comments, 1):
            print(f"{i}. **{comment['file']}:{comment['line']}** - @{comment['reviewer']} > {comment['body']}")
        
        print(f"\n### 🔵 Preguntas ({len(question_comments)})")
        for i, comment in enumerate(question_comments, 1):
            print(f"{i}. **{comment['file']}:{comment['line']}** - @{comment['reviewer']} > {comment['body']}")
        
        # Save results to a file for further processing
        with open(f'pr_{pr_number}_comments.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Results saved to pr_{pr_number}_comments.json")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()