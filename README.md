<a href="#">
    <img src="https://raw.githubusercontent.com/pedromxavier/flag-badges/main/badges/TR.svg" alt="made in TR">
</a>

# KutPAM – PAckage Manager

The Modern Package Manager Drawing Power from Mythology

Manage your Linux systems with KutPAM! While managing APT packages, automatically update your Flatpak applications—all in a single interface! It offers a unique experience with its design inspired by Göktürk culture.

In Turkish mythology, the wolf is a symbol of strength, origin, and leadership for the Turkish nation. The wolf logo used in KutPAM represents this deep historical and cultural heritage and symbolizes the power to manage your system.

Key Features: 

🔹 Göktürk-Themed Interface – A stylish and unique design with runic icons, dark themes, and historical motifs.

🔹 APT Package Management – Easily manage installation, removal, and updates with a single click.

🔹 Flatpak Update Support – Keeps your Flatpak applications automatically updated.

🔹 Smart System Maintenance: 

✔ Detects and repairs broken dependencies

✔ Easily manage updates

✔ Visual tools for adding/removing repositories

🔹 Detailed Package Information – Size, version history, developer details, and more.

🔹 Easy .deb Package Installation –

✔ Install .deb packages easily by dragging and dropping, or

✔ Select the file to install .deb packages.

💡 Why KutPAM? 

🚀 History & Technology Meet – A design inspired by Göktürk culture combined with modern functionality.

💪 Powerful and Reliable – Offers the solid infrastructure of APT with a modern touch.

🛠 User-Friendly – Say goodbye to terminal commands, manage everything from a visual interface!

📦 Fast Installation – Install .deb packages with drag-and-drop or file selection.

"With KutPAM, your system will be as powerful and organized as 'Kut' in Turkish mythology!" 🐺🔧


<h1 align="center">KutPAM Logo</h1>

<p align="center">
  <img src="kutpamlo.png" alt="KutPAM Logo" width="150" height="150">
</p>


----------------------

# Linux Screenshot
![Linux(pardus)](screenshot/linux_kutpam.gif)  

--------------------
Install Git Clone and Python3

Github Package Must Be Installed On Your Device.

git
```bash
sudo apt install git -y
```

Python3
```bash
sudo apt install python3 -y 

```

pip
```bash
sudo apt install python3-pip

```

# Required Libraries

Required Libraries for Debian/Ubuntu
```bash
sudo apt-get install python3-pyqt5
sudo apt-get install qttools5-dev-tools
sudo apt install network-manager
sudo apt install systemd
```


PyQt5
```bash
pip install PyQt5
```
PyQt5-sip
```bash
pip install PyQt5 PyQt5-sip
```

PyQt5-tools
```bash
pip install PyQt5-tools
```

Pillow
```bash
pip install Pillow
```

requests
```bash
pip install requests
```
----------------------------------


# Installation
Install KutPAM

```bash
sudo git clone https://github.com/cektor/KutPAM.git
```
```bash
cd KutPAM
```

```bash
sudo python3 kutpam.py

```

# To compile

NOTE: For Compilation Process pyinstaller must be installed. To Install If Not Installed.

pip install pyinstaller 

Linux Terminal 
```bash
pytohn3 -m pyinstaller --onefile --windowed kutpam.py
```

# To install directly on Linux

Linux (based debian) Terminal: Linux (debian based distributions) To install directly from Terminal.
```bash
wget -O Setup_Linux64.deb https://github.com/cektor/KutPAM/releases/download/1.00/Setup_Linux64.deb && sudo apt install ./Setup_Linux64.deb && sudo apt-get install -f -y
```


Release Page: https://github.com/cektor/KutPAM/releases/tag/1.00

----------------------------------
