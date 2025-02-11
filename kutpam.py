import sys
import subprocess
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtCore import Qt, QEvent
import os
import requests
from urllib.parse import quote
from PIL import Image
from io import BytesIO

STYLE = """
QMainWindow, QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
}
QLineEdit {
    padding: 8px;
    border: 2px solid #2d8aaf;
    border-radius: 4px;
    background-color: #2d2d2d;
    color: #e0e0e0;
}
QPushButton {
    padding: 8px 15px;
    background-color: #2d8aaf;
    border: none;
    border-radius: 4px;
    color: #ffffff;
    font-weight: bold;
}
QListWidget {
    border: 2px solid #2d8aaf;
    border-radius: 4px;
    background-color: #2d2d2d;
    color: #e0e0e0;
    padding: 5px;
}

QListWidget::item {
    color: #e0e0e0;
    background-color: #2d2d2d;
    border-bottom: 1px solid #383838;
    padding: 8px;
}

QListWidget::item[installed="true"] {
    color: #50fa7b;
}

QListWidget::item:selected {
    background-color: #2d8aaf;
    color: #ffffff !important;
}

QListWidget::item:hover {
    background-color: #383838;
}

QListWidget QScrollBar:vertical {
    background-color: #2d2d2d;
    width: 12px;
    margin: 0px;
}

QListWidget QScrollBar::handle:vertical {
    background-color: #2d8aaf;
    border-radius: 6px;
    min-height: 20px;
}

QListWidget QScrollBar::add-line:vertical,
QListWidget QScrollBar::sub-line:vertical {
    height: 0px;
}

QTextEdit {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 2px solid #2d8aaf;
    border-radius: 4px;
    padding: 5px;
    selection-background-color: #2d8aaf;
    selection-color: #ffffff;
}

QTextEdit QScrollBar:vertical {
    background-color: #2d2d2d;
    width: 12px;
    margin: 0px;
}

QTextEdit QScrollBar::handle:vertical {
    background-color: #2d8aaf;
    border-radius: 6px;
    min-height: 20px;
}

QTextEdit QScrollBar::add-line:vertical,
QTextEdit QScrollBar::sub-line:vertical {
    height: 0px;
}
"""

STYLE += """
QProgressBar {
    border: 2px solid #2d8aaf;
    border-radius: 4px;
    background-color: #2d2d2d;
    color: #e0e0e0;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #2d8aaf;
    width: 10px;
}
"""

def is_root():
    """Check if the script is being run as root"""
    return os.geteuid() == 0

def run_as_root():
    """Restart the application with root privileges"""
    try:
        # XAUTHORITY ve DISPLAY değişkenlerini koru
        xauth = os.getenv('XAUTHORITY', os.path.expanduser('~/.Xauthority'))
        display = os.getenv('DISPLAY', ':0')
        runtime_dir = os.getenv('XDG_RUNTIME_DIR', '/run/user/{}'.format(os.getuid()))
        
        env = os.environ.copy()
        env.update({
            'XAUTHORITY': xauth,
            'DISPLAY': display,
            'XDG_RUNTIME_DIR': runtime_dir,
            'DBUS_SESSION_BUS_ADDRESS': 'unix:path=/run/user/{}/bus'.format(os.getuid())
        })
        
        subprocess.check_call(['sudo', '-E', 'python3'] + sys.argv, env=env)
    except subprocess.CalledProcessError as e:
        print("Error: " + str(e))
        sys.exit(1)

def get_logo_path():
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "kutpamlo.png")
    elif os.path.exists("/usr/share/icons/hicolor/48x48/apps/kutpamlo.png"):
        return "/usr/share/icons/hicolor/48x48/apps/kutpamlo.png"
    home_dir = os.path.expanduser("/usr/share/icons/hicolor/48x48/apps/kutpamlo.png")
    if os.path.exists(home_dir):
        return home_dir
    return "kutpamlo.png"

