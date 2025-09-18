#!/usr/bin/env python3
"""
Скрипт для исправления типичных проблем CI/CD
"""

import subprocess
import sys
from pathlib import Path


def run_command(command, description, ignore_error=False):
    """Выполняет команду и выводит результат"""
    print(f"Running: {description}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=not ignore_error,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"  ✓ {description} - Success")
            if result.stdout.strip():
                print(f"    Output: {result.stdout.strip()}")
            return True
        else:
            print(f"  ✗ {description} - Failed")
            if result.stderr.strip():
                print(f"    Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"  ✗ {description} - Error: {e}")
        return False


def fix_file_permissions():
    """Исправляет права доступа к файлам"""
    print("\n1. Fixing file permissions...")
    
    # Делаем скрипты исполняемыми
    scripts_dir = Path("scripts")
    if scripts_dir.exists():
        for script_file in scripts_dir.glob("*.py"):
            run_command(f"chmod +x {script_file}", f"Make {script_file.name} executable", ignore_error=True)


def cleanup_docker_resources():
    """Очищает Docker ресурсы"""
    print("\n2. Cleaning up Docker resources...")
    
    run_command("docker system prune -f", "Clean Docker system", ignore_error=True)
    run_command("docker volume prune -f", "Clean Docker volumes", ignore_error=True)
    run_command("docker network prune -f", "Clean Docker networks", ignore_error=True)


def fix_storage_directories():
    """Создает необходимые директории"""
    print("\n3. Creating storage directories...")
    
    storage_dirs = [
        "storage/original",
        "storage/thumbs/100x100",
        "storage/thumbs/300x300", 
        "storage/thumbs/1200x1200"
    ]
    
    for dir_path in storage_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created directory: {dir_path}")


def update_dependencies():
    """Обновляет зависимости"""
    print("\n4. Updating dependencies...")
    
    run_command("pip install --upgrade pip", "Upgrade pip")
    run_command("pip install -r requirements.txt --upgrade", "Update dependencies", ignore_error=True)


def fix_git_issues():
    """Исправляет проблемы Git"""
    print("\n5. Fixing Git issues...")
    
    # Проверяем статус Git
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True
    )
    
    if result.stdout.strip():
        print("  Uncommitted changes found:")
        print(result.stdout)
        
        response = input("  Do you want to commit changes? (y/N): ")
        if response.lower() == 'y':
            run_command("git add .", "Stage changes")
            commit_msg = input("  Enter commit message: ") or "Fix CI/CD issues"
            run_command(f'git commit -m "{commit_msg}"', "Commit changes")
            
            response = input("  Do you want to push changes? (y/N): ")
            if response.lower() == 'y':
                run_command("git push", "Push changes")
    else:
        print("  ✓ Working tree is clean")


def restart_docker_compose():
    """Перезапускает Docker Compose"""
    print("\n6. Restarting Docker Compose...")
    
    run_command("docker compose down", "Stop services", ignore_error=True)
    run_command("docker compose up -d", "Start services")
    
    # Ждем готовности сервисов
    import time
    print("  Waiting for services to be ready...")
    time.sleep(10)
    
    run_command("docker compose ps", "Check services status")


def run_health_checks():
    """Запускает проверки здоровья"""
    print("\n7. Running health checks...")
    
    run_command("python scripts/check_ci.py", "CI/CD health check")
    run_command("python scripts/check_system.py", "System health check", ignore_error=True)


def main():
    """Основная функция"""
    print("CI/CD Issues Fixer")
    print("=" * 50)
    print("This script will attempt to fix common CI/CD issues")
    print()
    
    if not Path("requirements.txt").exists():
        print("Error: requirements.txt not found. Are you in the project root?")
        sys.exit(1)
    
    steps = [
        ("Fix file permissions", fix_file_permissions),
        ("Clean Docker resources", cleanup_docker_resources),
        ("Create storage directories", fix_storage_directories),
        ("Update dependencies", update_dependencies),
        ("Fix Git issues", fix_git_issues),
        ("Restart Docker Compose", restart_docker_compose),
        ("Run health checks", run_health_checks),
    ]
    
    print("Available fixes:")
    for i, (name, _) in enumerate(steps, 1):
        print(f"  {i}. {name}")
    
    print("\nOptions:")
    print("  a - Run all fixes")
    print("  q - Quit")
    print("  1-7 - Run specific fix")
    
    while True:
        choice = input("\nEnter your choice: ").strip().lower()
        
        if choice == 'q':
            print("Exiting...")
            break
        elif choice == 'a':
            print("\nRunning all fixes...")
            for name, func in steps:
                print(f"\n--- {name} ---")
                func()
            print("\n" + "=" * 50)
            print("All fixes completed!")
            break
        elif choice.isdigit() and 1 <= int(choice) <= len(steps):
            idx = int(choice) - 1
            name, func = steps[idx]
            print(f"\n--- {name} ---")
            func()
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()