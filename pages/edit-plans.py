import streamlit as st
import requests, json, base64
from slugify import slugify

# --- GitHub Settings ---
GITHUB_REPO = "faizanhaider55/marketing-deck"
GITHUB_PATH = "data"
GITHUB_BRANCH = "main"
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# --- GitHub functions ---
def list_github_files():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_PATH}?ref={GITHUB_BRANCH}"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200:
        return [f["name"] for f in resp.json() if f["name"].endswith(".json")]
    return []

def load_plan_from_github(filename):
    url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{GITHUB_PATH}/{filename}"
    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.json()
    return {}

def save_plan_to_github(filename, data, commit_msg="Update plan via Streamlit"):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_PATH}/{filename}"
    content = json.dumps(data, indent=2)
    b64_content = base64.b64encode(content.encode()).decode()
    body = {"message": commit_msg, "content": b64_content, "branch": GITHUB_BRANCH}
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200:
        body["sha"] = resp.json()["sha"]
    r = requests.put(url, headers=HEADERS, json=body)
    return r.status_code in [200, 201]

def parse_tools(text):
    tools = []
    for ln in text.splitlines():
        if not ln.strip():
            continue
        if " - " in ln:
            name, url = ln.split(" - ", 1)
        else:
            name, url = ln, ln
        tools.append({"name": name.strip(), "url": url.strip()})
    return tools

def format_tools(tools):
    if not tools:
        return []
    if isinstance(tools, list):
        normed = tools
    elif isinstance(tools, dict):
        normed = tools.get("high_priority", [])
    else:
        return []
    lines = []
    for t in normed:
        if isinstance(t, dict):
            lines.append(f"{t.get('name','')} - {t.get('url','')}".strip(" -"))
        elif isinstance(t, str):
            lines.append(t)
    return lines

# --- UI ---
st.set_page_config(page_title="Edit Plans", page_icon="✏️", layout="wide")
st.title("✏️ Edit Existing Marketing Plans")

# Load available plans
files = list_github_files()
if not files:
    st.error("No plans found in GitHub.")
    st.stop()

# Map filenames to titles for selection
file_title_map = {}
for f in files:
    plan_data = load_plan_from_github(f)
    title = plan_data.get("title", f)
    file_title_map[title] = f

select
