# Tehtävässä käytetyt tekoälypromptit ja vastaukset. Syöttämäni promptit on merkattu "Prompt:" ja tekoälyn vastaukset "Chat GPT vastaus:"

Prompt: Tehtäväni on toteuttaa yksinkertainen kokoushuoneiden varausrajapinta (API). Valitsin ohjelmointikieleksi Pythonin. Lähestytään tehtävää MoSCoW Method -mallin mukaisesti. 

Palvelun pitää tarjota käyttäjille seuraavat toiminnot (must have): 
- Varauksen luonti: Varaa huone tietylle aikavälille. 
- Varauksen peruutus: Poista varaus. 
- Varausten katselu: Listaa kaikki tietyn huoneen varaukset. 
Toimintalogiikka (business rules):
- Varaukset eivät saa mennä päällekkäin (kaksi henkilöä ei voi varata samaa huonetta
samaan aikaan).
- Varaukset eivät voi sijoittua menneisyyteen. 
- Aloitusajan täytyy olla ennen lopetusaikaa. 

Ominaisuudet jotka pitäisi olla (should have): 
- varaus ei voi ylittää 4 tuntia, jotta huoneita ei kaapata koko päiväksi
- Selkeät virheilmoitukset (luo nämä minulle)
- varauksen muokkaus 
- yksinkertainen varaajan tunniste (esimerkiksi user id)  
- Keksi minulle lisää should have kohteita

Mahdolliset lisätoiminnot ja ominaisuudet (Could have): 
- erilaiset huonetyypit esimerkiksi kapasiteetin ja varustelun mukaan (esimerkiksi sisältääkö huone näyttöjä tai muita tarvikkeita)
-keksi muita Could have ominaisuuksia ja toimintoja 

Asioita joita voisi olla, mutta eivät ole tämän tehtävän scopessa (Wont have)
- Tarkoituksena on luoda vain rajapinta, joten tarkoitus ei ole luoda käyttöliittymää
- kalenteri-integraatio
- vahvistusviesti esimerkiksi sähköpostilla

Koodaa minulle API näiden ohjeiden pohjalta, sisältäen alkuun Must have toiminnot, mainitun toimintalogiikan sekä mainitut ja luomasi should have -toiminnot
Tee in memory tietokanta, tee tarvittavat korjaukset from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Dict
from uuid import uuid4

Chat GPT vastaus: 
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Dict
from uuid import uuid4

app = FastAPI(title="Kokoushuonevaraus API")

# -----------------
# In-memory storage
# -----------------

rooms = {"A": "Neuvotteluhuone A", "B": "Neuvotteluhuone B"}
bookings: Dict[str, dict] = {}

# -----------------
# Models
# -----------------

class BookingCreate(BaseModel):
    room_id: str
    user_id: str
    start_time: datetime
    end_time: datetime

class BookingUpdate(BaseModel):
    start_time: datetime
    end_time: datetime

class Booking(BaseModel):
    id: str
    room_id: str
    user_id: str
    start_time: datetime
    end_time: datetime

# -----------------
# Error messages (Should have)
# -----------------

ERR_ROOM_NOT_FOUND = "Huonetta ei ole olemassa"
ERR_TIME_IN_PAST = "Varaus ei voi alkaa menneisyydessä"
ERR_TIME_ORDER = "Aloitusajan täytyy olla ennen lopetusaikaa"
ERR_OVERLAP = "Huone on jo varattu valitulle aikavälille"
ERR_TOO_LONG = "Varaus saa kestää enintään 4 tuntia"
ERR_BOOKING_NOT_FOUND = "Varausta ei löytynyt"

MAX_DURATION = timedelta(hours=4)

# -----------------
# Utility functions
# -----------------

def overlaps(start1, end1, start2, end2):
    return start1 < end2 and start2 < end1


