"""Local seed dataset for FanFest — ~10 rows per entity.

The evt-001 / user_00x IDs mirror what the existing services expect so the
demo app stays consistent while services are progressively migrated to use
these typed entities.

The special event_001 ID (underscore format) is kept for FEST-03 live match
state demo compatibility (live.js hardcodes EVENT_ID = 'event_001').

Import from here in tests instead of hand-rolling inline dicts.
"""
from datetime import datetime, timezone

from app.models.entities import (
    Comment,
    Event,
    Fan,
    Goal,
    Match,
    Photo,
    Prediction,
    Recap,
    RecapSlide,
    Registration,
)

_utc = timezone.utc

# ── Events ────────────────────────────────────────────────────────────────────

EVENTS: list[Event] = [
    Event(
        id="evt-001",
        home_team="Argentina",
        home_flag="\U0001f1e6\U0001f1f7",
        away_team="Brasil",
        away_flag="\U0001f1e7\U0001f1f7",
        venue_name="La Bombonera",
        venue_address="Brandsen 805, Buenos Aires",
        organizer="FanFest HQ",
        kickoff_iso="2030-01-01T18:00:00Z",
        match_start_time=datetime(2030, 1, 1, 18, 0, tzinfo=_utc),
        invite_link="http://localhost:8000/api/v1/events/evt-001/invite",
        calendar_link=(
            "https://calendar.google.com/calendar/render"
            "?action=TEMPLATE&text=Argentina+vs+Brasil"
            "&dates=20300101T180000Z/20300101T200000Z"
            "&location=Brandsen+805%2C+Buenos+Aires"
        ),
        maps_link="https://www.google.com/maps/dir/?api=1&destination=Brandsen+805%2C+Buenos+Aires",
        status="future",
        competition="FIFA World Cup 2026 · Semifinal",
        venue_distance="2.5km · La Boca",
        amenities=[["🍺", "Cervezas"], ["🎵", "Música"], ["📺", "Pantalla"], ["🍔", "Foodtruck"]],
    ),
    Event(
        id="evt-002",
        home_team="Belgrano",
        home_flag="🔵",
        away_team="River Plate",
        away_flag="🔴",
        venue_name="Estadio Mario Alberto Kempes",
        venue_address="Calle Crisol S/N, Córdoba",
        organizer="FanFest HQ",
        kickoff_iso="2026-06-15T21:00:00Z",
        match_start_time=datetime(2026, 6, 15, 21, 0, tzinfo=_utc),
        invite_link="http://localhost:8000/api/v1/events/evt-002/invite",
        calendar_link=(
            "https://calendar.google.com/calendar/render"
            "?action=TEMPLATE&text=Belgrano+vs+River+Plate"
            "&dates=20260615T210000Z/20260615T230000Z"
            "&location=Calle+Crisol+S%2FN%2C+C%C3%B3rdoba"
        ),
        maps_link="https://www.google.com/maps/dir/?api=1&destination=Calle+Crisol+S%2FN%2C+C%C3%B3rdoba",
        status="past",
        recap_event_id="evt-002",
        competition="Torneo Apertura 2026 · Final",
        venue_distance="5.0km · Alberdi",
        amenities=[["🍺", "Cervezas"], ["📺", "Pantalla gigante"], ["🔵", "Barra Belgrano"], ["🎵", "Música"]],
    ),
    Event(
        id="evt-003",
        home_team="Francia",
        home_flag="\U0001f1eb\U0001f1f7",
        away_team="Portugal",
        away_flag="\U0001f1f5\U0001f1f9",
        venue_name="Roof Lounge",
        venue_address="Thames 1800, Buenos Aires",
        organizer="FanFest HQ",
        kickoff_iso="2026-06-26T18:00:00Z",
        match_start_time=datetime(2026, 6, 26, 18, 0, tzinfo=_utc),
        invite_link="http://localhost:8000/api/v1/events/evt-003/invite",
        calendar_link=(
            "https://calendar.google.com/calendar/render"
            "?action=TEMPLATE&text=Francia+vs+Portugal"
            "&dates=20260626T180000Z/20260626T200000Z"
            "&location=Thames+1800%2C+Buenos+Aires"
        ),
        maps_link="https://www.google.com/maps/dir/?api=1&destination=Thames+1800%2C+Buenos+Aires",
        status="live",
        competition="FIFA World Cup 2026 · Cuartos de Final",
        venue_distance="800m · Soho",
        amenities=[["🍷", "Vinos"], ["📺", "Pantalla"], ["🎵", "Música en vivo"]],
    ),
    Event(
        id="evt-004",
        home_team="Argentina",
        home_flag="\U0001f1e6\U0001f1f7",
        away_team="México",
        away_flag="\U0001f1f2\U0001f1fd",
        venue_name="La Mona Sports Bar",
        venue_address="Güemes 456, Córdoba",
        organizer="FanFest HQ",
        kickoff_iso="2026-06-24T21:00:00Z",
        match_start_time=datetime(2026, 6, 24, 21, 0, tzinfo=_utc),
        invite_link="http://localhost:8000/api/v1/events/evt-004/invite",
        calendar_link=(
            "https://calendar.google.com/calendar/render"
            "?action=TEMPLATE&text=Argentina+vs+M%C3%A9xico"
            "&dates=20260624T210000Z/20260624T230000Z"
            "&location=G%C3%BCemes+456%2C+C%C3%B3rdoba"
        ),
        maps_link="https://www.google.com/maps/dir/?api=1&destination=G%C3%BCemes+456%2C+C%C3%B3rdoba",
        status="past",
        recap_event_id="evt-004",
        competition="FIFA World Cup 2026 · Grupo C · Jornada 2",
        venue_distance="400m · Güemes",
        amenities=[["🍔", "Foodtruck"], ["🐾", "Pet-friendly"], ["📺", "Pantalla"], ["🍺", "Cervezas"], ["🎵", "Música en vivo"]],
    ),
    Event(
        id="evt-005",
        home_team="Uruguay",
        home_flag="\U0001f1fa\U0001f1fe",
        away_team="Colombia",
        away_flag="\U0001f1e8\U0001f1f4",
        venue_name="Café del Sur",
        venue_address="San Martín 890, Rosario",
        organizer="FanFest HQ",
        kickoff_iso="2026-06-27T18:00:00Z",
        match_start_time=datetime(2026, 6, 27, 18, 0, tzinfo=_utc),
        invite_link="http://localhost:8000/api/v1/events/evt-005/invite",
        calendar_link=(
            "https://calendar.google.com/calendar/render"
            "?action=TEMPLATE&text=Uruguay+vs+Colombia"
            "&dates=20260627T180000Z/20260627T200000Z"
            "&location=San+Mart%C3%ADn+890%2C+Rosario"
        ),
        maps_link="https://www.google.com/maps/dir/?api=1&destination=San+Mart%C3%ADn+890%2C+Rosario",
        status="future",
        competition="FIFA World Cup 2026 · Grupo F · Jornada 3",
        venue_distance="1.5km · Pichincha",
        amenities=[["🍺", "Cervezas"], ["📺", "Pantalla"], ["🍔", "Foodtruck"]],
    ),
    Event(
        id="evt-006",
        home_team="Inglaterra",
        home_flag="\U0001f3f4\U000e0067\U000e0062\U000e0065\U000e006e\U000e0067\U000e007f",
        away_team="Italia",
        away_flag="\U0001f1ee\U0001f1f9",
        venue_name="The English Pub",
        venue_address="Reconquista 456, Buenos Aires",
        organizer="FanFest HQ",
        kickoff_iso="2026-06-28T20:00:00Z",
        match_start_time=datetime(2026, 6, 28, 20, 0, tzinfo=_utc),
        invite_link="http://localhost:8000/api/v1/events/evt-006/invite",
        calendar_link=(
            "https://calendar.google.com/calendar/render"
            "?action=TEMPLATE&text=Inglaterra+vs+Italia"
            "&dates=20260628T200000Z/20260628T220000Z"
            "&location=Reconquista+456%2C+Buenos+Aires"
        ),
        maps_link="https://www.google.com/maps/dir/?api=1&destination=Reconquista+456%2C+Buenos+Aires",
        status="past",
        recap_event_id="evt-006",
        competition="FIFA World Cup 2026 · Grupo D · Jornada 2",
        venue_distance="900m · Microcentro",
        amenities=[["🍺", "Cervezas"], ["📺", "Pantalla"], ["🎵", "Música"]],
    ),
    Event(
        id="evt-007",
        home_team="Países Bajos",
        home_flag="\U0001f1f3\U0001f1f1",
        away_team="Bélgica",
        away_flag="\U0001f1e7\U0001f1ea",
        venue_name="Amsterdam Bar",
        venue_address="Pellegrini 123, Rosario",
        organizer="FanFest HQ",
        kickoff_iso="2026-06-29T18:00:00Z",
        match_start_time=datetime(2026, 6, 29, 18, 0, tzinfo=_utc),
        invite_link="http://localhost:8000/api/v1/events/evt-007/invite",
        calendar_link=(
            "https://calendar.google.com/calendar/render"
            "?action=TEMPLATE&text=Pa%C3%ADses+Bajos+vs+B%C3%A9lgica"
            "&dates=20260629T180000Z/20260629T200000Z"
            "&location=Pellegrini+123%2C+Rosario"
        ),
        maps_link="https://www.google.com/maps/dir/?api=1&destination=Pellegrini+123%2C+Rosario",
        status="future",
        competition="FIFA World Cup 2026 · Grupo E · Jornada 1",
        venue_distance="600m · República",
        amenities=[["🍺", "Cervezas"], ["🎶", "DJ"], ["📺", "Pantalla"]],
    ),
    Event(
        id="evt-008",
        home_team="Japón",
        home_flag="\U0001f1ef\U0001f1f5",
        away_team="Corea del Sur",
        away_flag="\U0001f1f0\U0001f1f7",
        venue_name="Sushi & Sport",
        venue_address="Corrientes 2345, Buenos Aires",
        organizer="FanFest HQ",
        kickoff_iso="2026-06-30T13:00:00Z",
        match_start_time=datetime(2026, 6, 30, 13, 0, tzinfo=_utc),
        invite_link="http://localhost:8000/api/v1/events/evt-008/invite",
        calendar_link=(
            "https://calendar.google.com/calendar/render"
            "?action=TEMPLATE&text=Jap%C3%B3n+vs+Corea+del+Sur"
            "&dates=20260630T130000Z/20260630T150000Z"
            "&location=Corrientes+2345%2C+Buenos+Aires"
        ),
        maps_link="https://www.google.com/maps/dir/?api=1&destination=Corrientes+2345%2C+Buenos+Aires",
        status="live",
        competition="FIFA World Cup 2026 · Grupo H · Jornada 3",
        venue_distance="2.0km · Abasto",
        amenities=[["🍜", "Ramen"], ["📺", "Pantalla"], ["🍺", "Cervezas"]],
    ),
    Event(
        id="evt-009",
        home_team="Marruecos",
        home_flag="\U0001f1f2\U0001f1e6",
        away_team="Senegal",
        away_flag="\U0001f1f8\U0001f1f3",
        venue_name="Café Atlas",
        venue_address="Güemes 789, Córdoba",
        organizer="FanFest HQ",
        kickoff_iso="2026-07-01T16:00:00Z",
        match_start_time=datetime(2026, 7, 1, 16, 0, tzinfo=_utc),
        invite_link="http://localhost:8000/api/v1/events/evt-009/invite",
        calendar_link=(
            "https://calendar.google.com/calendar/render"
            "?action=TEMPLATE&text=Marruecos+vs+Senegal"
            "&dates=20260701T160000Z/20260701T180000Z"
            "&location=G%C3%BCemes+789%2C+C%C3%B3rdoba"
        ),
        maps_link="https://www.google.com/maps/dir/?api=1&destination=G%C3%BCemes+789%2C+C%C3%B3rdoba",
        status="future",
        competition="FIFA World Cup 2026 · Grupo G · Jornada 2",
        venue_distance="1.8km · Alberdi",
        amenities=[["☕", "Café"], ["📺", "Pantalla"], ["🍔", "Foodtruck"]],
    ),
    Event(
        id="evt-010",
        home_team="Brasil",
        home_flag="\U0001f1e7\U0001f1f7",
        away_team="Argentina",
        away_flag="\U0001f1e6\U0001f1f7",
        venue_name="Maracanã Fan Bar",
        venue_address="Pueyrredón 1111, Buenos Aires",
        organizer="FanFest HQ",
        kickoff_iso="2026-07-04T20:00:00Z",
        match_start_time=datetime(2026, 7, 4, 20, 0, tzinfo=_utc),
        invite_link="http://localhost:8000/api/v1/events/evt-010/invite",
        calendar_link=(
            "https://calendar.google.com/calendar/render"
            "?action=TEMPLATE&text=Brasil+vs+Argentina"
            "&dates=20260704T200000Z/20260704T220000Z"
            "&location=Pueyrred%C3%B3n+1111%2C+Buenos+Aires"
        ),
        maps_link="https://www.google.com/maps/dir/?api=1&destination=Pueyrred%C3%B3n+1111%2C+Buenos+Aires",
        status="future",
        competition="FIFA World Cup 2026 · Grupo A · Jornada 3",
        venue_distance="3.2km · Recoleta",
        amenities=[["🍺", "Cervezas"], ["🎵", "Samba en vivo"], ["📺", "Pantalla"], ["🍔", "Churrasco"]],
    ),
]

