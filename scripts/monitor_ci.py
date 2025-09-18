#!/usr/bin/env python3
"""
Скрипт для мониторинга статуса GitHub Actions
"""

import requests
import os
from datetime import datetime


def get_github_workflows_status(repo_url):
    """Получает статус workflow'ов из GitHub API"""
    if not repo_url:
        print("GitHub repository URL not configured")
        return None
    
    try:
        # Извлекаем owner/repo из URL
        if "github.com" in repo_url:
            parts = repo_url.split("/")
            owner = parts[-2]
            repo = parts[-1].replace(".git", "")
        else:
            print("Invalid GitHub URL format")
            return None
        
        api_url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs"
        
        # Получаем токен из переменной окружения (если есть)
        headers = {}
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            headers["Authorization"] = f"token {github_token}"
        
        response = requests.get(api_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            print("Repository not found or not accessible")
            return None
        else:
            print(f"GitHub API error: {response.status_code}")
            return None
            
    except requests.RequestException as e:
        print(f"Error connecting to GitHub API: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def display_workflow_status(data):
    """Отображает статус workflow'ов"""
    if not data or "workflow_runs" not in data:
        print("No workflow data available")
        return
    
    runs = data["workflow_runs"][:5]  # Показываем последние 5 запусков
    
    print("GitHub Actions Status")
    print("=" * 50)
    
    if not runs:
        print("No workflow runs found")
        return
    
    for run in runs:
        status = run["status"]
        conclusion = run["conclusion"]
        workflow = run["name"]
        branch = run["head_branch"]
        commit = run["head_sha"][:7]
        
        # Выбираем иконку статуса
        if status == "completed":
            if conclusion == "success":
                icon = "✓"
                status_text = "SUCCESS"
            elif conclusion == "failure":
                icon = "✗"
                status_text = "FAILED"
            else:
                icon = "⚠"
                status_text = conclusion.upper()
        else:
            icon = "⏳"
            status_text = status.upper()
        
        # Форматируем время
        created_at = datetime.fromisoformat(
            run["created_at"].replace("Z", "+00:00")
        )
        time_str = created_at.strftime("%Y-%m-%d %H:%M")
        
        print(f"{icon} {workflow}")
        print(f"   Branch: {branch} ({commit})")
        print(f"   Status: {status_text}")
        print(f"   Time: {time_str}")
        print(f"   URL: {run['html_url']}")
        print()


def check_local_git_status():
    """Проверяет локальный статус Git"""
    try:
        import subprocess
        
        print("Local Git Status")
        print("=" * 50)
        
        # Проверяем текущую ветку
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, check=True
        )
        current_branch = result.stdout.strip()
        print(f"Current branch: {current_branch}")
        
        # Проверяем статус
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, check=True
        )
        
        if result.stdout.strip():
            print("Uncommitted changes detected:")
            print(result.stdout)
        else:
            print("✓ Working tree is clean")
        
        # Проверяем remote URL
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, check=True
        )
        remote_url = result.stdout.strip()
        print(f"Remote origin: {remote_url}")
        print()
        
        return remote_url
        
    except subprocess.CalledProcessError:
        print("Error: Not a git repository or git not available")
        return None
    except Exception as e:
        print(f"Error checking git status: {e}")
        return None


def main():
    """Основная функция"""
    print("CI/CD Status Monitor")
    print("=" * 60)
    print()
    
    # Проверяем локальный Git статус
    remote_url = check_local_git_status()
    
    # Получаем статус GitHub Actions
    if remote_url and "github.com" in remote_url:
        workflow_data = get_github_workflows_status(remote_url)
        display_workflow_status(workflow_data)
    else:
        print("GitHub Actions Status")
        print("=" * 50)
        print("Repository not configured with GitHub or no remote origin set")
        print("To monitor GitHub Actions:")
        print("1. Push your code to GitHub repository")
        print("2. Set up GitHub remote: git remote add origin <github-url>")
        print("3. Optionally set GITHUB_TOKEN environment variable for API access")
        print()
    
    # Показываем локальную проверку CI/CD
    print("Local CI/CD Health")
    print("=" * 50)
    print("Run 'python scripts/check_ci.py' for detailed local validation")


if __name__ == "__main__":
    main()