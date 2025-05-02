import os

import streamlit as st
from openai import OpenAI

# === Configurações iniciais ===
st.set_page_config(page_title="Dia das Mães - Imagem Personalizada", layout="centered")

os.environ[
    "OPENAI_API_KEY"] = "api_key"

MAX_GLOBAL_REQUESTS = 100

#
# # === Logs de uso ===
# logs_file = "logs.csv"
# if os.path.exists(logs_file):
#     logs = pd.read_csv(logs_file)
#     if user_id in logs["user_id"].values:
#         st.warning("Você já gerou sua imagem ❤️ Obrigado por participar!")
#         st.stop()
# else:
#     logs = pd.DataFrame(columns=["user_id", "prompt", "image_path", "timestamp"])

# === Interface ===
st.title("💐 Crie uma imagem especial para sua mãe!")
st.write(
    "Digite um momento inesquecível que você viveu com sua mãe e receba uma imagem personalizada com amor e tecnologia.")

prompt = st.text_area("Digite aqui o momento especial:", height=100)
gerar = st.button("🎁 Gerar imagem")

# === Geração da Imagem ===
if gerar and prompt.strip():
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

        except Exception as e:
            st.error(f"Erro ao gerar imagem: {str(e)}")
else:
    if gerar:
        st.warning("Por favor, digite algo antes de gerar.")
