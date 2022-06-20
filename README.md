![Tests](https://github.com/SaluSL/planimbly/actions/workflows/tests.yml/badge.svg)

# Konfiguracja projektu pod systemem Windows:

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
5. Przechodzimy do folderu **scripts**
```
cd venv/Scripts
```
6. Aktywujemy środowsko w konsoli
```
activate.bat
```
7. Wychodzimy do **planimbly**
```
cd ../../
```
8. Instalujemy wymagane biblioteki
```
python -m pip install -r requirements.txt
python -m pip install -r requirements_dev.txt
```


### Uwaga, jeżeli instalujecie jakikolwiek pakiet, musicie dodać go do requirements.txt poprzez komendę: python -m pip freeze > requirements.txt

