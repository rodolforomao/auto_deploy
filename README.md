
pip install -r requirements.txt

python -m pip install pyinstaller

# Gerar executavel
python -m PyInstaller --onefile --name git_pull_remote main.py
