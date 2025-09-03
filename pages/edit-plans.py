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

# --- GitHub Functions ---
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
            name, url = ln.split(" - ",1)
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

# --- Session State Initialization ---
if "plans_data" not in st.session_state:
    st.session_state["plans_data"] = {}

def get_plan(filename):
    if filename in st.session_state["plans_data"]:
        return st.session_state["plans_data"][filename]
    plan = load_plan_from_github(filename)
    st.session_state["plans_data"][filename] = plan
    return plan

# --- Streamlit UI ---
st.set_page_config(page_title="Edit Plans", page_icon="✏️", layout="wide")
st.title("✏️ Edit Existing Marketing Plans")

files = list_github_files()
if not files:
    st.error("No plans found in GitHub.")
    st.stop()

# Select plan by title
plans_titles = {}
for f in files:
    plan_data = get_plan(f)
    title = plan_data.get("title", f)
    plans_titles[title] = f

selected_title = st.selectbox("Select a plan to edit", list(plans_titles.keys()))
selected_file = plans_titles[selected_title]

plan = get_plan(selected_file)
if not plan:
    st.warning("Could not load this plan.")
    st.stop()

# Editable fields
edit_title = st.text_input("Plan Title", value=plan.get("title",""))
st.session_state["plans_data"][selected_file]["title"] = edit_title

edit_stages = []
for i, s in enumerate(plan.get("stages", [])):
    with st.expander(f"📂 Stage {i+1}: {s.get('title','')}", expanded=False):
        stage_title = st.text_input(f"Stage {i+1} Title", value=s["title"], key=f"stage_{i}")
        st.session_state["plans_data"][selected_file]["stages"][i]["title"] = stage_title

        step_tabs = st.tabs([f"Step {j+1}" for j in range(len(s.get("steps", [])))])
        for j, step in enumerate(s.get("steps", [])):
            with step_tabs[j]:
                step_title = st.text_input(f"Step {j+1} Title", value=step.get("title",""), key=f"step_title_{i}_{j}")
                step_goal = st.text_area(f"Goal", value=step.get("goal",""), key=f"goal_{i}_{j}")
                step_why = st.text_area(f"Why", value=step.get("why",""), key=f"why_{i}_{j}")
                step_how = st.text_area(f"SOP / How", value="\n".join(step.get("how",[])), key=f"how_{i}_{j}")
                step_kpis = st.text_area(f"KPIs", value="\n".join(step.get("kpis",[])), key=f"kpis_{i}_{j}")
                step_deliverables = st.text_area(f"Deliverables", value="\n".join(step.get("deliverables",[])), key=f"deliv_{i}_{j}")

                toolbox = step.get("toolbox", {})
                tb_high = st.text_area("High Priority Tools", value="\n".join(format_tools(toolbox)), key=f"tb_high_{i}_{j}")
                tb_low = st.text_area(
                    "Low Priority Tools",
                    value="\n".join(format_tools(toolbox.get("low_priority", []))) if isinstance(toolbox, dict) else "",
                    key=f"tb_low_{i}_{j}"
                )

                # Update session state immediately
                st.session_state["plans_data"][selected_file]["stages"][i]["steps"][j] = {
                    "title": step_title,
                    "goal": step_goal,
                    "why": step_why,
                    "how": [ln.strip() for ln in step_how.splitlines() if ln.strip()],
                    "kpis": [ln.strip() for ln in step_kpis.splitlines() if ln.strip()],
                    "deliverables": [ln.strip() for ln in step_deliverables.splitlines() if ln.strip()],
                    "toolbox": {
                        "high_priority": parse_tools(tb_high),
                        "low_priority": parse_tools(tb_low)
                    }
                }

# Save button
if st.button("💾 Save Changes"):
    updated_plan = st.session_state["plans_data"][selected_file]
    success = save_plan_to_github(selected_file, updated_plan, commit_msg=f"Updated {updated_plan.get('title','')}")
    if success:
        st.success(f"✅ {updated_plan.get('title','')} updated successfully on GitHub!")
    else:
        st.error("❌ Failed to save plan on GitHub.")