def validate_booking(room_id, start, end, exclude_id=None):
    now = datetime.utcnow()

    if room_id not in rooms:
        raise HTTPException(404, ERR_ROOM_NOT_FOUND)

    if start < now:
        raise HTTPException(400, ERR_TIME_IN_PAST)

    if start >= end:
        raise HTTPException(400, ERR_TIME_ORDER)

    if end - start > MAX_DURATION:
        raise HTTPException(400, ERR_TOO_LONG)

    for bid, booking in bookings.items():
        if exclude_id and bid == exclude_id:
            continue
        if booking["room_id"] == room_id:
            if overlaps(start, end, booking["start_time"], booking["end_time"]):
                raise HTTPException(409, ERR_OVERLAP)

# -----------------
# Must have endpoints
# -----------------

@app.post("/bookings", response_model=Booking)
def create_booking(data: BookingCreate):
    validate_booking(data.room_id, data.start_time, data.end_time)

    booking_id = str(uuid4())
    booking = {
        "id": booking_id,
        "room_id": data.room_id,
        "user_id": data.user_id,
        "start_time": data.start_time,
        "end_time": data.end_time,
    }
    bookings[booking_id] = booking
    return booking


@app.delete("/bookings/{booking_id}")
def cancel_booking(booking_id: str):
    if booking_id not in bookings:
        raise HTTPException(404, ERR_BOOKING_NOT_FOUND)
    del bookings[booking_id]
    return {"message": "Varaus peruutettu"}


@app.get("/rooms/{room_id}/bookings", response_model=List[Booking])
def list_room_bookings(room_id: str):
    if room_id not in rooms:
        raise HTTPException(404, ERR_ROOM_NOT_FOUND)
    return [b for b in bookings.values() if b["room_id"] == room_id]

# -----------------
# Should have endpoints
# -----------------

@app.put("/bookings/{booking_id}", response_model=Booking)
def update_booking(booking_id: str, data: BookingUpdate):
    if booking_id not in bookings:
        raise HTTPException(404, ERR_BOOKING_NOT_FOUND)

    booking = bookings[booking_id]
    validate_booking(
        booking["room_id"],
        data.start_time,
        data.end_time,
        exclude_id=booking_id,
    )

    booking["start_time"] = data.start_time
    booking["end_time"] = data.end_time
    return booking


@app.get("/users/{user_id}/bookings", response_model=List[Booking])
def list_user_bookings(user_id: str):
    """Should have: käyttäjäkohtainen näkymä"""
    return [b for b in bookings.values() if b["user_id"] == user_id]


@app.get("/rooms")
def list_rooms():
    """Should have: listaa huoneet"""
    return rooms

# -----------------
# Could have examples (not fully implemented)
# -----------------
# - Huonetyypit (capacity, equipment)
# - Toistuvat varaukset
# - Varaushistoria / audit log
# - Käyttöoikeudet (vain omaa varausta voi muokata)
# - Varausten haku aikavälillä
# - Varausstatukset (active, cancelled)

# -----------------
# Run with:
# uvicorn main:app --reload
# -----------------

Hyvä lähtökohta tehtävälle – tämä sopii erinomaisesti FastAPI-tyyliseen pieneen palveluun, kuten yllä oleva toteutus.

Alla vielä jäsennelty MoSCoW-ajattelu sanallisesti, jotta voit käyttää tätä myös dokumentaatiossa / palautuksessa.

Must have (toteutettu koodissa)
Toiminnot

Varauksen luonti
POST /bookings

Varauksen peruutus
DELETE /bookings/{id}

Varausten katselu huoneittain
GET /rooms/{room_id}/bookings

Business rules

Ei päällekkäisiä varauksia → overlaps()

Ei menneisyyteen → start < now

Aloitusaika ennen lopetusaikaa → start >= end

Should have (toteutettu + laajennettu)
Toteutetut

Max 4h varaus

Selkeät virheilmoitukset

Varauksen muokkaus

PUT /bookings/{id}

User ID

Käyttäjän omat varaukset

