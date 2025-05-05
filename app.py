import os
from io import BytesIO

import requests
import streamlit as st
from PIL import Image
from openai import OpenAI
from streamlit_javascript import st_javascript
from supabase import create_client

# === Configurações iniciais ===
st.set_page_config(page_title="Dia das Mães - Imagem Personalizada", layout="centered")


@st.cache_resource
def init_connection():
    url = "SUPABASE_URL"
    key = "SUPABASE_SECRET_KEY"
    return create_client(url, key)


supabase = init_connection()


@st.cache_data
def log(_ip):
    response = supabase.table("logs").select("*").eq("ip", _ip).execute()
    return response.data or None


@st.cache_data
def insert_log(_ip, memory):
    supabase.table("logs").insert({
        "ip": _ip,
        "attempts": 1,
        "memory": memory
    }).execute()


@st.cache_data
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


os.environ["OPENAI_API_KEY"] = ("TOKEN")

MAX_GLOBAL_REQUESTS = 100

# === Interface ===
st.title("💐 Crie uma imagem especial para sua mãe!")
st.write(
    "Digite um momento inesquecível que você viveu com sua mãe e receba uma imagem personalizada com amor e tecnologia.")

ip = st_javascript("""await fetch("https://api.ipify.org?format=json").then(r => r.json()).then(j => j.ip)""")
prompt = st.text_area("Digite aqui o momento especial:", height=100, max_chars=248)
gerar = st.button("🎁 Gerar imagem")

MAX_ATTEMPTS = 1

# === Geração da Imagem ===
if gerar and prompt.strip():
    data = log(ip)
    data = data[0] if data else None
    if data and int(data["attempts"]) >= MAX_ATTEMPTS:
        disable = False
        st.warning("Você já alcançou o limite de imagens geradas ❤️ Obrigado por participar!")
    else:
        with st.spinner("Gerando imagem..."):
            try:

                client = OpenAI()
                prompt = 'In a 8bit animation style, reminiscent of early 21st century design principles like Final Fantasy for children.' \
                         f'A portrait Image of {prompt}'

                result = client.images.generate(
                    model="dall-e-3",
                    size="1024x1024",
                    prompt=prompt
                )

                image_url = result.data[0].url
                response = requests.get(image_url)
                img = Image.open(BytesIO(response.content)).convert("RGBA")
                image = apply_watermark(img, './watermark.png')
                st.image(image=image, caption="Sua imagem personalizada 💖", use_container_width=True)

                if not data:
                    insert_log(_ip=ip, memory=prompt)
                else:
                    update_log(_ip=ip, attempts=int(data["attempts"]), memory=prompt)
            except Exception as e:
                st.error(f"Erro ao gerar imagem: {str(e)}")
else:
    if gerar:
        st.warning("Por favor, digite algo antes de gerar.")
