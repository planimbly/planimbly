![Tests](https://github.com/SaluSL/planimbly/actions/workflows/tests.yml/badge.svg)

# Dokumentacja
- [quick start (PL)](README.md)
- [dokumentacja architektury (PL)](docs/dev-manuals/sys_arch.md)
- [strategia branchowania (ENG)](docs/dev-manuals/source_control.md)
- [testowanie (ENG)](docs/dev-manuals/testing.md)
- [struktura projektu (ENG)](docs/dev-manuals/proj_tree.md)

# Konfiguracja projektu pod systemem Windows i Linux:

1. Klonujemy repozytorium za pomocą komendy: 
```
git clone https://github.com/SaluSL/planimbly.git
```
2. Pobieramy plik z discorda .env oraz db.sqlite3 i umieszczamy je w utworzonym folderze **planimbly**
3. Otwieramy konsolę w folderze **planimbly**
4. Tworzymy środowisko wirtualne:
```
python -m venv venv
```
5. Przechodzimy do folderu **scripts** (Windows)
```
cd venv/Scripts
```
6a. Aktywujemy środowsko w konsoli (Windows)
```
activate.bat
```
6b. Aktywujemy środowsko w konsoli (Linux)
```
source ./venv/bin/activate
```
7. Wychodzimy do **planimbly** (Windows)
```
cd ../../
```
8. Instalujemy wymagane biblioteki
```
python -m pip install -r requirements.txt
python -m pip install -r requirements_dev.txt
```


### Uwaga, jeżeli instalujecie jakikolwiek pakiet, musicie dodać go do requirements.txt poprzez komendę: python -m pip freeze > requirements.txt