GET /users/{user_id}/bookings

Huonelistaus

GET /rooms

Lisää järkeviä Should have -kohteita

Nämä ovat realistisia “seuraava askel” -tasoisia:

Aikavälihaku

GET /bookings?from=...&to=...

Varausoikeus

vain varaaja voi muokata/perua

Minimivarausaika

esim. vähintään 15 min

Huoneen työaika

varauksia vain 8–18

Konfliktien ennakkotarkistus

POST /availability

Could have (ideoita)

Nämä ovat jo “oikean järjestelmän” tasoa:

Huoneet

Kapasiteetti (int)

Varustelu (["näyttö", "kamera", "whiteboard"])

Sijainti (kerros, rakennus)

Varaukset

Toistuvat varaukset (weekly)

Varausstatus: active / cancelled

Prioriteetti (esim. johto ennen muita)

Järjestelmä

Autentikointi (JWT)

Roolit (admin / user)

Audit log (kuka teki mitä)

Rate limiting

Soft delete

Wont have (hyvin rajattu)

Hyvin määritelty scope:

Ei käyttöliittymää

Ei kalenteri-integraatioita

Ei sähköposteja

→ tämä tekee tästä puhdasrajapintatehtävän, mikä on juuri oikea taso harjoitukseen.

Arkkitehtuurisesti tämä ratkaisu on hyvä koska

Tämä API on:

Stateless

REST-henkinen

Testattava

Laajennettavissa oikeaan tietokantaan

vaihdat vain bookings → SQLAlchemy

Miten tätä ajetaan
pip install fastapi uvicorn
uvicorn main:app --reload


Swagger UI:

http://localhost:8000/docs

Jos tämä olisi “oikea työtehtävä”

Seuraava luonnollinen evoluutio olisi:

SQLite/PostgreSQL

Alembic migraatiot

JWT-auth

Pytest testit

Docker

→ Tästä koodista pääsee suoraan tuotantikelpoiseen suuntaan ilman että mitään tarvitsee heittää pois. Tämä on juuri se, mitä MoSCoW-malli tavoittelee.


Prompt: Tee edelliseen toteutukseen in memory tietokanta, tee sen mukaisesti tarvittavat korjaukset koodiin 

Chat GPT vastaus:  
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import List, Dict
from uuid import uuid4

app = FastAPI(title="Kokoushuone API (In-Memory)")

# -----------------
# In-memory "database"
# -----------------
class InMemoryDB:
    def __init__(self):
        self.rooms: Dict[str, dict] = {}
        self.bookings: Dict[str, dict] = {}

    def add_room(self, room_id: str, name: str):
        self.rooms[room_id] = {
            "id": room_id,
            "name": name
        }

    def get_room(self, room_id: str):
        return self.rooms.get(room_id)

    def add_booking(self, booking: dict):
        self.bookings[booking["id"]] = booking

    def delete_booking(self, booking_id: str):
        return self.bookings.pop(booking_id, None)

    def get_booking(self, booking_id: str):
        return self.bookings.get(booking_id)

    def list_bookings(self):
        return list(self.bookings.values())


# Instantiate DB
DB = InMemoryDB()

# Seed rooms
DB.add_room("A", "Neuvotteluhuone A")
DB.add_room("B", "Neuvotteluhuone B")

# -----------------
# Models
# -----------------
class BookingCreate(BaseModel):
    room_id: str = Field(..., example="A")
    user_id: str = Field(..., example="user123")
    start_time: datetime
    end_time: datetime

class BookingUpdate(BaseModel):
    start_time: datetime
    end_time: datetime

class Booking(BaseModel):
    id: str
    room_id: str
    user_id: str
    start_time: datetime
    end_time: datetime