# ── Fans ──────────────────────────────────────────────────────────────────────
# user_001 / user_002 / user_003 mirror registry._checked_in so a future
# refactor can drop registry.py entirely and read from here.

FANS: list[Fan] = [
    Fan(user_id="user_001", name="Alice",    location="Buenos Aires, AR"),
    Fan(user_id="user_002", name="Bob",      location="Córdoba, AR"),
    Fan(user_id="user_003", name="Carlos",   location="Rosario, AR"),
    Fan(user_id="user_004", name="Diana",    location="Mendoza, AR"),
    Fan(user_id="user_005", name="Elena",    location="Salta, AR"),
    Fan(user_id="user_006", name="Fernando", location="Tucumán, AR"),
    Fan(user_id="user_007", name="Gabriela", location="Mar del Plata, AR"),
    Fan(user_id="user_008", name="Hernán",   location="La Plata, AR"),
    Fan(user_id="user_009", name="Iván",     location="Santa Fe, AR"),
    Fan(user_id="user_010", name="Julia",    location="Bariloche, AR"),
]

# ── Registrations ─────────────────────────────────────────────────────────────

REGISTRATIONS: list[Registration] = [
    Registration("user_001", "evt-001", datetime(2029, 12, 10, 10, 0, tzinfo=_utc), checked_in=True,  checked_in_at=datetime(2030, 1, 1, 17, 45, tzinfo=_utc)),
    Registration("user_002", "evt-001", datetime(2029, 12, 11, 14, 0, tzinfo=_utc), checked_in=True,  checked_in_at=datetime(2030, 1, 1, 17, 50, tzinfo=_utc)),
    Registration("user_003", "evt-001", datetime(2029, 12, 12,  9, 0, tzinfo=_utc), checked_in=False),
    Registration("user_004", "evt-001", datetime(2029, 12, 13, 11, 0, tzinfo=_utc), checked_in=False),
    Registration("user_005", "evt-001", datetime(2029, 12, 14, 15, 0, tzinfo=_utc), checked_in=True,  checked_in_at=datetime(2030, 1, 1, 18, 5,  tzinfo=_utc)),
    Registration("user_006", "evt-001", datetime(2029, 12, 15,  8, 0, tzinfo=_utc), checked_in=False),
    Registration("user_007", "evt-001", datetime(2029, 12, 16, 12, 0, tzinfo=_utc), checked_in=False),
    Registration("user_001", "evt-002", datetime(2026, 6,  5, 10, 0, tzinfo=_utc),  checked_in=True,  checked_in_at=datetime(2026, 6, 15, 20, 45, tzinfo=_utc)),
    Registration("user_002", "evt-003", datetime(2026, 6, 11, 14, 0, tzinfo=_utc),  checked_in=True,  checked_in_at=datetime(2026, 6, 26, 17, 55, tzinfo=_utc)),
    Registration("user_003", "evt-004", datetime(2026, 6, 12,  9, 0, tzinfo=_utc),  checked_in=True,  checked_in_at=datetime(2026, 6, 24, 20, 50, tzinfo=_utc)),
    Registration("user_004", "evt-002", datetime(2026, 6,  8, 11, 0, tzinfo=_utc),  checked_in=False),
    Registration("user_005", "evt-003", datetime(2026, 6, 14, 15, 0, tzinfo=_utc),  checked_in=True,  checked_in_at=datetime(2026, 6, 26, 17, 40, tzinfo=_utc)),
    Registration("user_007", "evt-002", datetime(2026, 6,  5, 12, 0, tzinfo=_utc),  checked_in=True,  checked_in_at=datetime(2026, 6, 15, 20, 55, tzinfo=_utc)),
    Registration("user_008", "evt-005", datetime(2026, 6, 17,  9, 0, tzinfo=_utc),  checked_in=False),
    Registration("user_009", "evt-002", datetime(2026, 6,  6, 16, 0, tzinfo=_utc),  checked_in=True,  checked_in_at=datetime(2026, 6, 15, 20, 50, tzinfo=_utc)),
]

