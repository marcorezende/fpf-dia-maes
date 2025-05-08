import base64
import os
from io import BytesIO

import requests
import streamlit as st
from PIL import Image
from openai import OpenAI, RateLimitError
from streamlit_javascript import st_javascript
from supabase import create_client

# === Configurações iniciais ===
st.set_page_config(page_title="Dia das Mães - Imagem Personalizada", layout="centered")

MAX_GLOBAL_REQUESTS = 100
MAX_ATTEMPTS = 2


@st.cache_resource
def init_connection():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SECRET_KEY")
    return create_client(url, key)


supabase = init_connection()


def log(_ip):
    response = supabase.table("logs").select("*").eq("ip", _ip).execute()
    return response.data or None


def insert_log(_ip, memory):
    supabase.table("logs").insert({
        "ip": _ip,
        "attempts": 1,
        "memory": memory
    }).execute()


def update_log(_ip, attempts, memory):
    supabase.table("logs").update({
        "attempts": attempts + 1,
        "memory": memory
    }).eq('ip', _ip).execute()


def apply_watermark(_image, watermark_image, position=(0, 0)):
    watermark = Image.open(watermark_image).convert("RGBA")
    r, g, b, a = watermark.split()
    watermark = Image.merge("RGBA", (r, g, b, a))

    padding = 384
    original_width, original_height = _image.size
    new_height = original_height + 2 * padding

    new_image = Image.new("RGBA", (original_width, new_height), (0, 0, 0, 255))
    new_image.paste(_image, (0, padding))
    new_image.paste(watermark, position, watermark)

    return new_image


with open("data/patrocinio.png", "rb") as img_file:
    encoded = base64.b64encode(img_file.read()).decode()

col1, col2 = st.columns([3, 1])

with col1:
    st.header('Crie uma imagem especial para sua :green[mãe]!')

with col2:
    st.image("data/bit.png", use_container_width=True)

# === Interface ===
st.write(
    "Digite um momento inesquecível que você viveu com sua mãe e receba uma imagem personalizada com amor e tecnologia.")

ip = st_javascript("""await fetch("https://api.ipify.org?format=json").then(r => r.json()).then(j => j.ip)""")
prompt_user = st.text_area("Digite aqui o momento especial:", height=100, max_chars=248)

if 'run_button' in st.session_state and st.session_state.run_button is True:
    st.session_state.running = True
else:
    st.session_state.running = False

gerar = st.button("🎁 Gerar imagem", disabled=st.session_state.running, key='run_button')

initial_prompt = f"""You are a specialist artist to a mother's day campaign your task is to
In a 8bit animation style, reminiscent of early 21st century design principles like Final Fantasy for children.
Remember that people's features must be Brazilian.

A portrait Image of: \n
{prompt_user}"""

# === Geração da Imagem ===
if gerar and prompt_user.strip():
    data = log(ip)
    data = data[0] if data else None
    if data and int(data["attempts"]) >= MAX_ATTEMPTS:
        disable = False
        st.warning("Você já alcançou o limite de imagens geradas ❤️ Obrigado por participar!")
    else:
        with st.spinner("Gerando imagem..."):
            try:

                client = OpenAI()
                prompt = initial_prompt.format(prompt_user=prompt_user)

                result = client.images.generate(
                    model="dall-e-3",
                    size="1024x1024",
                    prompt=prompt
                )

                image_url = result.data[0].url
                response = requests.get(image_url)
                img = Image.open(BytesIO(response.content)).convert("RGBA")
                image = apply_watermark(img, './watermark.png')
                img_bytes = BytesIO()
                image.save(img_bytes, format="PNG")
                img_bytes.seek(0)
                st.session_state.running = False
                st.download_button(
                    label="📥 Baixar imagem",
                    data=img_bytes,
                    file_name="minha-imagem.png",
                    mime="image/png"
                )
                st.image(image=image, caption="Sua imagem personalizada 💖", use_container_width=True)

                if not data:
                    insert_log(_ip=ip, memory=prompt)
                else:
                    update_log(_ip=ip, attempts=int(data["attempts"]), memory=prompt)
            except RateLimitError:
                st.session_state.running = False
                st.error("🚫 Limite de requisições por minuto excedido. Por favor, aguarde um pouco e tente novamente.")
            except Exception as e:
                st.session_state.running = False
                st.error(f"Erro ao gerar imagem: {str(e)}")

else:
    if gerar:
        st.warning("Por favor, digite algo antes de gerar.")

st.markdown("""
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #4caf50;
        color: white;
        text-align: center;
        padding: 10px;
        font-size: 14px;
    }
    </style>
    <div class="footer">
        Feito com ❤️ por Vanilton Pinheiro, Marco Rezende e Mário Santos na FPF Tech | © 2025
    </div>
""", unsafe_allow_html=True)