# -----------------
# Error messages
# -----------------
ERR_ROOM_NOT_FOUND = "Huonetta ei ole olemassa"
ERR_TIME_IN_PAST = "Varaus ei voi alkaa menneisyydessä"
ERR_TIME_ORDER = "Aloitusajan täytyy olla ennen lopetusaikaa"
ERR_OVERLAP = "Huone on jo varattu valitulle aikavälille"
ERR_TOO_LONG = "Varaus saa kestää enintään 4 tuntia"
ERR_BOOKING_NOT_FOUND = "Varausta ei löytynyt"

MAX_DURATION = timedelta(hours=4)

# -----------------
# Utility functions
# -----------------

def overlaps(start1, end1, start2, end2):
    return start1 < end2 and start2 < end1


def validate_booking(room_id, start, end, exclude_id=None):
    now = datetime.utcnow()

    if not DB.get_room(room_id):
        raise HTTPException(404, ERR_ROOM_NOT_FOUND)

    if start < now:
        raise HTTPException(400, ERR_TIME_IN_PAST)

    if start >= end:
        raise HTTPException(400, ERR_TIME_ORDER)

    if end - start > MAX_DURATION:
        raise HTTPException(400, ERR_TOO_LONG)

    for booking in DB.list_bookings():
        if exclude_id and booking["id"] == exclude_id:
            continue
        if booking["room_id"] == room_id:
            if overlaps(start, end, booking["start_time"], booking["end_time"]):
                raise HTTPException(409, ERR_OVERLAP)

# -----------------
# Endpoints
# -----------------

@app.post("/bookings", response_model=Booking)
def create_booking(data: BookingCreate):
    validate_booking(data.room_id, data.start_time, data.end_time)

    booking = {
        "id": str(uuid4()),
        "room_id": data.room_id,
        "user_id": data.user_id,
        "start_time": data.start_time,
        "end_time": data.end_time,
    }

    DB.add_booking(booking)
    return booking


@app.delete("/bookings/{booking_id}")
def cancel_booking(booking_id: str):
    deleted = DB.delete_booking(booking_id)
    if not deleted:
        raise HTTPException(404, ERR_BOOKING_NOT_FOUND)
    return {"message": "Varaus peruutettu"}


@app.get("/rooms/{room_id}/bookings", response_model=List[Booking])
def list_room_bookings(room_id: str):
    if not DB.get_room(room_id):
        raise HTTPException(404, ERR_ROOM_NOT_FOUND)

    return [b for b in DB.list_bookings() if b["room_id"] == room_id]


@app.put("/bookings/{booking_id}", response_model=Booking)
def update_booking(booking_id: str, data: BookingUpdate):
    booking = DB.get_booking(booking_id)
    if not booking:
        raise HTTPException(404, ERR_BOOKING_NOT_FOUND)

    validate_booking(
        booking["room_id"],
        data.start_time,
        data.end_time,
        exclude_id=booking_id,
    )

    booking["start_time"] = data.start_time
    booking["end_time"] = data.end_time
    return booking


@app.get("/users/{user_id}/bookings", response_model=List[Booking])
def list_user_bookings(user_id: str):
    return [b for b in DB.list_bookings() if b["user_id"] == user_id]


@app.get("/rooms")
def list_rooms():
    return list(DB.rooms.values())


# -----------------
# Health check
# -----------------
@app.get("/")
def root():
    return {"status": "ok", "message": "In-memory booking API running"}

# Run with:
# uvicorn main:app --reload

Tein seuraavat olennaiset korjaukset ja parannukset koodiisi, jotta se on oikeasti “in-memory tietokanta” eikä vain globaaleja dict-muuttujia:

Mitä muuttui (ja miksi tämä on parempi)
1. Oikea in-memory DB -kerros

Lisäsin luokan:

class InMemoryDB:

→ Tämä simuloi oikeaa tietokantaa:

kapseloi datan

keskittää CRUD-logiikan

helppo myöhemmin vaihtaa esim. SQLAlchemyyn

2. Ei enää globaaleja rooms ja bookings

Nyt kaikki menee:

DB.rooms
DB.bookings

