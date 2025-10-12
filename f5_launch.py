#!/usr/bin/env python3
"""
F5 Quick Launch Configuration для PneumoStabSim Professional
Автоматическая настройка окружения для отладки
"""
import os
import sys
import subprocess
from pathlib import Path

class F5LaunchConfig:
    """Конфигуратор для быстрого запуска (F5) в различных IDE"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.venv_path = self.project_root / "venv"
        self.requirements_file = self.project_root / "requirements.txt"
        
    def setup_environment(self):
        """Настройка окружения для отладки"""
        print("🔧 F5 Launch: Настройка окружения...")
        
        # Проверка и создание виртуального окружения
        if not self._check_venv():
            if not self._create_venv():
                return False
        
        # Проверка зависимостей
        if not self._check_dependencies():
            if not self._install_dependencies():
                return False
        
        # Настройка переменных окружения
        self._setup_env_vars()
        
        print("✅ F5 Launch: Окружение готово!")
        return True
    
    def _check_venv(self):
        """Проверка наличия виртуального окружения"""
        python_exe = self.venv_path / ("Scripts/python.exe" if os.name == 'nt' else "bin/python")
        return python_exe.exists()
    
    def _create_venv(self):
        """Создание виртуального окружения"""
        print("📦 Создание виртуального окружения...")
        try:
            subprocess.run([sys.executable, "-m", "venv", str(self.venv_path)], 
                         check=True, cwd=self.project_root)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка создания venv: {e}")
            return False
    
    def _check_dependencies(self):
        """Проверка установленных зависимостей"""
        if not self.requirements_file.exists():
            return True
            
        pip_exe = self.venv_path / ("Scripts/pip.exe" if os.name == 'nt' else "bin/pip")
        if not pip_exe.exists():
            return False
            
        try:
            # Проверяем наличие PySide6 как основной зависимости
            result = subprocess.run([str(pip_exe), "show", "PySide6"], 
                                  capture_output=True, text=True, cwd=self.project_root)
            return result.returncode == 0
        except Exception:
            return False
    
    def _install_dependencies(self):
        """Установка зависимостей"""
        print("📥 Установка зависимостей...")
        pip_exe = self.venv_path / ("Scripts/pip.exe" if os.name == 'nt' else "bin/pip")
        
        try:
            # Обновляем pip
            subprocess.run([str(pip_exe), "install", "--upgrade", "pip"], 
                         check=True, cwd=self.project_root)
            
            # Устанавливаем зависимости
            subprocess.run([str(pip_exe), "install", "-r", str(self.requirements_file)], 
                         check=True, cwd=self.project_root)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка установки зависимостей: {e}")
            return False
    
    def _setup_env_vars(self):
        """Настройка переменных окружения"""
        env_vars = {
            'PYTHONPATH': f"{self.project_root};{self.project_root / 'src'}",
            'QT_SCALE_FACTOR_ROUNDING_POLICY': 'PassThrough',
            'QT_AUTO_SCREEN_SCALE_FACTOR': '1',
            'QT_ENABLE_HIGHDPI_SCALING': '1',
        }
        
        for key, value in env_vars.items():
            os.environ[key] = str(value)
    
    def launch_debug_mode(self):
        """Запуск в режиме отладки"""
        if not self.setup_environment():
            return False
        
        print("🚀 F5 Launch: Запуск PneumoStabSim в режиме отладки...")
        
        # Настройка отладочных переменных
        debug_env = os.environ.copy()
        debug_env.update({
            'QT_DEBUG_PLUGINS': '1',
            'QT_LOGGING_RULES': '*.debug=true;js.debug=true;qt.qml.debug=true',
            'PYTHONDEBUG': '1'
        })
        
        # Запуск приложения
        python_exe = self.venv_path / ("Scripts/python.exe" if os.name == 'nt' else "bin/python")
        app_path = self.project_root / "app.py"
        
        try:
            process = subprocess.Popen(
                [str(python_exe), str(app_path), "--debug"],
                cwd=self.project_root,
                env=debug_env
            )
            return process
        except Exception as e:
            print(f"❌ Ошибка запуска: {e}")
            return None
    
    def launch_normal_mode(self):
        """Запуск в обычном режиме"""
        if not self.setup_environment():
            return False
        
        print("🚀 F5 Launch: Запуск PneumoStabSim...")
        
        python_exe = self.venv_path / ("Scripts/python.exe" if os.name == 'nt' else "bin/python")
        app_path = self.project_root / "app.py"
        
        try:
            process = subprocess.Popen(
                [str(python_exe), str(app_path)],
                cwd=self.project_root,
                env=os.environ.copy()
            )
            return process
        except Exception as e:
            print(f"❌ Ошибка запуска: {e}")
            return None

def main():
    """Главная функция для F5 запуска"""
    launcher = F5LaunchConfig()
    
    # Определяем режим запуска из аргументов
    debug_mode = "--debug" in sys.argv or "-d" in sys.argv
    
    if debug_mode:
        process = launcher.launch_debug_mode()
    else:
        process = launcher.launch_normal_mode()
    
    if process:
        try:
            # Ждем завершения процесса
            process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Получен сигнал прерывания, завершение...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

if __name__ == "__main__":
    main()