# ── Matches ───────────────────────────────────────────────────────────────────
# event_001 (underscore) is the FEST-03 live match demo; live.js hardcodes
# EVENT_ID = 'event_001' so this ID must stay as-is.

MATCHES: list[Match] = [
    Match(
        event_id="event_001",
        home_team="River Plate",
        away_team="Boca Juniors",
        venue="Estadio Monumental",
        home_score=0, away_score=0, status="pre", clock_seconds=0,
    ),
    Match(
        event_id="evt-001",
        home_team="Argentina", away_team="Brasil",
        venue="La Bombonera",
        home_score=0, away_score=0, status="pre", clock_seconds=0,
    ),
    Match(
        event_id="evt-002",
        home_team="Belgrano", away_team="River Plate",
        venue="Estadio Mario Alberto Kempes",
        home_score=3, away_score=2, status="ended", clock_seconds=5700,
        goals=[
            Goal(player="Facundo Colidio",  team="River Plate", minute=17),
            Goal(player="Leonardo Morales", team="Belgrano",    minute=25),
            Goal(player="Tomás Galván",     team="River Plate", minute=55),
            Goal(player="Uvita Fernández",  team="Belgrano",    minute=82),
            Goal(player="Uvita Fernández",  team="Belgrano",    minute=90),
        ],
    ),
    Match(
        event_id="evt-003",
        home_team="Francia", away_team="Portugal",
        venue="Roof Lounge",
        home_score=1, away_score=0, status="live", clock_seconds=3600,
        goals=[Goal(player="Mbappé", team="Francia", minute=39)],
    ),
    Match(
        event_id="evt-004",
        home_team="Argentina", away_team="México",
        venue="La Mona Sports Bar",
        home_score=2, away_score=1, status="ended", clock_seconds=5400,
        goals=[
            Goal(player="Messi",   team="Argentina", minute=22),
            Goal(player="Lozano",  team="México",    minute=55),
            Goal(player="Di María", team="Argentina", minute=78),
        ],
    ),
    Match(
        event_id="evt-005",
        home_team="Uruguay", away_team="Colombia",
        venue="Café del Sur",
        home_score=0, away_score=0, status="pre", clock_seconds=0,
    ),
    Match(
        event_id="evt-006",
        home_team="Inglaterra", away_team="Italia",
        venue="The English Pub",
        home_score=3, away_score=2, status="ended", clock_seconds=5400,
        goals=[
            Goal(player="Kane",      team="Inglaterra", minute=20),
            Goal(player="Bellingham",team="Inglaterra", minute=35),
            Goal(player="Immobile",  team="Italia",     minute=50),
            Goal(player="Saka",      team="Inglaterra", minute=65),
            Goal(player="Verratti",  team="Italia",     minute=80),
        ],
    ),
    Match(
        event_id="evt-007",
        home_team="Países Bajos", away_team="Bélgica",
        venue="Amsterdam Bar",
        home_score=0, away_score=0, status="pre", clock_seconds=0,
    ),
    Match(
        event_id="evt-008",
        home_team="Japón", away_team="Corea del Sur",
        venue="Sushi & Sport",
        home_score=0, away_score=0, status="live", clock_seconds=1800,
    ),
    Match(
        event_id="evt-009",
        home_team="Marruecos", away_team="Senegal",
        venue="Café Atlas",
        home_score=0, away_score=0, status="pre", clock_seconds=0,
    ),
    Match(
        event_id="evt-010",
        home_team="Brasil", away_team="Argentina",
        venue="Maracanã Fan Bar",
        home_score=0, away_score=0, status="pre", clock_seconds=0,
    ),
]

