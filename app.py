import os

import streamlit as st
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
        "attempts": attempts+1,
        "memory": memory
    }).eq('ip', _ip).execute()


os.environ["OPENAI_API_KEY"] = ("TOKEN")

MAX_GLOBAL_REQUESTS = 100

# === Interface ===
st.title("💐 Crie uma imagem especial para sua mãe!")
st.write(
    "Digite um momento inesquecível que você viveu com sua mãe e receba uma imagem personalizada com amor e tecnologia.")

ip = st_javascript("""await fetch("https://api.ipify.org?format=json").then(r => r.json()).then(j => j.ip)""")
prompt = st.text_area("Digite aqui o momento especial:", height=100)
gerar = st.button("🎁 Gerar imagem")

MAX_ATTEMPTS = 1

# === Geração da Imagem ===
if gerar and prompt.strip():
    data = log(ip)
    data = data[0] if data else None
    if data and int(data["attempts"]) >= MAX_ATTEMPTS:
        st.warning("Você já alcançou o limite de imagens geradas ❤️ Obrigado por participar!")
    else:
        with st.spinner("Gerando imagem..."):
            try:

                client = OpenAI()

                result = client.images.generate(
                    model="dall-e-3",
                    size="1792x1024",
                    prompt=prompt
                )

                image_url = result.data[0].url

                # image = Image.open(io.BytesIO(image_bytes))
                st.image(image_url, caption="Sua imagem personalizada 💖", use_container_width=True)

                # # Download
                # with open(image_path, "rb") as f:
                #     st.download_button("📥 Baixar imagem", f, file_name="imagem_dia_das_maes.png")

                # Compartilhamento
                whatsapp_text = f"Olha a imagem que fiz com minha mãe! 💖 #DiaDasMães {prompt}"
                whatsapp_link = f"https://wa.me/?text={whatsapp_text.replace(' ', '%20')}"
                st.markdown(f"[📤 Compartilhar no WhatsApp]({whatsapp_link})")

                if not data:
                    insert_log(_ip=ip, memory=prompt)
                else:
                    update_log(_ip=ip, attempts=int(data["attempts"]), memory=prompt)
            except Exception as e:
                st.error(f"Erro ao gerar imagem: {str(e)}")
else:
    if gerar:
        st.warning("Por favor, digite algo antes de gerar.")