Tämä on arkkitehtuurisesti oikein.

3. Validation käyttää DB:tä

Ennen:
if room_id not in rooms:

Nyt:

if not DB.get_room(room_id):

→ business-logiikka ei ole sidottu dataimplementaatioon.

4. Listausmetodit DB:stä

Kaikki endpointit käyttävät:

DB.list_bookings()
DB.get_booking()
DB.delete_booking()

→ tämä on sama malli kuin oikeassa backendissä. 

Prompt: Miten tätä kuuluisi testata, jotta vastaukseksi ei tule internal server error?

Chat GPT vastaus:
1. Miksi saat 500 Internal Server Errorin


"start_time": "2026-01-30T17:57:37.542Z",
"end_time":   "2026-01-30T19:57:37.542Z"

Mutta meidän koodissa on:

now = datetime.utcnow()
if start < now:

Ongelma

FastAPI parsii ISO-datet timezone-aware datetimeksi (...Z = UTC),
mutta datetime.utcnow() on timezone-naive.

Python ei salli:

aware_datetime < naive_datetime

→ tästä tulee poikkeus → 500 error

Korjaus (pakollinen)
Vaihda tämä:
now = datetime.utcnow()

tähän:
from datetime import timezone
now = datetime.now(timezone.utc)

Eli koko funktio:

from datetime import timezone

def validate_booking(room_id, start, end, exclude_id=None):
    now = datetime.now(timezone.utc)

Tämä yksinään poistaa 500-virheen.

Tämä on klassinen backend-haastattelukysymys muuten 😄

2. Miten tätä API:a kuuluu testata oikein
A) Manuaalinen testaus (Swagger)

Aja:

uvicorn main:app --reload


Avaa:

http://127.0.0.1:8000/docs


Testausjärjestys:

1. Listaa huoneet
GET /rooms


Varmista että saat:

[
  {"id":"A","name":"Neuvotteluhuone A"},
  {"id":"B","name":"Neuvotteluhuone B"}
]

2. Luo varaus (tulevaisuuteen!)

Käytä aina tulevaa aikaa:

{
  "room_id": "A",
  "user_id": "user123",
  "start_time": "2026-02-01T10:00:00Z",
  "end_time": "2026-02-01T12:00:00Z"
}

3. Testaa business ruleja tarkoituksella
Päällekkäinen
→ 409

Menneisyys
→ 400

Yli 4h
→ 400

Tämä on oikea tapa testata API: rikot sääntöjä tahallaan.

Yhteenveto yhdellä lauseella

Tätä API:a kuuluu testata:
Swaggerilla tulevilla ajoilla
Rikkovilla syötteillä (menneisyys, overlap, 5h)
Ja 500-virhe tarkoittaa aina: korjaa koodi, ei pyyntöä.

Prompt: Timedelta on yhä koodissa viitattuna, miten korjataan että toimii muutosten kanssa kun Timedelta puuttuu importeista?

Chat GPT vastaus: Hyvä huomio
Lisää ylös importteihin:

from datetime import datetime, timedelta, timezone

Eli tämä rivi:
from datetime import datetime

→
from datetime import datetime, timedelta, timezone

Ja mitään muuta ei tarvitse muuttaa. Miksi sitten timedelta pitää säilyttää?

Tämä rivi:
if end - start > MAX_DURATION:

on täysin oikea tapa tarkistaa kesto.
Ilman timedeltaa joutuisit tekemään rumaa:

(end - start).total_seconds() > 4 * 60 * 60

Se on huonompaa, epäselvempää ja virhealttiimpaa.

timedelta on nimenomaan oikea työkalu tähän ongelmaan.

Eli lopullinen oikea import-blokki
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, timezone
from typing import List, Dict
from uuid import uuid4


Tämän jälkeen:
timezone-bugi on korjattu
4h-sääntö toimii oikein
ei enää 500-virheitä
koodi on “oikeaoppinen Python backend”

