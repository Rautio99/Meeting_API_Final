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
