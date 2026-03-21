class Mir4ApiError(RuntimeError):
    """Respuesta inesperada de webapi.mir4global.com (code != 200 o sin data)."""


class Mir4HttpError(Mir4ApiError):
    """Error HTTP de red o status no exitoso."""
