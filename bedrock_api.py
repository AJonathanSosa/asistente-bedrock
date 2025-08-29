import streamlit as st
import speech_recognition as sr
from datetime import datetime, timedelta
import random
import io
from dateparser.search import search_dates
from st_audiorec import st_audiorec   # ✅ Nuevo grabador de audio
from google_model.google_calendar import conectar_google_calendar, extraer_duracion, crear_evento
from bedrock.bedrock_functions import construir_prompt, consulta_a_bedrock
st.set_page_config(page_title="Asistente Personal IA", layout="centered")


st.markdown("""
<div style="text-align:center; background-color:#0C0CAD; padding:10px; border-radius:10px; color:white">
    <h1>🤖 Nova </h1>
    <p>Tú asistente personal, organiza tus tareas y conversa con tu asistente por voz</p>
</div>
""", unsafe_allow_html=True)

# Inicializa sesión de chat y tareas
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "tasks" not in st.session_state:
    st.session_state.tasks = []
if "configurado" not in st.session_state:
    st.session_state.configurado = False
if "preferencias" not in st.session_state:
    st.session_state.preferencias = {}


if not st.session_state.configurado:
    st.subheader("⚙️ Configuración inicial (por voz)")
    st.markdown("🎤 **Menciona los temas que te interesan para mostrar información relacionada o salta esta configuración.**")

    audio_gustos = st_audiorec()

    gustos_detectados = ""
    if audio_gustos is not None:
        st.audio(audio_gustos, format="audio/wav")
        recognizer = sr.Recognizer()
        try:
            with sr.AudioFile(io.BytesIO(audio_gustos)) as source:
                audio = recognizer.record(source)
                gustos_detectados = recognizer.recognize_google(audio, language="es-ES")
                st.success(f"✅ Gustos detectados: {gustos_detectados}")
        except Exception:
            st.warning("⚠️ No se pudo reconocer el audio.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Guardar configuración") and gustos_detectados:
            st.session_state.preferencias = {
                "gustos": gustos_detectados,
                "estilo": "breves",
                "idioma": "español"
            }
            st.session_state.configurado = True
            st.success("✅ Preferencias guardadas. ¡Listo para conversar!")
            st.rerun()
    with col2:
        if st.button("Saltar"):
            st.session_state.preferencias = {
                "gustos": "general",
                "estilo": "breves",
                "idioma": "español"
            }
            st.session_state.configurado = True
            st.info("⚠️ Configuración predeterminada aplicada.")
            st.rerun()
