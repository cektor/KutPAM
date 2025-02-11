from setuptools import setup, find_packages

setup(
    name="kutpam",  
    version="1.0",  
    description="KutPAM is a powerful and user-friendly package manager for Linux. It manages APT packages easily while keeping Flatpak applications up to date. Inspired by Gokturk culture, it combines modern functionality with a unique design.", 
    author="Fatih Önder", 
    author_email="fatih@algyazilim.com",  
    url="https://github.com/cektor/KutPAM", 
    packages=find_packages(), 
    install_requires=[
        'PyQt5',  # PyQt5 kütüphanesi doğru yazılmış
        'requests',  # requests kütüphanesi doğru yazılmış
        'pillow',  # Pillow doğru yazılmış
    ],
    package_data={
        'kutpam': ['*.png', '*.desktop'],  # Paket içinde taşınacak dosyalar (ikonlar ve .desktop dosyası)
    },
    data_files=[
        ('share/applications', ['kutpam.desktop']),  
        ('share/icons/hicolor/48x48/apps', ['kutpamlo.png']),  # Dosya adını kutpamlo.png olarak belirttim, doğru dosya adı olmalı
    ],
    entry_points={
        'gui_scripts': [
            'kutpam=kutpam:main',  # Ana fonksiyonun doğru şekilde ayarlandığından emin olun
        ]
    },
)

