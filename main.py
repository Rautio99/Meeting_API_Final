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