# ── Predictions ───────────────────────────────────────────────────────────────

_pred_base = datetime(2029, 12, 31, 20, 0, tzinfo=_utc)

PREDICTIONS: list[Prediction] = [
    Prediction("user_001", "evt-001", home_score=3, away_score=1, submitted_at=_pred_base),
    Prediction("user_002", "evt-001", home_score=2, away_score=0, submitted_at=_pred_base),
    Prediction("user_003", "evt-001", home_score=1, away_score=1, submitted_at=_pred_base),
    Prediction("user_004", "evt-001", home_score=2, away_score=1, submitted_at=_pred_base),
    Prediction("user_005", "evt-001", home_score=1, away_score=0, submitted_at=_pred_base),
    Prediction("user_006", "evt-001", home_score=3, away_score=2, submitted_at=_pred_base),
    Prediction("user_007", "evt-002", home_score=2, away_score=1, submitted_at=datetime(2026, 6, 20, 10, 0, tzinfo=_utc)),
    Prediction("user_008", "evt-003", home_score=1, away_score=0, submitted_at=datetime(2026, 6, 21, 11, 0, tzinfo=_utc)),
    Prediction("user_001", "evt-002", home_score=1, away_score=0, submitted_at=datetime(2026, 6, 20, 12, 0, tzinfo=_utc)),
    Prediction("user_002", "evt-003", home_score=2, away_score=1, submitted_at=datetime(2026, 6, 21, 14, 0, tzinfo=_utc)),
    Prediction("user_009", "evt-001", home_score=4, away_score=0, submitted_at=_pred_base),
    Prediction("user_010", "evt-001", home_score=2, away_score=2, submitted_at=_pred_base),
]