# myproject1-470300
else:
    if "preferencias" not in st.session_state:
        st.session_state.preferencias = {"gustos": "tecnología, música", "estilo": "breves", "idioma": "español"}
    if "tasks" not in st.session_state:
        st.session_state.tasks = []
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "show_modal" not in st.session_state:
        st.session_state.show_modal = False
    if "show_info" not in st.session_state:
        st.session_state.show_info = False
    service = conectar_google_calendar()

    # Botón para mostrar/ocultar información del usuario
    if st.button("\n\n 👤 Mostrar / Ocultar Información"):
        st.session_state.show_info = not st.session_state.show_info

    if st.session_state.show_info:
        with st.container():
            st.markdown("#### 🧠 Información del usuario")
            gustos_actuales = st.session_state.preferencias.get("gustos", "No configurado")
            estilo_actual = st.session_state.preferencias.get("estilo", "breves")
            idioma_actual = st.session_state.preferencias.get("idioma", "español")

            st.info(f"**Gustos:** {gustos_actuales}\n\n")

            if st.button("✏️ Editar gustos"):
                st.session_state.show_modal = True  # Activar modal
    # === Modal flotante ===
    if st.session_state.show_modal:
        st.markdown('<div class="modal-backdrop"></div>', unsafe_allow_html=True)
        modal = st.empty()
        with modal.container():
            st.markdown('<div class="modal-content">', unsafe_allow_html=True)

            st.markdown("### ⚙️ Editar preferencias")
            nuevo_gusto = st.text_input("Gustos", value=st.session_state.preferencias.get("gustos", ""))
            nuevo_estilo = st.selectbox("Estilo de respuesta", ["breves", "detalladas"], index=0)

            col_modal = st.columns(2)
            with col_modal[0]:
                if st.button("✅ Guardar cambios"):
                    st.session_state.preferencias["gustos"] = nuevo_gusto
                    st.session_state.preferencias["estilo"] = nuevo_estilo
                    st.session_state.show_modal = False
                    st.rerun()
            with col_modal[1]:
                if st.button("❌ Cancelar"):
                    st.session_state.show_modal = False
                    st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

    # 👇 Esto ya queda SIEMPRE visible, en la misma columna
    st.markdown("##### 🔍 Recomendaciones basadas en tus gustos:")
    gustos_actuales = st.session_state.preferencias.get("gustos", "general").lower()

    # Diccionario de recomendaciones
    recomendaciones_dict = {
        "tecnología": [
            "Última noticia tech: avances en IA generativa",
            "Cursos recomendados: Machine Learning, Python avanzado"
        ],
        "música": [
            "Playlist sugerida: Lo-Fi para concentración",
            "Evento: Concierto virtual este fin de semana"
        ],
        "deporte": [
            "Rutina sugerida: 20 min cardio diario",
            "Partido destacado: Liga de Campeones mañana"
        ],
        "cine": [
            "Estreno de la semana: película de ciencia ficción en cartelera",
            "Top recomendado en streaming: thriller psicológico"
        ]
    }

    # Mostrar recomendaciones según gustos
    mostro_algo = False
    for clave, sugerencias in recomendaciones_dict.items():
        if clave in gustos_actuales:
            for s in sugerencias:
                st.markdown(f"- {s}")
            mostro_algo = True

    # Si no encontró nada, mostrar recomendaciones random
    if not mostro_algo:
        st.info("No encontré coincidencias exactas con tus gustos, aquí tienes algo al azar 👇")
        random_sugerencias = random.choice(list(recomendaciones_dict.values()))
        for s in random_sugerencias:
            st.markdown(f"- {s}")
    st.markdown("---")

    col1, col2 = st.columns([2, 1])
    with col1:
        user_input = st.text_input("Escribe tu mensaje:", "")

        if st.button("Enviar") and user_input:
            # Detectar intención de crear evento
            palabras_clave = ["agenda", "agendar", "cita", "evento", "reunión", "recordatorio"]
            if any(palabra in user_input.lower() for palabra in palabras_clave):
                # Intentar parsear fecha/hora
                fecha_evento = search_dates(
                    user_input,
                    languages=['es'],
                    settings={"PREFER_DATES_FROM": "future"}
                ) 
                if fecha_evento:
                    # Calcular duración
                    duracion_min = extraer_duracion(user_input, default_min=30)
                    _, fecha_evento = fecha_evento[0]
                    fecha_inicio = fecha_evento.isoformat()
                    fecha_fin = (fecha_evento + timedelta(minutes=duracion_min)).isoformat()
                    link_evento = crear_evento(service, user_input, fecha_inicio, fecha_fin, "Evento creado desde Nova")
                    respuesta = f"✅ Evento creado: {link_evento}"
                else:
                    respuesta = "No pude identificar la fecha y hora. Por favor indica cuándo."
                st.markdown(f"{respuesta}")
            else:
                prompt = construir_prompt(st.session_state.chat_history, user_input, st.session_state.preferencias)
                respuesta = consulta_a_bedrock(prompt)
                st.session_state.chat_history.append({"usuario": user_input, "ia": respuesta})
                st.markdown(f"Tú: {user_input}")
                st.markdown(f"Nova: {respuesta}")

        # Historial
        # if st.session_state.chat_history:
        st.markdown("\n\n\n\n---")
        st.markdown("### Historial del chat")
        for entrada in reversed(st.session_state.chat_history):
            st.markdown(f"Tú: {entrada['usuario']}")
            st.markdown(f"Nova: {entrada['ia']}")

    with col2:
        st.subheader("📋 Tareas pendientes")

        tarea_input = st.text_input("Nueva tarea:")
        fecha_entrega = st.date_input("Fecha de entrega")
        hora_entrega = st.time_input("Hora de entrega")

        if st.button("➕ Agregar tarea"):
            if tarea_input:
                dt_entrega = datetime.combine(fecha_entrega, hora_entrega)
                st.session_state.tasks.append({"tarea": tarea_input, "entrega": dt_entrega})
                st.success(f"Tarea '{tarea_input}' agregada")
            else:
                st.warning("Ingrese una tarea primero")

        if st.session_state.tasks:
            for t in st.session_state.tasks:
                fecha_str = t["entrega"].strftime("%Y-%m-%d %H:%M")
                st.markdown(f"- {t['tarea']} (Entrega: {fecha_str})")
                if datetime.now() + timedelta(days=1) >= t["entrega"]:
                    st.error(f"⚠️ La tarea '{t['tarea']}' vence en menos de 1 día!")
        else:
            st.info("No hay tareas pendientes")

    

