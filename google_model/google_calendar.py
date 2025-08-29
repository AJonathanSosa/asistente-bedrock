import pickle
import os
import re
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import re



SCOPES = ['https://www.googleapis.com/auth/calendar']

def extraer_duracion(user_input: str, default_min: int = 15) -> int:
    """
    Busca duración en el texto del usuario. Ej: '30 minutos', '2 horas'
    Devuelve la duración en minutos. Si no encuentra, usa default_min.
    """
    match = re.search(r'(\d+)\s*(minutos|min|horas|hora|h)', user_input.lower())
    if match:
        cantidad = int(match.group(1))
        unidad = match.group(2)
        if "hora" in unidad or unidad == "h":
            return cantidad * 60
        else:
            return cantidad
    return default_min


def conectar_google_calendar():
    """ Conecta con la API de Google Calendar usando OAuth 2.0.

    Este método intenta cargar credenciales previamente guardadas en el archivo
    `token.pkl`. Si no existen o no son válidas, solicita autenticación al usuario
    mediante un flujo OAuth en el navegador, usando el archivo de credenciales
    de cliente (`google_model/credentials.json`). Una vez autenticado, guarda las
    credenciales en `token.pkl` para futuros usos.

    Returns:
        googleapiclient.discovery.Resource:
            Objeto de servicio autorizado para interactuar con la API de Google Calendar
            (permite listar, crear, actualizar y eliminar eventos).
    Raises:
        FileNotFoundError: Si no se encuentra el archivo `google_model/credentials.json`
                           necesario para iniciar el flujo de autenticación.
        google.auth.exceptions.RefreshError: Si no se pueden refrescar las credenciales expiradas.
    """
    creds = None
    # Cargar token si existe
    if os.path.exists('token.pkl'):
        with open('token.pkl', 'rb') as token:
            creds = pickle.load(token)

    # Si no hay credenciales válidas, pedir login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('google_model/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Guardar token para la próxima vez
        with open('token.pkl', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)
    return service


def crear_evento(service, titulo, fecha_inicio, fecha_fin, descripcion=""):
    """Crea un evento en Google Calendar. Construye un objeto de evento con título, descripción, fecha de inicio y fin,
    y lo inserta en el calendario principal del usuario (`primary`).  
    El evento se crea en la zona horaria `America/Mexico_City`.

    Args:
         service (googleapiclient.discovery.Resource):
            Objeto de servicio de Google Calendar previamente autenticado.
        titulo (str):
            Título del evento.
        fecha_inicio (str):
            Fecha y hora de inicio del evento en formato ISO 8601 
            (ejemplo: "2025-08-29T10:00:00").
        fecha_fin (str):
            Fecha y hora de fin del evento en formato ISO 8601 
            (ejemplo: "2025-08-29T11:00:00").
        descripcion (str, optional):
            Descripción del evento. Por defecto es una cadena vacía.

    Returns:
        str:
            URL pública (`htmlLink`) que apunta al evento creado en Google Calendar.
    Raises:
        googleapiclient.errors.HttpError:
            Si ocurre un error al comunicarse con la API de Google Calendar.
    """
    evento = {
        'summary': titulo,
        'description': descripcion,
        'start': {'dateTime': fecha_inicio, 'timeZone': 'America/Mexico_City'},
        'end': {'dateTime': fecha_fin, 'timeZone': 'America/Mexico_City'},
    }

    evento_creado = service.events().insert(calendarId='primary', body=evento).execute()
    return evento_creado.get('htmlLink')