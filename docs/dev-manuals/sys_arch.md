# Architektura Systemu [PL]
## Stack technologiczny
Cały backend aplikacji wykonany jest w języku **python** w wersji 3.10

####  ORM, Requesty, Render HTML
- framework **Django** w wersji 4.0
#### API
- **Django REST** framework w wersji 3.13
#### Frontend
##### HTML + CSS
- Frontend aplikacji wyświetlany będzie w przeglądarkach, zatem używamy języka HTML oraz CSS do wyświetlania i formatowania strony,
##### JavaScript
- język Javascript z frameworkiem **Vue 3** służy do dynamicznego pobierania oraz wysyłania żądań na serwer bez konieczności przeładowywania strony,
- Framework Vue osadzony jest bezpośrednio w kodzie html po stronie serwera, i nie wymaga
swojej własnej obsługi żądzań.
##### CSS Framework
- **Bootstrap** w wersji 5.1 służy do uproszczenia responsywności, oraz zminiejszenia ilości potrzebnego CSS-a
#### Baza Danych
##### Dewelopment
- W środowisku deweloperskim używamy bazy danych **sqlite** z językiem SQL.
##### Produkcja
- W środowisku produkcyjnym używamy bazy **PostgreSQL**, dostarczonej przez serwis hostingowy SaaS Heroku.com
- Baza jest podłączona do aplikacji biblioteką **psycopg2**
#### Algorytm
- Algorytm generujący grafiki został oparty o bibliotekę do języka Python **Google OR-tools** w wersji 9.3, pomagającą rozwiązać problem przydziału pracowników do miejsc pracy.


## Środowisko produkcyjne
- Całość aplikacji jest wdrożona poprzez serwis hostingowy SaaS **Heroku.com**, która używa **Ubuntu 20.04** jako serwera aplikacji
- Serwerem http jest **gunicorn** w wersji 20.1

## Środowisko deweloperskie
- Istnieje możliwość developmentu na systemach Windows i Linux
## Użytkownik końcowy
- Użytkownik będzie korzystał z aplikacji poprzez przeglądarkę internetową


