import streamlit as st
import requests
import zipfile
import io
from datetime import datetime


# --------------------------------------------------
# CONFIG
# --------------------------------------------------
username = 'JuriTeufllisch'
repo_name = 'cam'

# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def datetime_from_filename(filename: str) -> datetime:
    name = filename.replace(".jpg", "").replace(".jpeg", "")
    return datetime.strptime(name, "%d_%m_%y %H%M%S")


@st.cache_data(ttl=600)
def get_sorted_jpg_filenames(username: str, repo_name: str):
    api_url = f"https://api.github.com/repos/{username}/{repo_name}/contents/"
    response = requests.get(api_url)
    response.raise_for_status()

    files = [
        item["name"]
        for item in response.json()
        if item["name"].lower().endswith((".jpg", ".jpeg"))
    ]

    return sorted(
        files,
        key=lambda f: datetime.strptime(
            f.replace(".jpg", "").replace(".jpeg", ""),
            "%d_%m_%y %H%M%S"
        ),
        reverse=True
    )



@st.cache_data(ttl=600)
def create_zip_of_images(files):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file in files:
            raw_url = f"https://raw.githubusercontent.com/{username}/{repo_name}/main/{file}"
            image_data = requests.get(raw_url).content
            zip_file.writestr(file, image_data)

    zip_buffer.seek(0)
    return zip_buffer


def make_caption(filename: str) -> str:
    return (
        f"{filename[:2]}.{filename[3:5]}.{filename[6:8]} "
        f"{filename[9:11]}:{filename[11:13]}"
    )

# --------------------------------------------------
# LOAD FILES
# --------------------------------------------------
files = get_sorted_jpg_filenames(username, repo_name)

if not files:
    st.subheader("Currently no images available. Try again later!")
    st.stop()

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------
st.session_state.setdefault("access", False)
st.session_state.setdefault("mini_view", False)
st.session_state.setdefault("current_file_index", 0)

# --------------------------------------------------
# ACCESS CONTROL
# --------------------------------------------------
if not st.session_state["access"]:
    pwd = datetime.now().strftime("%H%M")
    pwd_input = st.text_input("Enter password:", type="password")
    if pwd_input == pwd:
        st.session_state["access"] = True
    else:
        st.stop()

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
with st.sidebar:
    n_default = min(12, len(files))
    x_default = min(6, n_default)

    n_max = st.slider(
        "number of images",
        min_value=1,
        max_value=len(files),
        value=n_default
    )

    x = st.slider(
        "number of images per line",
        min_value=1,
        max_value=x_default,
        value=x_default
    )

# NAVIGATION
# --------------------------------------------------
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    older = st.button(
        "←",
        disabled=st.session_state["current_file_index"] >= len(files) - 1
    )

with col3:
    newer = st.button(
        "→",
        disabled=st.session_state["current_file_index"] == 0
    )


if older and st.session_state["current_file_index"] < len(files) - 1:
    st.session_state["current_file_index"] += 1

if newer and st.session_state["current_file_index"] > 0:
    st.session_state["current_file_index"] -= 1

# --------------------------------------------------
# MAIN IMAGE
# --------------------------------------------------
current_file = files[st.session_state["current_file_index"]]
raw_url = f"https://raw.githubusercontent.com/{username}/{repo_name}/main/{current_file}"

st.image(
    raw_url,
    caption=make_caption(current_file),
    use_column_width=True
)

# --------------------------------------------------
# MINI VIEW
# --------------------------------------------------
st.session_state["mini_view"] = st.checkbox("show thumbnails")

if st.session_state["mini_view"]:
    rows = (n_max + x - 1) // x
    display_index = 0  # neueste zuerst

    for _ in range(rows):
        cols = st.columns(x)
        for col in cols:
            if display_index >= n_max:
                break

            file = files[display_index]
            col.image(
                f"https://raw.githubusercontent.com/{username}/{repo_name}/main/{file}",
                caption=make_caption(file),
                use_column_width=True
            )
            display_index += 1

# --------------------------------------------------
# DOWNLOAD ZIP
# --------------------------------------------------
st.download_button(
    label="Download images",
    data=create_zip_of_images(files[:n_max]),
    file_name="images.zip",
    mime="application/zip"
)