# ── Photos ────────────────────────────────────────────────────────────────────

_photo_t = datetime(2030, 1, 1, 18, 30, tzinfo=_utc)

PHOTOS: list[Photo] = [
    Photo("photo-001", "evt-001", "https://picsum.photos/400/300?random=1",  "user_001", "Alice",    uploaded_at=_photo_t),
    Photo("photo-002", "evt-001", "https://picsum.photos/400/300?random=2",  "user_002", "Bob",      uploaded_at=datetime(2030, 1, 1, 18, 45, tzinfo=_utc)),
    Photo("photo-003", "evt-001", "https://picsum.photos/400/300?random=3",  "user_005", "Elena",    uploaded_at=datetime(2030, 1, 1, 19,  0, tzinfo=_utc)),
    Photo("photo-004", "evt-001", "https://picsum.photos/400/300?random=4",  "user_001", "Alice",    uploaded_at=datetime(2030, 1, 1, 19, 10, tzinfo=_utc)),
    Photo("photo-005", "evt-001", "https://picsum.photos/400/300?random=5",  "user_002", "Bob",      uploaded_at=datetime(2030, 1, 1, 19, 20, tzinfo=_utc)),
    Photo("photo-006", "evt-001", "https://picsum.photos/400/300?random=6",  "user_005", "Elena",    uploaded_at=datetime(2030, 1, 1, 19, 35, tzinfo=_utc)),
    Photo("photo-007", "evt-001", "https://picsum.photos/400/300?random=7",  "user_001", "Alice",    uploaded_at=datetime(2030, 1, 1, 19, 50, tzinfo=_utc)),
    Photo("photo-008", "evt-002", "http://localhost:8000/media/evt-002/belgrano1.jpg",                                        "user_007", "Gabriela", uploaded_at=datetime(2026, 6, 15, 21, 30, tzinfo=_utc), uploader_handle="@gaby_celeste",  caption="La previa en el Kempes. Una noche para la historia 🔵", likes_count=41),
    Photo("photo-009", "evt-002", "http://localhost:8000/media/evt-002/balgrano2.jpeg",                                       "user_009", "Iván",     uploaded_at=datetime(2026, 6, 15, 21, 50, tzinfo=_utc), uploader_handle="@ivan_bel",      caption="El banco de Belgrano, atentos al partido 💪", likes_count=18),
    Photo("photo-016", "evt-002", "http://localhost:8000/media/evt-002/belgrano3.jpeg",                                       "user_001", "Alice",    uploaded_at=datetime(2026, 6, 15, 22, 10, tzinfo=_utc), uploader_handle="@alice_fan",     caption="Celebración celeste en el Kempes. ¡Campeones! 🏆🔵", likes_count=93),
    Photo("photo-017", "evt-002", "http://localhost:8000/media/evt-002/belgrano4.jpeg",                                       "user_004", "Diana",    uploaded_at=datetime(2026, 6, 15, 22, 30, tzinfo=_utc), uploader_handle="@diana_mv",      caption="Llanto y alegría. Belgrano campeón Apertura 2026 ✨", likes_count=55),
    Photo("photo-018", "evt-002", "http://localhost:8000/media/evt-002/belgrano-2509-optimized.jpg",                          "user_003", "Carlos",   uploaded_at=datetime(2026, 6, 15, 22, 45, tzinfo=_utc), uploader_handle="@carlos_fan",    caption="El Kempes repleto de azul. ¡Qué noche! 🔵⚪", likes_count=72),
    Photo("photo-019", "evt-002", "http://localhost:8000/media/evt-002/WhatsApp%20Image%202026-06-20%20at%2012.58.46.jpeg",   "user_002", "Bob",      uploaded_at=datetime(2026, 6, 15, 22, 58, tzinfo=_utc), uploader_handle="@bob_ftw",       caption="El momento del penal decisivo. El Kempes se paralizó 😤⚽", likes_count=34),
    Photo("photo-020", "evt-002", "http://localhost:8000/media/evt-002/WhatsApp%20Image%202026-06-20%20at%2012.47.42.jpeg",   "user_006", "Fernando", uploaded_at=datetime(2026, 6, 15, 23,  5, tzinfo=_utc), uploader_handle="@fer_nando",     caption="Uvita celebra el gol del título 🙌🔵", likes_count=127),
    Photo("photo-021", "evt-002", "http://localhost:8000/media/evt-002/WhatsApp%20Image%202026-06-20%20at%2012.58.47.jpeg",   "user_007", "Gabriela", uploaded_at=datetime(2026, 6, 15, 23, 15, tzinfo=_utc), uploader_handle="@gaby_celeste",  caption="Locura en la tribuna. ¡Primer Apertura de Belgrano! 🎉", likes_count=211),
    Photo("photo-010", "evt-003", "https://picsum.photos/400/300?random=10", "user_002", "Bob",      uploaded_at=datetime(2026, 6, 26, 18, 40, tzinfo=_utc)),
    Photo("photo-011", "evt-004", "http://localhost:8000/media/evt-004/mundial.jpeg",  "user_003", "Carlos",   uploaded_at=datetime(2026, 6, 24, 21, 20, tzinfo=_utc), uploader_handle="@carlos_fan",   caption="¡Llegando al fan fest! El ambiente está increíble 🔥", likes_count=24),
    Photo("photo-012", "evt-004", "http://localhost:8000/media/evt-004/mundial2.jpg", "user_003", "Carlos",   uploaded_at=datetime(2026, 6, 24, 21, 55, tzinfo=_utc), uploader_handle="@carlos_fan",   caption="¡Gol de Lozano! La barra está explotando 🇲🇽⚽"),
    Photo("photo-013", "evt-004", "http://localhost:8000/media/evt-004/mundial3.jpg", "user_006", "Fernando", uploaded_at=datetime(2026, 6, 24, 22, 10, tzinfo=_utc), uploader_handle="@fer_nando",    caption="El pub lleno a reventar, increíble noche 🍺🎉", likes_count=8),
    Photo("photo-014", "evt-006", "https://picsum.photos/400/300?random=14", "user_004", "Diana",    uploaded_at=datetime(2026, 6, 28, 20, 40, tzinfo=_utc), uploader_handle="@diana_mv",     caption="Kane desde el punto del penal 🏴󠁧󠁢󠁥󠁮󠁧󠁿"),
    Photo("photo-015", "evt-006", "https://picsum.photos/400/300?random=15", "user_006", "Fernando", uploaded_at=datetime(2026, 6, 28, 21, 30, tzinfo=_utc), uploader_handle="@fer_nando",    caption="Three Lions! 🦁🦁🦁", likes_count=61),
]