def get_icon_path():
    """Simge dosyasının yolunu döndürür."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "kutpamlo.png")
    elif os.path.exists("/usr/share/icons/hicolor/48x48/apps/kutpamlo.png"):
        return "/usr/share/icons/hicolor/48x48/apps/kutpamlo.png"
    return None

LOGO_PATH = get_logo_path()
ICON_PATH = get_icon_path()

class SearchThread(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    
    def __init__(self, search_term, parent=None):
        super().__init__(parent)
        self.search_term = search_term

    def run(self):
        try:
            cmd = f"apt-cache search --names-only {self.search_term}"
            self.process = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True
            )
            
            if self.process.returncode != 0:
                self.error.emit(self.process.stderr)
                return
                
            packages = []
            for line in self.process.stdout.splitlines():
                if " - " in line:
                    pkg_name = line.split(" - ")[0].strip()
                    # Her paket için detaylı bilgi al
                    pkg_details_cmd = f"apt-cache show {pkg_name}"
                    details = subprocess.run(pkg_details_cmd, shell=True, capture_output=True, text=True)
                    
                    pkg_info = {"name": pkg_name, "description": "", "size": "", "maintainer": "", "version": ""}
                    
                    if details.returncode == 0:
                        for detail_line in details.stdout.splitlines():
                            if detail_line.startswith("Description-tr:"):
                                pkg_info["description"] = detail_line.split(":", 1)[1].strip()
                            elif detail_line.startswith("Installed-Size:"):
                                size = int(detail_line.split(":", 1)[1].strip())
                                pkg_info["size"] = f"{size/1024:.1f} MB" if size >= 1024 else f"{size} KB"
                            elif detail_line.startswith("Maintainer:"):
                                pkg_info["maintainer"] = detail_line.split(":", 1)[1].strip()
                            elif detail_line.startswith("Version:"):
                                pkg_info["version"] = detail_line.split(":", 1)[1].strip()
                    
                    packages.append(pkg_info)
            
            self.finished.emit(packages)
        except Exception as e:
            self.error.emit(str(e))

class IconManager:
    def __init__(self):
        self.cache_dir = os.path.expanduser("~/.cache/paket-manager/icons")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.default_icon = QIcon.fromTheme("package")
        self.icon_cache = {}

    def get_package_icon(self, package_name):
        cache_path = os.path.join(self.cache_dir, f"{package_name}.png")
        
        if os.path.exists(cache_path):
            return QIcon(cache_path)
            
        try:
            # Ubuntu paket sunucusundan ikon indirme
            url = f"https://packages.ubuntu.com/icons/{quote(package_name)}.png"
            response = requests.get(url)
            
            if response.status_code == 200:
                # İkonu önbelleğe kaydet
                img = Image.open(BytesIO(response.content))
                img = img.resize((32, 32), Image.Resampling.LANCZOS)
                img.save(cache_path)
                return QIcon(cache_path)
        except:
            pass
            
        return self.default_icon

def format_size(size_kb):
    """Boyutu okunaklı formata çevirir"""
    if size_kb < 1024:  # < 1MB
        return f"{size_kb:.1f} KB"
    elif size_kb < 1024*1024:  # < 1GB
        return f"{size_kb/1024:.1f} MB"
    else:  # >= 1GB
        return f"{size_kb/(1024*1024):.1f} GB"

class PackageDetailsDialog(QDialog):
    def __init__(self, package_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{package_name} - Paket Detayları")
        self.setMinimumWidth(700)
        self.setMinimumHeight(700)
        
        try:
            layout = QVBoxLayout()
            self.text_area = QTextEdit()
            self.text_area.setReadOnly(True)
            layout.addWidget(self.text_area)
            
            # HTML Stili
            html_style = """
            <style>
                body { 
                    font-family: 'Segoe UI', Arial; 
                    background-color: #2d2d2d; 
                    color: #e0e0e0;
                    padding: 20px;
                }
                .container {
                    background-color: #333333;
                    border-radius: 8px;
                    padding: 20px;
                    margin-bottom: 20px;
                }
                .header {
                    color: #2d8aaf;
                    font-size: 24px;
                    margin-bottom: 20px;
                }
                .info-row {
                    display: flex;
                    margin: 10px 0;
                    padding: 10px;
                    background-color: #2d2d2d;
                    border-radius: 4px;
                }
                .label {
                    color: #2d8aaf;
                    font-weight: bold;
                    width: 150px;
                }
                .value {
                    color: #e0e0e0;
                    flex: 1;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }
                th {
                    background-color: #2d8aaf;
                    color: white;
                    padding: 12px;
                    text-align: left;
                }
                td {
                    padding: 12px;
                    border-bottom: 1px solid #444;
                }
                tr:hover {
                    background-color: #383838;
                }
            </style>
            """
            
            # Paket bilgilerini al
            cmd = f"apt-cache show {package_name}"
            process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if process.returncode == 0:
                html_content = f"{html_style}<div class='container'>"
                html_content += f"<div class='header'>{package_name}</div>"
                
                description = ""
                current_version = {}
                versions = []
                
                for line in process.stdout.splitlines():
                    if line.strip():
                        if line.startswith("Description-tr:"):
                            description = line.split(":", 1)[1].strip()
                            continue
                        elif line.startswith("Description:") and not description:
                            description = line.split(":", 1)[1].strip()
                            continue
                        
                        if line.startswith("Version:"):
                            if current_version:
                                versions.append(current_version.copy())
                            current_version = {"Sürüm:": line.split(":", 1)[1].strip()}
                            
                        if line.startswith("Installed-Size:"):
                            size_kb = float(line.split(":", 1)[1].strip())
                            current_version["Kurulum Boyutu:"] = format_size(size_kb)
                
                if current_version:
                    versions.append(current_version)
                
                # Açıklamayı ekle
                if description:
                    html_content += f"""
                    <div class='info-row'>
                        <div class='label'>Açıklama:</div>
                        <div class='value'>{description}</div>
                    </div>"""
                
                # Sürüm geçmişi
                if versions:
                    html_content += "<h3 style='color:#2d8aaf; margin-top:30px;'>Sürüm Geçmişi</h3>"
                    html_content += "<table>"
                    html_content += "<tr><th>Sürüm</th><th>Boyut</th></tr>"
                    
                    for version in versions:
                        html_content += f"<tr><td>{version.get('Sürüm:', '-')}</td>"
                        html_content += f"<td>{version.get('Kurulum Boyutu:', '-')}</td></tr>"
                    
                    html_content += "</table>"
                
                html_content += "</div>"
                self.text_area.setHtml(html_content)
            
            close_btn = QPushButton("Kapat")
            close_btn.clicked.connect(self.close)
            close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2d8aaf;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #3899c2;
                }
            """)
            layout.addWidget(close_btn)
            self.setLayout(layout)
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Paket detayları alınırken hata oluştu: {str(e)}")

