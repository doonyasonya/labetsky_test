#!/usr/bin/env python3
"""
Скрипт для проверки готовности CI/CD пайплайна
"""

import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """Выполняет команду и возвращает результат"""
    print(f"Checking {description}...")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=False,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"  ✓ {description} - OK")
            return True
        else:
            print(f"  ✗ {description} - FAILED")
            if result.stderr:
                print(f"    Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"  ✗ {description} - ERROR: {e}")
        return False


def check_files():
    """Проверяет наличие необходимых файлов"""
    files = [
        (".github/workflows/ci.yml", "CI workflow"),
        (".github/workflows/deploy.yml", "Deploy workflow"),
        (".flake8", "Flake8 config"),
        ("pyproject.toml", "Python project config"),
        (".gitignore", "Git ignore file"),
    ]
    
    print("Checking configuration files...")
    all_present = True
    for file_path, description in files:
        if Path(file_path).exists():
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ {description} - MISSING")
            all_present = False
    
    return all_present


def main():
    """Основная функция проверки CI/CD"""
    print("CI/CD Pipeline Health Check")
    print("=" * 40)
    
    checks = []
    
    # Проверка файлов конфигурации
    checks.append(check_files())
    
    # Проверка синтаксиса и критических ошибок
    checks.append(run_command(
        "flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics",
        "Critical syntax errors"
    ))
    
    # Проверка линтинга (только предупреждения)
    run_command(
        "flake8 . --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics",
        "Code style warnings (informational)"
    )
    
    # Проверка тестов (в Docker контейнере если доступен)
    if run_command("docker compose ps --services | grep api", "Docker compose availability"):
        checks.append(run_command(
            "docker compose exec api python -m pytest tests/test_api.py tests/test_file_endpoints.py -v --tb=short",
            "Unit tests (Docker)"
        ))
    else:
        print("  ⚠ Docker compose not available, skipping unit tests")
        print("    Run 'docker compose up -d' to enable test checking")
    
    # Проверка Docker build
    checks.append(run_command(
        "docker build -t image-processing-api-ci-test . > /dev/null 2>&1",
        "Docker build"
    ))
    
    print("\n" + "=" * 40)
    
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"✓ CI/CD Ready! All {total} checks passed.")
        print("\nYour pipeline is ready for:")
        print("  • GitHub Actions CI/CD")
        print("  • Automated testing")
        print("  • Docker builds")
        print("  • Quality checks")
        return 0
    else:
        print(f"✗ CI/CD Issues: {total - passed}/{total} checks failed.")
        print("\nFix the issues above before pushing to repository.")
        return 1


if __name__ == "__main__":
    sys.exit(main())