# ── Seed comments (for demo richness) ─────────────────────────────────────────

_comment_t = datetime(2026, 6, 24, 21, 30, tzinfo=_utc)

COMMENTS: list[Comment] = [
    Comment(
        id="comment-001", photo_id="photo-011",
        user_id="user_005", user_name="Elena", user_handle="@elena_fan",
        text="¡Qué fotos! 🙌 El ambiente se ve increíble",
        created_at=_comment_t,
    ),
    Comment(
        id="comment-002", photo_id="photo-011",
        user_id="user_002", user_name="Bob", user_handle="@bob_ftw",
        text="Ojalá hubiera podido ir 😭",
        created_at=datetime(2026, 6, 24, 21, 45, tzinfo=_utc),
    ),
    Comment(
        id="comment-003", photo_id="photo-013",
        user_id="user_003", user_name="Carlos", user_handle="@carlos_fan",
        text="¡Una noche para no olvidar! México campeón 🏆",
        created_at=datetime(2026, 6, 24, 22, 20, tzinfo=_utc),
    ),
]

# ── Recaps (pre-generated for past events) ────────────────────────────────────

RECAPS: list[Recap] = [
    Recap(
        event_id="evt-002",
        narrative=(
            "Una noche histórica en el Estadio Mario Alberto Kempes de Córdoba. "
            "Belgrano consiguió el primer título Apertura de su historia al remontar "
            "un 2-1 adverso ante River Plate. El héroe fue Nicolás 'Uvita' Fernández, "
            "que anotó un doblete en los minutos finales — el primero de penal tras "
            "una revisión del VAR, el segundo en el tiempo de descuento — para desatar "
            "la locura en todo Córdoba."
        ),
        slides=[
            RecapSlide(label="Resultado final",          description="Belgrano 3 - 2 River Plate"),
            RecapSlide(label="Colidio abre el marcador", description="Facundo Colidio pone en ventaja a River en el minuto 17"),
            RecapSlide(label="Morales empata de cabeza", description="Leonardo Morales iguala con un remate fuerte en el minuto 25"),
            RecapSlide(label="Galván vuelve a adelantar a River", description="Tomás Galván restaura la ventaja riverplatense en el minuto 55"),
            RecapSlide(label="Penal histórico (VAR)",    description="El VAR sanciona pena máxima; Uvita Fernández la convierte en el minuto 82"),
            RecapSlide(label="Campeón en el descuento",  description="Uvita Fernández sella el 3-2 en el último minuto y hace historia"),
        ],
        home_team="Belgrano",
        away_team="River Plate",
        home_score=3,
        away_score=2,
        photo_count=8,
        correct_predictors=[],
        fallback=True,
    ),
    Recap(
        event_id="evt-004",
        narrative=(
            "Una noche épica en La Mona Sports Bar de Córdoba. Argentina brilló con "
            "la magia de Messi y Di María para vencer 2-1 a México en un duelo "
            "vibrante que tuvo a los fanáticos de pie durante los 90 minutos."
        ),
        slides=[
            RecapSlide(label="Resultado final",       description="Argentina 2 - 1 México"),
            RecapSlide(label="Gol de Messi",          description="Messi abre el marcador en el minuto 22 con un disparo inatajable"),
            RecapSlide(label="Empate de Lozano",      description="Chucky Lozano empata en el minuto 55 con un golazo de media distancia"),
            RecapSlide(label="Gol de la victoria",    description="Di María sentencia el partido en el minuto 78 con un remate de zurda"),
        ],
        home_team="Argentina",
        away_team="México",
        home_score=2,
        away_score=1,
        photo_count=3,
        correct_predictors=[],
        fallback=True,
    ),
    Recap(
        event_id="evt-006",
        narrative=(
            "The English Pub fue testigo de un thriller europeo. Inglaterra remontó "
            "el duelo ante Italia con tres goles en un partido que no decepcionó a nadie. "
            "La genialidad de Saka en el minuto 65 resultó definitiva."
        ),
        slides=[
            RecapSlide(label="Resultado final",       description="Inglaterra 3 - 2 Italia"),
            RecapSlide(label="Gol de Kane",           description="Kane abre el marcador de penal en el minuto 20"),
            RecapSlide(label="Gol de Bellingham",     description="Bellingham amplía con un golazo de volea en el minuto 35"),
            RecapSlide(label="Reacción italiana",     description="Immobile y Verratti descuentan en los minutos 50 y 80"),
            RecapSlide(label="Saka define",           description="Saka sella la victoria inglesa en el minuto 65"),
        ],
        home_team="Inglaterra",
        away_team="Italia",
        home_score=3,
        away_score=2,
        photo_count=2,
        correct_predictors=[],
        fallback=True,
    ),
]

# ── Convenience lookups (used by services) ────────────────────────────────────

FAN_NAMES: dict[str, str] = {f.user_id: f.name for f in FANS}