class FlatpakManager:
    def __init__(self):
        self.packages = []
    
    def search_packages(self, term):
        try:
            # Arama komutunu düzelt
            cmd = ["flatpak", "search", term]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return self.parse_search_results(result.stdout)
            return []
        except Exception as e:
            print(f"Arama hatası: {str(e)}")
            return []
            
    def parse_search_results(self, output):
        packages = []
        lines = output.strip().split('\n')
        
        # İlk satırı (başlık) atla
        for line in lines[1:]:
            if line.strip():
                # Tab ile ayrılmış değerleri al
                parts = line.split('\t')
                if len(parts) >= 2:  # En az isim ve ID olmalı
                    pkg = {
                        'name': parts[0].strip(),
                        'id': parts[1].strip() if len(parts) > 1 else '',
                        'version': parts[2].strip() if len(parts) > 2 else '',
                        'description': parts[3].strip() if len(parts) > 3 else ''
                    }
                    packages.append(pkg)
        return packages

    def get_app_id(self, package_id):
        try:
            # Temiz ID al
            clean_id = package_id.split()[0].strip()
            if '/' not in clean_id:
                # Flathub'dan tam ID'yi al
                search_cmd = ["flatpak", "search", "--columns=application", clean_id]
                result = subprocess.run(search_cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip().split('\n')[0]
            return clean_id
        except:
            return None

    def install_package(self, package_id):
        try:
            app_id = self.get_app_id(package_id)
            if not app_id:
                return None
                
            # Flathub kaynağını ekle
            subprocess.run(["flatpak", "remote-add", "--if-not-exists", "flathub", 
                          "https://flathub.org/repo/flathub.flatpakrepo"])
            
            # Kurulum komutları
            commands = [
                ["flatpak", "install", "-y", "flathub", app_id],
                ["flatpak", "update", "-y", app_id]
            ]
            
            for cmd in commands:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    return result
            return result
            
        except Exception as e:
            print(f"Kurulum hatası: {str(e)}")
            return None

    def remove_package(self, package_id):
        try:
            app_id = self.get_app_id(package_id)
            if not app_id:
                return None
            
            # Tam ref ile kaldır
            cmd = ["flatpak", "uninstall", "-y", "--force-remove", app_id]
            return subprocess.run(cmd, capture_output=True, text=True)
            
        except Exception as e:
            print(f"Kaldırma hatası: {str(e)}")
            return None

    def check_if_installed(self, package_id):
        """Paketin kurulu olup olmadığını kontrol et"""
        try:
            app_id = self.get_app_id(package_id)
            if not app_id:
                return False
                
            cmd = ["flatpak", "list", "--app", "--columns=application"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                installed_apps = result.stdout.strip().split('\n')
                return app_id in installed_apps
            return False
            
        except:
            return False

class FlatpakDetailsDialog(QDialog):
    def __init__(self, package_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Flatpak Paket Detayları")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        
        layout = QVBoxLayout()
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        layout.addWidget(self.text_area)
        
        html_style = """
        <style>
            body { 
                font-family: 'Segoe UI', Arial; 
                background-color: #2d2d2d; 
                color: #e0e0e0;
                padding: 20px;
            }
            .container {
                background-color: #333333;
                border-radius: 8px;
                padding: 20px;
            }
            .header {
                color: #2d8aaf;
                font-size: 24px;
                margin-bottom: 20px;
            }
            .info-row {
                display: flex;
                margin: 10px 0;
                padding: 10px;
                background-color: #2d2d2d;
                border-radius: 4px;
            }
            .label {
                color: #2d8aaf;
                font-weight: bold;
                width: 150px;
            }
            .value {
                color: #e0e0e0;
                flex: 1;
            }
        </style>
        """
        
        # Flatpak detaylarını al
        cmd = ["flatpak", "info", package_id]
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        if process.returncode == 0:
            html_content = f"{html_style}<div class='container'>"
            html_content += f"<div class='header'>{package_id}</div>"
            
            translations = {
                "Application": "Uygulama",
                "Version": "Sürüm",
                "Branch": "Dal",
                "Installation": "Kurulum",
                "Description": "Açıklama",
                "Download": "İndirme Boyutu",
                "Installed": "Kurulu Boyut",
                "Runtime": "Çalışma Zamanı",
                "ID": "Kimlik",
                "Origin": "Kaynak",
                "Homepage": "Ana Sayfa",
                "Size": "Boyut"
            }
            
            for line in process.stdout.splitlines():
                if ":" in line:
                    label, value = line.split(":", 1)
                    label = label.strip()
                    translated_label = translations.get(label, label)
                    
                    html_content += f"""
                    <div class='info-row'>
                        <div class='label'>{translated_label}</div>
                        <div class='value'>{value.strip()}</div>
                    </div>"""
            
            html_content += "</div>"
            self.text_area.setHtml(html_content)
        
        close_btn = QPushButton("Kapat")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d8aaf;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3899c2;
            }
        """)
        layout.addWidget(close_btn)
        self.setLayout(layout)

class RepoManagerDialog(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        
        # Repo listesi bölümü
        list_group = QGroupBox("Aktif Depolar")
        list_layout = QVBoxLayout()
        
        self.repo_list = QListWidget()
        self.repo_list.setAlternatingRowColors(True)
        search_box = QLineEdit()
        search_box.setPlaceholderText("Depo ara...")
        search_box.textChanged.connect(self.filter_repos)
        
        list_layout.addWidget(search_box)
        list_layout.addWidget(self.repo_list)
        list_group.setLayout(list_layout)
        
        # Buton grubu
        button_group = QGroupBox("İşlemler")
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Depo Ekle")
        self.add_button.setIcon(QIcon.fromTheme("list-add"))
        self.edit_button = QPushButton("Depo Düzenle")
        self.edit_button.setIcon(QIcon.fromTheme("document-edit"))
        self.remove_button = QPushButton("Depo Kaldır")
        self.remove_button.setIcon(QIcon.fromTheme("list-remove"))
        self.update_button = QPushButton("Tüm Depoları Güncelle")
        self.update_button.setIcon(QIcon.fromTheme("view-refresh"))
        
        for btn in [self.add_button, self.edit_button, self.remove_button, self.update_button]:
            button_layout.addWidget(btn)
            
        button_group.setLayout(button_layout)
        
        # İstatistik grubu
        stats_group = QGroupBox("Depo İstatistikleri")
        stats_layout = QGridLayout()
        
        self.total_repos_label = QLabel("Toplam Depo: 0")
        self.active_repos_label = QLabel("Aktif Depo: 0")
        self.last_update_label = QLabel("Son Güncelleme: -")
        
        stats_layout.addWidget(self.total_repos_label, 0, 0)
        stats_layout.addWidget(self.active_repos_label, 0, 1)
        stats_layout.addWidget(self.last_update_label, 0, 2)
        
        stats_group.setLayout(stats_layout)
        
        # Ana düzene ekle
        layout.addWidget(stats_group)
        layout.addWidget(list_group)
        layout.addWidget(button_group)
        
        self.setLayout(layout)
        
        # Bağlantılar
        self.add_button.clicked.connect(self.add_repo)
        self.edit_button.clicked.connect(self.edit_repo)
        self.remove_button.clicked.connect(self.remove_repo)
        self.update_button.clicked.connect(self.update_repos)
        
        # Depoları yükle
        self.load_repos()
        self.update_stats()

    def load_repos(self):
        """sources.list dosyasından depoları yükle"""
        try:
            self.repo_list.clear()
            sources_paths = ["/etc/apt/sources.list"]
            sources_dir = "/etc/apt/sources.list.d"
            
            # sources.list.d dizinindeki .list dosyalarını da ekle
            if os.path.exists(sources_dir):
                sources_paths.extend([os.path.join(sources_dir, f) for f in os.listdir(sources_dir) if f.endswith('.list')])
            
            for source_path in sources_paths:
                if os.path.exists(source_path):
                    with open(source_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                item = QListWidgetItem(line)
                                item.setData(Qt.UserRole, source_path)  # Dosya yolunu sakla
                                self.repo_list.addItem(item)
            
            self.update_stats()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Depolar yüklenirken hata oluştu: {str(e)}")

    def add_repo(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Yeni Depo Ekle")
        layout = QVBoxLayout()
        
        repo_input = QLineEdit()
        repo_input.setPlaceholderText("deb http://archive.ubuntu.com/ubuntu jammy main")
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, dialog
        )
        
        layout.addWidget(QLabel("Depo Satırı:"))
        layout.addWidget(repo_input)
        layout.addWidget(buttons)
        dialog.setLayout(layout)
        
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        if dialog.exec_() == QDialog.Accepted:
            repo_line = repo_input.text().strip()
            if repo_line:
                try:
                    with open("/etc/apt/sources.list", "a") as f:
                        f.write(f"\n{repo_line}")
                    self.load_repos()
                    subprocess.run(["sudo", "apt-get", "update"])
                except Exception as e:
                    QMessageBox.critical(self, "Hata", f"Depo eklenirken hata oluştu: {str(e)}")

    def edit_repo(self):
        current = self.repo_list.currentItem()
        if not current:
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle("Depo Düzenle")
        layout = QVBoxLayout()
        
        repo_input = QLineEdit(current.text())
        source_path = current.data(Qt.UserRole)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, dialog
        )
        
        layout.addWidget(QLabel(f"Kaynak Dosya: {source_path}"))
        layout.addWidget(QLabel("Depo Satırı:"))
        layout.addWidget(repo_input)
        layout.addWidget(buttons)
        dialog.setLayout(layout)
        
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        if dialog.exec_() == QDialog.Accepted:
            new_line = repo_input.text().strip()
            if new_line:
                try:
                    # Dosyayı oku
                    with open(source_path, 'r') as f:
                        lines = f.readlines()
                    
                    # Eski satırı bul ve değiştir
                    for i, line in enumerate(lines):
                        if line.strip() == current.text():
                            lines[i] = new_line + '\n'
                            break
                    
                    # Dosyaya geri yaz
                    with open(source_path, 'w') as f:
                        f.writelines(lines)
                    
                    self.load_repos()
                    subprocess.run(["sudo", "apt-get", "update"])
                except Exception as e:
                    QMessageBox.critical(self, "Hata", f"Depo düzenlenirken hata oluştu: {str(e)}")

    def remove_repo(self):
        current = self.repo_list.currentItem()
        if not current:
            return
            
        reply = QMessageBox.question(self, 'Depo Kaldır',
                                   'Bu depoyu kaldırmak istediğinize emin misiniz?',
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                                   
        if reply == QMessageBox.Yes:
            try:
                source_path = current.data(Qt.UserRole)
                repo_line = current.text()
                
                # Dosyayı oku
                with open(source_path, 'r') as f:
                    lines = f.readlines()
                
                # Depo satırını kaldır
                lines = [line for line in lines if line.strip() != repo_line]
                
                # Dosyaya geri yaz
                with open(source_path, 'w') as f:
                    f.writelines(lines)
                
                self.load_repos()
                subprocess.run(["sudo", "apt-get", "update"])
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Depo kaldırılırken hata oluştu: {str(e)}")

    def filter_repos(self, text):
        for i in range(self.repo_list.count()):
            item = self.repo_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())
            
    def update_stats(self):
        total = self.repo_list.count()
        active = sum(1 for i in range(total) if not self.repo_list.item(i).isHidden())
        
        self.total_repos_label.setText(f"Toplam Depo: {total}")
        self.active_repos_label.setText(f"Aktif Depo: {active}")
        
        # Son güncelleme zamanını al
        try:
            last_update = os.path.getmtime("/var/lib/apt/periodic/update-success-stamp")
            last_update = datetime.fromtimestamp(last_update).strftime("%Y-%m-%d %H:%M")
            self.last_update_label.setText(f"Son Güncelleme: {last_update}")
        except:
            self.last_update_label.setText("Son Güncelleme: Bilinmiyor")

    def update_repos(self):
        try:
            subprocess.run(["sudo", "apt-get", "update"], check=True)
            QMessageBox.information(self, "Başarılı", "Depolar başarıyla güncellendi!")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Depolar güncellenirken hata oluştu: {str(e)}")

class MainWindow(QMainWindow):
    def __init__(self):
        if not is_root():
            run_as_root()
            sys.exit(0)
        super().__init__()
        self.icon_manager = IconManager()
        self.setStyleSheet(STYLE)
        # Pencere boyutunu sabitle
        self.setFixedSize(700, 750)  # Genişlik: 800px, Yükseklik: 600px
        self.init_ui()
        self.packages = []  # Bulunan paketleri sakla
        # Search box'a event filter ekle
        self.search_input.installEventFilter(self)
        # self.package_list.itemClicked.connect(self.show_package_details)

    def init_ui(self):
        self.setWindowTitle("KutPAM")
        self.setWindowIcon(QIcon(ICON_PATH))

        
        # Ana widget ve layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        
        # Tab widget oluştur
        tab_widget = QTabWidget()
        
        # Ana işlemler tab'ı
        main_tab = QWidget()
        main_layout = QVBoxLayout()
        
        # Arama alanı ve filtre grubu
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Paket ara...")
        
        # Filtre ComboBox'ı ekle
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Tüm Paketler", "Kurulu Paketler", "Kurulu Olmayan Paketler"])
        self.filter_combo.currentTextChanged.connect(self.filter_packages)
        
        self.search_button = QPushButton("Ara")
        self.search_button.clicked.connect(self.search_packages)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.filter_combo)
        search_layout.addWidget(self.search_button)
        main_layout.addLayout(search_layout)
        
        # Paket listesi
        self.package_list = QListWidget()
        self.package_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.package_list.customContextMenuRequested.connect(self.show_context_menu)
        main_layout.addWidget(self.package_list)
        
        # Ana işlem butonları grubu
        operations_group = QGroupBox("Temel İşlemler")
        operations_layout = QHBoxLayout()
        
        self.install_button = QPushButton("Kur")
        self.remove_button = QPushButton("Kaldır")
        self.update_button = QPushButton("Güncelle")
        self.clean_button = QPushButton("Temizle")
        
        for btn in [self.install_button, self.remove_button, 
                   self.update_button, self.clean_button]:
            operations_layout.addWidget(btn)
        
        operations_group.setLayout(operations_layout)
        main_layout.addWidget(operations_group)
        
        # Sinyal bağlantıları
        self.install_button.clicked.connect(self.install_package)
        self.remove_button.clicked.connect(self.remove_package)
        self.update_button.clicked.connect(self.update_packages)
        self.clean_button.clicked.connect(self.clean_packages)
        
        main_tab.setLayout(main_layout)
        
        # Bakım işlemleri tab'ı
        maintenance_tab = QWidget()
        maintenance_layout = QVBoxLayout()
        
        # Sistem onarım grubu
        repair_group = QGroupBox("Sistem Onarım")
        repair_layout = QVBoxLayout()
        
        self.fix_broken_btn = QPushButton("Bozuk Paketleri Onar")
        self.fix_depends_btn = QPushButton("Bağımlılıkları Düzelt")
        self.fix_install_btn = QPushButton("Yarım Kalan Kurulumları Tamamla")
        self.flatpak_update_btn = QPushButton("Flatpak Paketlerini Güncelle")
        
        for btn in [self.fix_broken_btn, self.fix_depends_btn, 
                   self.fix_install_btn, self.flatpak_update_btn]:
            repair_layout.addWidget(btn)
        
        self.fix_broken_btn.clicked.connect(self.fix_broken_packages)
        self.fix_depends_btn.clicked.connect(self.fix_dependencies)
        self.fix_install_btn.clicked.connect(self.fix_interrupted_install)
        self.flatpak_update_btn.clicked.connect(self.update_flatpak)
        
        repair_group.setLayout(repair_layout)
        maintenance_layout.addWidget(repair_group)
        
        # Güncelleme kontrol grubu
        update_group = QGroupBox("Sistem Güncellemeleri")
        update_layout = QVBoxLayout()
        
        self.check_updates_btn = QPushButton("Güncellemeleri Kontrol Et")
        self.updates_list = QListWidget()
        self.update_all_btn = QPushButton("Tüm Güncellemeleri Yükle")
        
        update_layout.addWidget(self.check_updates_btn)
        update_layout.addWidget(self.updates_list)
        update_layout.addWidget(self.update_all_btn)
        
        self.check_updates_btn.clicked.connect(self.check_updates)
        self.update_all_btn.clicked.connect(self.update_all_packages)
        
        update_group.setLayout(update_layout)
        maintenance_layout.addWidget(update_group)
        
        maintenance_tab.setLayout(maintenance_layout)
        
        # Hakkında sekmesi
        about_tab = QWidget()
        about_layout = QVBoxLayout()
        
        about_html = """
        <div style="text-align: center; padding: 20px;">
            <img src='""" + LOGO_PATH + """' alt='KutPAM Logo' style='width: 100px; height: 100px;'>
            <h2 style="color: #2d8aaf;">KutPAM – Kut Package Manager</h2>
            <p style="color: #e0e0e0;">Mitolojiden Gücünü Alan Paket Yöneticisi</p>
            <p style="color: #e0e0e0;">Linux (APT) sistemlerinizi KutPAM ile yönetin! APT paketlerini yönetirken, Flatpak uygulamalarınızı otomatik güncelleyin—hepsi tek bir arayüzde! Göktürk kültüründen ilham alan tasarımıyla benzersiz bir deneyim sunar.</p>
            <h3 style="color: #2d8aaf;">Başlıca Özellikler:</h3>
            <ul style="color: #e0e0e0; text-align: left; display: inline-block;">
                <li>🔹 Göktürk Temalı Arayüz – Runik ikonlar ve TÜRK'ün sembolü Kurt Logo, koyu tema ve tarihi motiflerle şık ve özgün bir tasarım.</li>
                <li>🔹 DEB Paketi Kurulumu – DEB Paket Kurucu Dahili Aracı.</li>
                <li>🔹 APT Paket Yönetimi – Kurulum, kaldırma ve güncelleme işlemlerini tek tıkla yönetin.</li>
                <li>🔹 Flatpak Güncelleme Desteği – Flatpak uygulamalarınızı otomatik olarak güncel tutar.</li>
                <li>🔹 Akıllı Sistem Bakımı:
                    <ul>
                        <li>✔ Bozuk bağımlılıkları tespit edip onarır</li>
                        <li>✔ Güncellemeleri kolayca yönetin</li>
                        <li>✔ Depo ekleme/kaldırma için görsel araçlar</li>
                    </ul>
                </li>
                <li>🔹 Detaylı Paket Bilgileri – Boyut, sürüm geçmişi, geliştirici bilgileri ve daha fazlası.</li>
            </ul>
            <h3 style="color: #2d8aaf;">💡 Neden KutPAM?</h3>
            <ul style="color: #e0e0e0; text-align: left; display: inline-block;">
                <li>🚀 Tarih & Teknoloji Buluşuyor – Göktürk kültüründen esinlenen tasarım, işlevsellikle birleşiyor.</li>
                <li>💪 Güçlü ve Güvenilir – APT’nin sağlam altyapısını bir dokunuşla sunar.</li>
                <li>🛠 Kullanıcı Dostu – Terminal komutlarına veda edin, her şeyi görsel arayüzden yönetin!</li>
            </ul>
            <p style="color: #e0e0e0;">"KutPAM ile sisteminiz, Türk mitolojisindeki 'Kut' gibi güçlü ve düzenli olsun!" 🐺🔧</p>
            <br/>
            <p>Geliştirici: ALG Yazılım Inc.©</p>
            <p>www.algyazilim.com | info@algyazilim.com</p>
            <p>Fatih ÖNDER (CekToR) | fatih@algyazilim.com</p>
            <p>GitHub: https://github.com/cektor</p>
            <p>Sürüm: 1.0</p>
            <p>ALG Yazılım Pardus'a Göç'ü Destekler.</p>
            <p>Telif Hakkı © 2025 GNU</p>
        </div>
        """
        
        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setHtml(about_html)
        about_text.setStyleSheet("""
            QTextEdit {
                background-color: #2d2d2d;
                border: none;
            }
        """)
        about_text.setFont(QFont("Segoe UI Emoji", 10))
        about_layout.addWidget(about_text)
        about_tab.setLayout(about_layout)
        
        # Tab'ları ekle
        tab_widget.addTab(main_tab, "Paket İşlemleri")
        tab_widget.addTab(maintenance_tab, "Sistem Bakımı")
        
        # Depo yönetimi sekmesi
        repo_tab = RepoManagerDialog()
        tab_widget.addTab(repo_tab, "Depo Yönetimi")
        
        # Yeni DEB paketi sekmesi
        deb_tab = DebPackageTab()
        tab_widget.addTab(deb_tab, "DEB Paketi Kur")
        
        tab_widget.addTab(about_tab, "Hakkında")
        layout.addWidget(tab_widget)
        
        # İlerleme çubuğu
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Çıktı alanı
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        layout.addWidget(self.output_area)
        
        main_widget.setLayout(layout)

    def eventFilter(self, source, event):
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Return:
            if source is self.search_input:
                self.search_packages()
                return True
            elif source is self.flatpak_search:
                self.search_flatpak()
                return True
        return super().eventFilter(source, event)

    def search_packages(self):
        """Paket arama işlemini başlat"""
        term = self.search_input.text().strip()
        if not term:
            return
            
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.package_list.clear()
        self.search_thread = SearchThread(term)
        self.search_thread.progress.connect(self.update_progress)
        self.search_thread.finished.connect(self.on_search_complete)
        self.search_thread.error.connect(self.show_error)
        self.search_thread.start()

    def get_package_details(self, package_name):
        try:
            cmd = f"apt-cache show {package_name}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                details = {}
                for line in result.stdout.splitlines():
                    if line.startswith("Description-tr:") or line.startswith("Description-en:"):
                        details["description"] = line.split(":", 1)[1].strip()
                    elif line.startswith("Installed-Size:"):
                        size = int(line.split(":", 1)[1].strip())
                        if size < 1024:
                            details["size"] = f"{size} KB"
                        else:
                            details["size"] = f"{size/1024:.1f} MB"
                    elif line.startswith("Maintainer:"):
                        details["maintainer"] = line.split(":", 1)[1].strip()
                    elif line.startswith("Version:"):
                        details["version"] = line.split(":", 1)[1].strip()
                return details
            return None
        except:
            return None

    def show_results(self, packages):
        self.package_list.clear()
        for pkg in packages:
            details = self.get_package_details(pkg['name'])
            if details:
                item_text = (f"{pkg['name']}\n"
                            f"Açıklama: {details.get('description', 'Bilgi yok')}\n"
                            f"Boyut: {details.get('size', 'Bilgi yok')}\n"
                            f"Geliştirici: {details.get('maintainer', 'Bilgi yok')}")
                
                item = QListWidgetItem(item_text)
                if self.check_package_status(pkg['name']):
                    item.setData(Qt.UserRole, True)
                    item.setForeground(QColor("#50fa7b"))
                    item.setText(f"✓ {item_text}")
                self.package_list.addItem(item)

    def check_package_status(self, package_name):
        """Paketin kurulu olup olmadığını kontrol et"""
        try:
            cmd = ['dpkg', '-l', package_name]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return "[Kurulu]" if result.returncode == 0 else ""
        except:
            return ""

    def on_package_found(self, package):
        details = self.get_package_details(package["name"])
        if details:
            item_text = (f"{package['name']}\n"
                        f"Sürüm: {details.get('version', 'Bilgi yok')}\n"
                        f"Açıklama: {details.get('description', 'Bilgi yok')}\n"
                        f"Boyut: {details.get('size', 'Bilgi yok')}\n"
                        f"Geliştirici: {details.get('maintainer', 'Bilgi yok')}")
            
            item = QListWidgetItem(item_text)
            if package.get("installed"):
                item.setForeground(QColor("#50fa7b"))
                item.setText(f"✓ {item_text}")
            
            self.package_list.addItem(item)

    def show_error(self, message):
        QMessageBox.critical(self, "Hata", message)

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        if value % 10 == 0:  # Her %10'da bir güncelle
            QApplication.processEvents()

    def on_search_complete(self, packages):
        self.packages = packages  # Paketleri sakla
        self.filter_packages()   # Filtreye göre göster
        self.progress_bar.setVisible(False)

    def install_package(self):
        if not self.package_list.currentItem():
            return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        package_name = self.package_list.currentItem().text().split("\n")[0].split(" [")[0]
        try:
            cmd = ["sudo", "apt-get", "install", "-y", package_name]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                self.output_area.append(f"{package_name} başarıyla kuruldu")
                self.search_packages()  # Listeyi güncelle
            else:
                raise Exception(stderr.decode())
                
        except Exception as e:
            self.show_error(f"Kurulum hatası: {str(e)}")
        self.progress_bar.setVisible(False)

    def remove_package(self):
        if not self.package_list.currentItem():
            return
            
        # Paket ismini ayıkla
        package_text = self.package_list.currentItem().text()
        package_name = package_text.split('\n')[0]
        package_name = package_name.replace('✓ ', '')
        package_name = package_name.replace(' [Kurulu]', '')
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        try:
            self.output_area.append(f"{package_name} kaldırılıyor...")
            
            # Paket kontrolü
            check_cmd = ["dpkg", "-l", package_name]
            check_result = subprocess.run(check_cmd, capture_output=True, text=True)
            
            if check_result.returncode != 0:
                self.progress_bar.setVisible(False)
                raise Exception(f"Paket sistemde kurulu değil: {package_name}")
                
            # Paketi kaldır
            cmd = ["sudo", "apt-get", "remove", "-y", package_name]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                self.output_area.append(f"{package_name} başarıyla kaldırıldı!")
                self.search_packages()
            else:
                raise Exception(stderr)
                
        except Exception as e:
            self.show_error(f"Kaldırma hatası: {str(e)}")
        
        self.progress_bar.setVisible(False)

    def update_packages(self):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        try:
            self.output_area.append("Sistem güncelleniyor...")
            cmd = ["sudo", "apt-get", "update"]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                self.output_area.append("Sistem başarıyla güncellendi!")
            else:
                raise Exception(stderr.decode())
        except Exception as e:
            self.show_error(f"Güncelleme hatası: {str(e)}")
        self.progress_bar.setVisible(False)

    def clean_packages(self):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        try:
            self.output_area.append("Sistem temizleniyor...")
            cmd = ["sudo", "apt-get", "autoremove", "-y"]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                self.output_area.append("Sistem başarıyla temizlendi!")
            else:
                raise Exception(stderr.decode())
        except Exception as e:
            self.show_error(f"Temizleme hatası: {str(e)}")
        self.progress_bar.setVisible(False)

    def fix_broken_packages(self):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        try:
            self.output_area.append("Bozuk paketler onarılıyor...")
            commands = [
                ["sudo", "dpkg", "--configure", "-a"],
                ["sudo", "apt-get", "install", "-f", "-y"],
                ["sudo", "apt-get", "--fix-broken", "install", "-y"],
                ["sudo", "apt-get", "update"],
                ["sudo", "apt-get", "clean"],
                ["sudo", "apt-get", "autoclean"]
            ]
            
            for i, cmd in enumerate(commands):
                process = subprocess.run(cmd, capture_output=True, text=True)
                if process.returncode != 0:
                    raise Exception(process.stderr)
                progress = int(((i + 1) / len(commands)) * 100)
                self.progress_bar.setValue(progress)
                
            self.output_area.append("Sistem başarıyla onarıldı!")
            
        except Exception as e:
            self.show_error(f"Onarım hatası: {str(e)}")
        self.progress_bar.setVisible(False)

    def fix_dependencies(self):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        try:
            self.output_area.append("Bağımlılık sorunları gideriliyor...")
            commands = [
                ["sudo", "apt-get", "install", "--fix-missing", "-y"],
                ["sudo", "apt-get", "install", "-f", "-y"],
                ["sudo", "dpkg", "--configure", "-a"]
            ]
            
            for i, cmd in enumerate(commands):
                process = subprocess.run(cmd, capture_output=True, text=True)
                if process.returncode != 0:
                    raise Exception(process.stderr)
                progress = int(((i + 1) / len(commands)) * 100)
                self.progress_bar.setValue(progress)
                
            self.output_area.append("Bağımlılıklar düzeltildi!")
            
        except Exception as e:
            self.show_error(f"Bağımlılık düzeltme hatası: {str(e)}")
        self.progress_bar.setVisible(False)

    def fix_interrupted_install(self):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        try:
            self.output_area.append("Yarım kalan kurulumlar tamamlanıyor...")
            commands = [
                ["sudo", "dpkg", "--configure", "-a"],
                ["sudo", "apt-get", "install", "-f", "-y"],
                ["sudo", "apt-get", "update"],
                ["sudo", "apt-get", "upgrade", "-y"]
            ]
            
            for i, cmd in enumerate(commands):
                process = subprocess.run(cmd, capture_output=True, text=True)
                if process.returncode != 0:
                    raise Exception(process.stderr)
                progress = int(((i + 1) / len(commands)) * 100)
                self.progress_bar.setValue(progress)
                
            self.output_area.append("Yarım kalan kurulumlar tamamlandı!")
            
        except Exception as e:
            self.show_error(f"Kurulum tamamlama hatası: {str(e)}")
        self.progress_bar.setVisible(False)

    def check_updates(self):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.output_area.append("Güncellemeler kontrol ediliyor...")
        
        try:
            # Paket listesini güncelle
            subprocess.run(["sudo", "apt-get", "update"], check=True)
            
            # Güncellenebilir paketleri al
            result = subprocess.run(
                ["apt-get", "-s", "upgrade"],
                capture_output=True,
                text=True
            )
            
            updates = []
            for line in result.stdout.splitlines():
                if line.startswith("Inst"):
                    pkg = line.split()[1]
                    ver = line.split()[2].strip("[]")
                    updates.append(f"{pkg} -> {ver}")
            
            if updates:
                self.updates_list.clear()
                self.updates_list.setVisible(True)
                self.update_all_btn.setVisible(True)
                for update in updates:
                    self.updates_list.addItem(update)
                self.output_area.append(f"{len(updates)} adet güncelleme mevcut")
            else:
                self.output_area.append("Sistem güncel")
                
        except Exception as e:
            self.show_error(f"Güncelleme kontrolü hatası: {str(e)}")
            
        self.progress_bar.setVisible(False)

    def update_all_packages(self):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.output_area.append("Tüm güncellemeler yükleniyor...")
        
        try:
            process = subprocess.Popen(
                ["sudo", "apt-get", "upgrade", "-y"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.output_area.append(output.strip())
                    QApplication.processEvents()
                    
            if process.returncode == 0:
                self.output_area.append("Tüm güncellemeler başarıyla yüklendi!")
                self.updates_list.clear()
                self.updates_list.setVisible(False)
                self.update_all_btn.setVisible(False)
            else:
                raise Exception(process.stderr.read())
                
        except Exception as e:
            self.show_error(f"Güncelleme hatası: {str(e)}")
            
        self.progress_bar.setVisible(False)

    def list_installed_packages(self):
        try:
            cmd = "apt list --installed"
            process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = process.communicate()
            
            if error:
                raise Exception(error.decode())
                
            packages = output.decode().split('\n')
            self.packages_list.clear()  # Listeyi temizle
            
            for package in packages:
                if package.strip():  # Boş satırları atla
                    # Paket adını '/' karakterinden önce al
                    package_name = package.split('/')[0]
                    item = QListWidgetItem(package_name)
                    # Koyu yeşil renk uygula (RGB: 0,100,0)
                    item.setForeground(QBrush(QColor(0, 100, 0)))
                    self.packages_list.addItem(item)
                    
        except Exception as e:
            self.show_error(f"Paket listesi alınamadı: {str(e)}")

    def filter_packages(self):
        if not self.packages:  # Eğer paket listesi boşsa
            return
            
        filter_type = self.filter_combo.currentText()
        self.package_list.clear()
        
        for pkg in self.packages:
            is_installed = self.check_package_status(pkg['name'])
            should_show = False
            
            if filter_type == "Tüm Paketler":
                should_show = True
            elif filter_type == "Kurulu Paketler":
                should_show = is_installed
            elif filter_type == "Kurulu Olmayan Paketler":
                should_show = not is_installed
                
            if should_show:
                item = QListWidgetItem(f"{pkg['name']}\n{pkg['description']}")
                if is_installed:
                    item.setData(Qt.UserRole, True)
                    item.setForeground(QColor("#50fa7b"))
                    item.setText(f"✓ {pkg['name']} [Kurulu]\n{pkg['description']}")
                self.package_list.addItem(item)

    def run_command(self, cmd, timeout=60):
        try:
            process = subprocess.run(cmd, 
                                   capture_output=True,
                                   text=True,
                                   timeout=timeout)
            return process
        except subprocess.TimeoutExpired:
            if hasattr(self, 'process'):
                self.process.terminate()
            self.show_error("İşlem zaman aşımına uğradı!")
            return None

    def check_apt_lock(self):
        lock_file = "/var/lib/dpkg/lock-frontend"
        if os.path.exists(lock_file):
            self.show_error("Başka bir paket yöneticisi çalışıyor!")
            return False
        return True

    def clear_cache(self):
        if hasattr(self, 'packages'):
            self.packages.clear()
        if hasattr(self, 'package_list'):
            self.package_list.clear()
        import gc
        gc.collect()

    def show_package_details(self, item):
        package_name = item.text().split('\n')[0].replace('✓ ', '').split(' [')[0]
        dialog = PackageDetailsDialog(package_name, self)
        dialog.exec_()

    def show_context_menu(self, position):
        item = self.package_list.itemAt(position)
        if item:
            menu = QMenu(self)
            menu.setStyleSheet("""
                QMenu {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 1px solid #2d8aaf;
                    padding: 5px;
                }
                QMenu::item {
                    padding: 5px 20px;
                }
                QMenu::item:selected {
                    background-color: #2d8aaf;
                }
            """)
            
            details_action = menu.addAction("Paket Detayları")
            action = menu.exec_(self.package_list.mapToGlobal(position))
            
            if action == details_action:
                package_name = item.text().split('\n')[0].replace('✓ ', '').split(' [')[0]
                dialog = PackageDetailsDialog(package_name, self)
                dialog.exec_()

    def update_flatpak(self):
        if not self.check_flatpak_installed():
            QMessageBox.warning(self, "Flatpak Yüklü Değil", 
                                "Flatpak sistemde yüklü değil. Lütfen yüklemek için şu bağlantıyı ziyaret edin: https://flatpak.org/setup/")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.output_area.append("Flatpak paketleri güncelleniyor...")

        try:
            process = subprocess.Popen(
                ["flatpak", "update", "-y"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.output_area.append(output.strip())
                    QApplication.processEvents()

            if process.returncode == 0:
                self.output_area.append("Flatpak paketleri başarıyla güncellendi!")
            else:
                raise Exception(process.stderr.read())

        except Exception as e:
            self.show_error(f"Güncelleme hatası: {str(e)}")

        self.progress_bar.setVisible(False)

    def check_flatpak_installed(self):
        """Flatpak'in sistemde yüklü olup olmadığını kontrol eder"""
        try:
            result = subprocess.run(["flatpak", "--version"], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def search_flatpak(self):
        term = self.flatpak_search.text().strip()
        if term:
            self.flatpak_list.clear()
            packages = self.flatpak_manager.search_packages(term)
            
            for pkg in packages:
                item_text = f"{pkg['name']}\nID: {pkg['id']}"
                if pkg['version']: 
                    item_text += f"\nSürüm: {pkg['version']}"
                if pkg['description']:
                    item_text += f"\nAçıklama: {pkg['description']}"
                    
                item = QListWidgetItem(item_text)
                self.flatpak_list.addItem(item)

    def install_flatpak(self):
        if not self.flatpak_list.currentItem():
            return
            
        try:
            if not self.check_flatpak_installed():
                self.show_error("Flatpak yüklü değil!")
                return
                
            lines = self.flatpak_list.currentItem().text().split('\n')
            package_id = None
            
            for line in lines:
                if line.startswith('ID:'):
                    package_id = line.replace('ID:', '').strip().split()[0]
                    break
            
            if package_id:
                result = self.flatpak_manager.install_package(package_id)
                if result and result.returncode == 0:
                    self.output_area.append(f"Flatpak paketi başarıyla kuruldu: {package_id}")
                    self.search_flatpak()  # Listeyi güncelle
                else:
                    self.show_error(f"Kurulum hatası: {result.stderr if result else 'Bilinmeyen hata'}")
            else:
                self.show_error("Geçerli bir paket ID'si bulunamadı")
        except Exception as e:
            self.show_error(f"Kurulum işlemi sırasında hata: {str(e)}")

    def remove_flatpak(self):
        if self.flatpak_list.currentItem():
            try:
                lines = self.flatpak_list.currentItem().text().split('\n')
                package_id = None
                
                for line in lines:
                    if line.startswith('ID:'):
                        package_id = line.replace('ID:', '').strip()
                        break
                
                if package_id:
                    result = self.flatpak_manager.remove_package(package_id)
                    if result and result.returncode == 0:
                        self.output_area.append(f"Flatpak paketi başarıyla kaldırıldı: {package_id}")
                        self.search_flatpak()  # Listeyi güncelle
                    else:
                        error_msg = result.stderr if result else "Paket kaldırılamadı"
                        self.show_error(f"Kaldırma hatası: {error_msg}")
                else:
                    self.show_error("Geçerli bir paket ID'si bulunamadı")
            except Exception as e:
                self.show_error(f"Kaldırma işlemi sırasında hata: {str(e)}")

    def show_flatpak_context_menu(self, position):
        item = self.flatpak_list.itemAt(position)
        if item:
            menu = QMenu(self)
            menu.setStyleSheet("""
                QMenu {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    border: 1px solid #2d8aaf;
                }
                QMenu::item:selected {
                    background-color: #2d8aaf;
                }
            """)
            details_action = menu.addAction("Paket Detayları")
            action = menu.exec_(self.flatpak_list.mapToGlobal(position))
            
            if action == details_action:
                # ID'yi doğru şekilde al
                lines = item.text().split('\n')
                for line in lines:
                    if line.startswith('ID:'):
                        package_id = line.replace('ID:', '').strip()
                        break
                dialog = FlatpakDetailsDialog(package_id, self)
                dialog.exec_()

    def open_repo_manager(self):
        dialog = RepoManagerDialog(self)
        dialog.exec_()

class DebInstallDialog(QDialog):
    def __init__(self, deb_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Paket Detayları")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout()
        
        # Paket bilgileri alanı
        info_group = QGroupBox("Paket Bilgileri")
        info_layout = QFormLayout()
        
        self.name_label = QLabel()
        self.version_label = QLabel()
        self.maintainer_label = QLabel()
        self.website_label = QLabel()
        self.size_label = QLabel()
        
        info_layout.addRow("Paket Adı:", self.name_label)
        info_layout.addRow("Versiyon:", self.version_label)
        info_layout.addRow("Geliştirici:", self.maintainer_label)
        info_layout.addRow("Web Sitesi:", self.website_label)
        info_layout.addRow("Boyut:", self.size_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Bağımlılıklar alanı
        deps_group = QGroupBox("Bağımlılıklar")
        deps_layout = QVBoxLayout()
        self.deps_list = QListWidget()
        deps_layout.addWidget(self.deps_list)
        deps_group.setLayout(deps_layout)
        layout.addWidget(deps_group)
        
        # Butonlar
        button_layout = QHBoxLayout()
        install_btn = QPushButton("Kur")
        cancel_btn = QPushButton("İptal")
        
        install_btn.clicked.connect(self.install_package)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(install_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.deb_path = deb_path
        self.load_package_info()
        
    def load_package_info(self):
        try:
            cmd = ["dpkg", "-I", self.deb_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                info = result.stdout.split('\n')
                
                for line in info:
                    if "Package:" in line:
                        self.name_label.setText(line.split("Package:")[1].strip())
                    elif "Version:" in line:
                        self.version_label.setText(line.split("Version:")[1].strip())
                    elif "Maintainer:" in line:
                        self.maintainer_label.setText(line.split("Maintainer:")[1].strip())
                    elif "Homepage:" in line:
                        url = line.split("Homepage:")[1].strip()
                        self.website_label.setText(f'<a href="{url}">{url}</a>')
                        self.website_label.setOpenExternalLinks(True)
                    elif "Installed-Size:" in line:
                        size = int(line.split("Installed-Size:")[1].strip())
                        self.size_label.setText(f"{size/1024:.1f} MB")
                    elif "Depends:" in line:
                        deps = line.split("Depends:")[1].strip().split(", ")
                        self.deps_list.clear()
                        self.deps_list.addItems(deps)
                        
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Paket bilgileri okunamadı: {str(e)}")
            
    def install_package(self):
        try:
            cmd = ["sudo", "dpkg", "-i", self.deb_path]
            process = subprocess.run(cmd, capture_output=True, text=True)
            
            if process.returncode != 0:
                # Bağımlılık hatası varsa apt-get install -f çalıştır
                fix_cmd = ["sudo", "apt-get", "install", "-f", "-y"]
                fix_process = subprocess.run(fix_cmd, capture_output=True, text=True)
                
                if fix_process.returncode == 0:
                    QMessageBox.information(self, "Başarılı", "Paket başarıyla kuruldu!")
                    self.accept()
                else:
                    raise Exception(fix_process.stderr)
            else:
                QMessageBox.information(self, "Başarılı", "Paket başarıyla kuruldu!")
                self.accept()
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kurulum hatası: {str(e)}")

class DebPackageTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        
        # Dosya seçme alanı
        file_group = QGroupBox("DEB Paketi Seç")
        file_layout = QHBoxLayout()
        
        self.file_path = QLineEdit()
        self.file_path.setPlaceholderText("Dosya seçin veya sürükleyip bırakın...")
        self.file_path.setReadOnly(True)
        
        browse_btn = QPushButton("Gözat")
        browse_btn.clicked.connect(self.browse_file)
        
        file_layout.addWidget(self.file_path)
        file_layout.addWidget(browse_btn)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Sürükle-bırak alanı
        drop_group = QGroupBox("veya Buraya Sürükleyip Bırakın")
        drop_layout = QVBoxLayout()
        
        self.drop_label = QLabel("DEB dosyasını bu alana sürükleyip bırakın")
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #2d8aaf;
                border-radius: 8px;
                padding: 40px;
                color: #888;
            }
        """)
        
        drop_layout.addWidget(self.drop_label)
        drop_group.setLayout(drop_layout)
        layout.addWidget(drop_group)
        
        self.setLayout(layout)
        
        # Sürükle-bırak desteği
        self.setAcceptDrops(True)
        
    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "DEB Paketi Seç",
            "",
            "DEB Paketleri (*.deb)"
        )
        if file_path:
            self.process_deb_file(file_path)
            
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and event.mimeData().urls()[0].path().endswith('.deb'):
            event.acceptProposedAction()
            self.drop_label.setStyleSheet("""
                QLabel {
                    border: 2px dashed #50fa7b;
                    border-radius: 8px;
                    padding: 40px;
                    color: #50fa7b;
                    background: rgba(80, 250, 123, 0.1);
                }
            """)
            
    def dragLeaveEvent(self, event):
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #2d8aaf;
                border-radius: 8px;
                padding: 40px;
                color: #888;
            }
        """)
        
    def dropEvent(self, event):
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #2d8aaf;
                border-radius: 8px;
                padding: 40px;
                color: #888;
            }
        """)
        file_path = event.mimeData().urls()[0].toLocalFile()
        self.process_deb_file(file_path)
        
    def process_deb_file(self, file_path):
        self.file_path.setText(file_path)
        dialog = DebInstallDialog(file_path, self)
        dialog.exec_()

if __name__ == "__main__":
    if not is_root():
        run_as_root()
    else:
        # GUI için gerekli ortam değişkenlerini ayarla
        if 'XDG_RUNTIME_DIR' not in os.environ:
            os.environ['XDG_RUNTIME_DIR'] = '/run/user/{}'.format(os.getuid())
        
        app = QApplication(sys.argv)
        if ICON_PATH:
            app.setWindowIcon(QIcon(ICON_PATH))
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
