![Tests](https://github.com/SaluSL/planimbly/actions/workflows/tests.yml/badge.svg)

# Dokumentacja
- [quick start (PL)](README.md)
- [dokumentacja architektury (PL)](docs/dev-manuals/sys_arch.md)
- [strategia branchowania (ENG)](docs/dev-manuals/source_control.md)
- [testowanie (ENG)](docs/dev-manuals/testing.md)
- [struktura projektu (ENG)](docs/dev-manuals/proj_tree.md)

# Konfiguracja projektu pod Dockerem

1. Pobierz dockera
    - dla systemu Windows: https://docs.docker.com/desktop/install/windows-install/
    - dla systemu Linux: https://docs.docker.com/engine/install/
2. Klonujemy repozytorium za pomocą komendy: 
```console
$ git clone https://github.com/planimbly/planimbly.git
```
3. Pobieramy plik z discorda (#docker) .env i umieszczamy go w utworzonym folderze **planimbly**
4. Otwieramy konsolę w folderze **planimbly**
5. Budujemy kontenery za pomocą komendy:
```console
$ docker compose up --build
```
6. Dodajemy przykładowe dane do bazy za pomocą komend:
```console
$ docker cp ./localfile.sql containername:/container/path/file.sql
$ docker exec -u postgresuser containername psql dbname postgresuser -f /container/path/file.sql
```
W praktyce komendy mogą wyglądać tak:
```console
$ docker ps
```
```
CONTAINER ID   IMAGE           COMMAND                  CREATED         STATUS                   PORTS                    NAMES
bed21bdfd933   planimbly-web   "sh -c 'python manag…"   4 minutes ago   Up 3 minutes             0.0.0.0:8000->8000/tcp   planimbly-web-1
1d225fe762d9   postgres:15     "docker-entrypoint.s…"   4 minutes ago   Up 4 minutes (healthy)   5432/tcp                 planimbly-db-1
```
```console
$ docker cp ./dev_test_data.sql planimbly-db-1:/docker-entrypoint-initdb.d/data.sql
$ docker exec -u postgres planimbly-db-1 psql postgres postgres -f docker-entrypoint-initdb.d/data.sql
```
Dane zostały dodane do naszej bazy deweloperskiej.
Możemy sprawdzić zawartość tabel za pomocą komendy:
```console
$ docker exec -it planimbly-db-1 psql -U postgres -c "SELECT * FROM organizations_unit;"
```
7. za każdym razem startujemy kontenery komendą:
```console
$ docker compose up
```
wcześniej zapisane przez nas dane nie zostaną usunięte.

8. w każdej chwili możemy usunąć nasze kontenery oraz volumes poprzez komendę:
```console
$ docker compose down
```
**UWAGA!** Po usunięciu kontenerów tracimy wszystkie zapisy bazy danych i trzeba powtórzyć wcześniejszy proces począwszy od kroku 1.



# Konfiguracja projektu pod systemem Windows i Linux:

1. Klonujemy repozytorium za pomocą komendy: 
```
git clone https://github.com/planimbly/planimbly.git
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

# Konfiguracja Huey:

1. Instalujemy pakiet redis, huey (jest w reqiurements.txt)
2. Instalujemy redisa oraz wsl z tego linku https://redis.io/docs/getting-started/installation/install-redis-on-windows/
3. Włączamy serwer Redis na tym samym porcie
4. Za każdym razem jak włączamy serwer, w innym terminalu wpisujemy:

```
python manage.py run_huey
```

w tym terminalu są logi z wykonywania algorytmu