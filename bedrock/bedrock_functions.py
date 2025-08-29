import json
import boto3

bedrock = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1"
)


def construir_prompt(historia, mensaje_usuario, preferencias):
    """Construye el prompt que se enviará al modelo de lenguaje en Bedrock.

    Args:
        historia (list[dict]):
            Lista de turnos de la conversación previa.
            Cada elemento debe ser un diccionario con las claves:
                - 'usuario' (str): mensaje del usuario en ese turno.
                - 'ia' (str): respuesta del asistente en ese turno.
        mensaje_usuario (str):
            El nuevo mensaje del usuario que debe responder el modelo.
        preferencias (dict):
            Diccionario con las preferencias del usuario. Debe contener:
                - 'gustos' (str): intereses o preferencias del usuario.
                - 'estilo' (str): estilo de las respuestas (breves).
                - 'idioma' (str): idioma principal en que deben generarse las respuestas(español).

    Returns:
        str:
            Prompt en formato de texto listo para ser enviado al modelo de lenguaje.
    """
    prompt = (
        "Eres un asistente personal útil y organizado.\n"
        f"Eres un asistente personal. Gustos del usuario: {preferencias['gustos']}.\n"
        f"Prefiere respuestas {preferencias['estilo']}.\n"
        f"Idioma principal: {preferencias['idioma']}.\n"
        "Adapta siempre tus respuestas a esos gustos.\n\n"
    )
    for entrada in historia:
        prompt += f"\n\nHuman: {entrada['usuario']}\n\nAssistant: {entrada['ia']}"
    prompt += f"\n\nHuman: {mensaje_usuario}\n\nAssistant:"
    return prompt


def consulta_a_bedrock(prompt):
    """Envía un prompt al modelo Claude (Anthropic) en Amazon Bedrock y devuelve la respuesta.

    Args:
        prompt (str):
            Texto del prompt que se desea enviar al modelo.

    Returns:
        str:
            Texto generado por el modelo, sin espacios iniciales o finales.

    Raises:
        botocore.exceptions.ClientError:
            Si ocurre un error al llamar al servicio Bedrock.
        KeyError:
            Si la respuesta no contiene la clave esperada ('completion').
        json.JSONDecodeError:
            Si la respuesta del modelo no se puede decodificar como JSON.
    """
    body = json.dumps({
        "prompt": prompt,
        "max_tokens_to_sample": 400,
        "temperature": 0.7,
        "stop_sequences": ["\n\n", "Usuario:", "Asistente:"]
    })

    response = bedrock.invoke_model(
        body=body,
        modelId="anthropic.claude-v2",
        contentType="application/json",
        accept="application/json"
    )

    resultado = json.loads(response['body'].read())
    return resultado['completion'].strip()