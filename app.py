import os, json, requests, base64
from urllib.parse import urlparse
import streamlit as st
from slugify import slugify

st.set_page_config(page_title="Marketing Masterplans", page_icon="📚", layout="wide")

# --- GitHub Settings ---
GITHUB_REPO = "faizanhaider55/marketing-deck"
GITHUB_PATH = "data"
GITHUB_BRANCH = "main"
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# --- Utilities ---
def github_file_url(filename):
    return f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{GITHUB_PATH}/{filename}"

def load_plan_from_github(filename):
    url = github_file_url(filename)
    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.json()
    return {}

def list_github_files():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_PATH}?ref={GITHUB_BRANCH}"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200:
        return [f["name"] for f in resp.json() if f["name"].endswith(".json")]
    return []

def save_plan_to_github(filename, data, commit_msg="Add new plan via Streamlit"):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_PATH}/{filename}"
    resp = requests.get(url, headers=HEADERS)
    content = json.dumps(data, indent=2)
    b64_content = base64.b64encode(content.encode()).decode()
    body = {"message": commit_msg, "content": b64_content, "branch": GITHUB_BRANCH}
    if resp.status_code == 200:
        body["sha"] = resp.json()["sha"]
    r = requests.put(url, headers=HEADERS, json=body)
    return r.status_code in [200, 201]

def md_list(items):
    return "\n".join([f"- {it}" for it in items]) if items else ""

def get_stage(plan, stage_title):
    for s in plan.get("stages", []):
        if s.get("title") == stage_title:
            return s
    return None

def get_step(stage, step_title):
    for s in stage.get("steps", []):
        if s.get("title") == step_title:
            return s
    return None

def render_toolbox(toolbox):
    if not toolbox:
        return
    st.markdown("## 🔧 Toolbox")
    if isinstance(toolbox, dict):
        for section, tools in toolbox.items():
            if not tools: continue
            st.markdown(f"### {section.replace('_',' ').title()}")
            for t in tools:
                st.markdown(f"- [{t['name']}]({t['url']})")
    elif isinstance(toolbox, list):
        for t in toolbox:
            st.markdown(f"- [{t['name']}]({t['url']})")

# --- Load all plans dynamically ---
plans = {}
for file in list_github_files():
    plan_data = load_plan_from_github(file)
    if plan_data.get("title"):
        plans[plan_data["title"]] = plan_data

# --- Sidebar: Add new plan ---
st.sidebar.markdown("---")
st.sidebar.subheader("➕ Submit a New Plan")
with st.sidebar.expander("Add Your Own Plan"):
    new_plan_title = st.text_input("Plan Title")
    if st.button("Submit Plan"):
        if not new_plan_title:
            st.warning("Please enter a plan title")
        else:
            filename = slugify(new_plan_title) + ".json"
            new_plan = {"title": new_plan_title, "intro": "", "stages": []}
            if save_plan_to_github(filename, new_plan):
                st.success(f"Plan '{new_plan_title}' submitted successfully!")
                st.experimental_rerun()  # reload the page to show the new plan

# --- Select existing plan ---
st.sidebar.markdown("---")
st.sidebar.title("📚 Marketing Masterplans")
if not plans:
    st.warning("No plans available yet.")
    st.stop()

plan_key = st.sidebar.selectbox("Plan", list(plans.keys()))
plan = plans[plan_key]

# --- Stage selection ---
stage_titles = [s["title"] for s in plan.get("stages", [])]
if not stage_titles:
    st.info("No stages found in this plan.")
    st.stop()
stage_title = st.selectbox("Select Stage", stage_titles)
stage = get_stage(plan, stage_title)

# --- Step selection ---
step_titles = [s["title"] for s in stage.get("steps", [])]
if not step_titles:
    st.info("No steps found in this stage.")
    st.stop()
step_title = st.selectbox("Select Step", step_titles)
step = get_step(stage, step_title)

# --- Display Step Details ---
st.markdown(f"## {step.get('title','')}")
st.markdown(f"**Goal:** {step.get('goal','')}")
st.markdown(f"**Why:** {step.get('why','')}")
st.markdown("**SOP / How:**")
st.markdown(md_list(step.get("how",[])))
st.markdown("**KPIs:**")
st.markdown(md_list(step.get("kpis",[])))
st.markdown("**Deliverables:**")
st.markdown(md_list(step.get("deliverables",[])))
render_toolbox(step.get("toolbox"))
