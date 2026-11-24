from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9-]{0,63}$"
Identifier = Annotated[str, StringConstraints(pattern=ID_PATTERN)]
PlaylistName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
NoteText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
NoteSource = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class StrictInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ErrorBody(BaseModel):
    code: str
    message: str
    fields: list[str] | None = None


class Login(StrictInput):
    profileId: Identifier
    code: str = Field(min_length=1, max_length=128)


class Profile(BaseModel):
    profileId: Identifier
    displayName: str
    role: Literal["listener", "editor"]


class ProfileInput(StrictInput):
    displayName: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class PersonalLogin(StrictInput):
    code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=128)] = Field(repr=False)


class CreatedProfile(Profile):
    accessCode: str = Field(repr=False)
    graphPending: bool


class Credit(BaseModel):
    name: str
    role: str


class Note(StrictInput):
    text: NoteText
    source: NoteSource


class Editorial(BaseModel):
    credits: list[Credit] = Field(default_factory=list)
    notes: list[Note] = Field(default_factory=list)


class Song(BaseModel):
    songId: Identifier
    title: str
    editorial: Editorial


class SongSummary(BaseModel):
    songId: Identifier
    title: str


class SongPage(BaseModel):
    items: list[SongSummary]
    nextAfter: Identifier | None = None


class Recommendation(BaseModel):
    song: Song
    affinity: int = Field(ge=1)


class Recommendations(BaseModel):
    items: list[Recommendation]
    partial: bool


class PlaylistInput(StrictInput):
    name: PlaylistName


class TrackOrder(StrictInput):
    songIds: list[Identifier] = Field(max_length=1000)


class NoteUpdate(StrictInput):
    notes: list[Note] = Field(min_length=1, max_length=20)


class Playlist(BaseModel):
    playlistId: Identifier
    name: str
    trackCount: int


class Playlists(BaseModel):
    items: list[Playlist]


class Track(BaseModel):
    songId: Identifier
    position: int = Field(ge=1)
    song: Song | None


class PlaylistDetail(Playlist):
    tracks: list[Track]


class SavedTrack(BaseModel):
    playlistId: Identifier
    songId: Identifier
    position: int = Field(ge=1)
    created: bool


class Health(BaseModel):
    status: Literal["ok"]
