class ApiError(Exception):
    def __init__(self, status, code, message):
        self.status = status
        self.code = code
        self.message = message
        super().__init__(code)


def missing_playlist():
    return ApiError(404, "playlist_not_found", "No encontramos esa playlist.")


def missing_song():
    return ApiError(404, "song_not_found", "La ficha de esta canción no está disponible.")
