import os, json, requests, base64
from urllib.parse import urlparse
import streamlit as st
from slugify import slugify

st.set_page_config(page_title="Marketing Masterplans", page_icon="📚", layout="wide")

# --- GitHub Settings ---
GITHUB_REPO = "faizanhaider55/marketing-deck"  # replace with your repo
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

def save_plan_to_github(filename, data, commit_msg="Update plan via Streamlit"):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_PATH}/{filename}"
    resp = requests.get(url, headers=HEADERS)
    content = json.dumps(data, indent=2)
    b64_content = base64.b64encode(content.encode()).decode()
    body = {"message": commit_msg, "content": b64_content, "branch": GITHUB_BRANCH}
    if resp.status_code == 200:
        sha = resp.json()["sha"]
        body["sha"] = sha
    r = requests.put(url, headers=HEADERS, json=body)
    if r.status_code in [200, 201]:
        return True
    st.error(f"Error uploading: {r.text}")
    return False

def domain_from_url(url):
    try:
        netloc = urlparse(url).netloc or url
        return netloc.replace("www.", "")
    except Exception:
        return ""

def clearbit_logo(url):
    d = domain_from_url(url)
    if not d:
        return None
    return f"https://logo.clearbit.com/{d}"

def md_list(items):
    return "\n".join([f"- {it}" for it in items]) if items else ""

def get_stage(plan, stage_title=None):
    for s in plan.get("stages", []):
        if stage_title and s.get("title") == stage_title:
            return s
    return None

def get_step(stage, step_title=None):
    for s in stage.get("steps", []):
        if step_title and s.get("title") == step_title:
            return s
    return None

def render_toolbox_section(title, tools):
    if not tools:
        return
    with st.expander(title):
        cols = st.columns(3)
        for i, t in enumerate(tools):
            with cols[i % 3]:
                logo = clearbit_logo(t.get("url", ""))
                if logo:
                    st.image(logo, width=50)
                name = t.get("name", "Tool")
                url = t.get("url", "#")
                st.markdown(f"[{name}]({url})", unsafe_allow_html=True)

def render_toolbox(toolbox):
    if not toolbox:
        return
    st.markdown("## 🔧 Toolbox")
    if isinstance(toolbox, dict):
        render_toolbox_section("🔑 High Priority", toolbox.get("high_priority", []))
        render_toolbox_section("🧩 Low Priority", toolbox.get("low_priority", []))
    elif isinstance(toolbox, list):
        render_toolbox_section("Tools", toolbox)

# --- Load existing plans dynamically from GitHub ---
def list_github_files():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_PATH}?ref={GITHUB_BRANCH}"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200:
        return [f["name"] for f in resp.json() if f["name"].endswith(".json")]
    return []

plans = {}
plan_files = {}
for file in list_github_files():
    plan_data = load_plan_from_github(file)
    if plan_data.get("title"):
        plans[plan_data["title"]] = plan_data
        plan_files[plan_data["title"]] = file

# --- Sidebar: Add new plan ---
st.sidebar.markdown("---")
st.sidebar.subheader("➕ Submit a New Plan")
with st.sidebar.expander("Add Your Own Plan"):
    new_plan_title = st.text_input("Plan Title")
    base_plan_choice = st.selectbox("Import from existing plan (optional)", ["None"] + list(plans.keys()))
    base_plan_data = plans.get(base_plan_choice) if base_plan_choice != "None" else None
    num_stages = st.number_input(
        "Number of Stages", min_value=1, max_value=10,
        value=len(base_plan_data["stages"]) if base_plan_data else 1, step=1
    )

    new_plan_stages = []
    for i in range(num_stages):
        st.markdown(f"**Stage {i+1}**")
        stage_title = st.text_input(
            f"Stage {i+1} Title",
            value=(base_plan_data["stages"][i]["title"] if base_plan_data and i < len(base_plan_data["stages"]) else ""),
            key=f"stage_title_{i}"
        )
        num_steps = st.number_input(
            f"Number of Steps in Stage {i+1}",
            min_value=1, max_value=10,
            value=(len(base_plan_data["stages"][i]["steps"]) if base_plan_data and i < len(base_plan_data["stages"]) else 1),
            step=1, key=f"num_steps_{i}"
        )

        steps = []
        for j in range(num_steps):
            st.markdown(f"Step {j+1}")
            step_title = st.text_input(
                f"Step {j+1} Title",
                value=(base_plan_data["stages"][i]["steps"][j]["title"] if base_plan_data and i < len(base_plan_data["stages"]) and j < len(base_plan_data["stages"][i]["steps"]) else ""),
                key=f"step_title_{i}_{j}"
            )
            step_goal = st.text_area(
                f"Step {j+1} Goal",
                value=(base_plan_data["stages"][i]["steps"][j]["goal"] if base_plan_data and i < len(base_plan_data["stages"]) and j < len(base_plan_data["stages"][i]["steps"]) else ""),
                key=f"step_goal_{i}_{j}"
            )
            steps.append({"title": step_title, "goal": step_goal, "why": "", "how": [], "kpis": [], "deliverables": [], "toolbox": {}})
        new_plan_stages.append({"title": stage_title, "steps": steps, "description": ""})

    if st.button("Submit Plan"):
        if not new_plan_title:
            st.warning("Please enter a plan title")
        else:
            filename = slugify(new_plan_title) + ".json"
            new_plan = {"title": new_plan_title, "intro": "", "stages": new_plan_stages}
            if save_plan_to_github(filename, new_plan, commit_msg=f"Add plan {new_plan_title}"):
                st.success(f"Plan '{new_plan_title}' submitted successfully!")

# --- Sidebar: Select existing plan ---
st.sidebar.markdown("---")
st.sidebar.title("📚 Marketing Masterplans")
plan_title = st.sidebar.selectbox("Plan", list(plans.keys()), index=0)
plan = plans[plan_title]
plan_file = plan_files[plan_title]

st.sidebar.markdown("---")
admin = st.sidebar.checkbox("🛠️ Admin Mode", help="Enable editing of the current step")

# --- Stage & Step Selection ---
stage_titles = [s["title"] for s in plan.get("stages", [])]
stage_title = st.sidebar.selectbox("Stage", stage_titles, index=0)
stage = get_stage(plan, stage_title=stage_title)

step_titles = [s["title"] for s in stage.get("steps", [])]
step_title = st.sidebar.selectbox("Step", step_titles, index=0)
step = get_step(stage, step_title=step_title)

# --- Main Display ---
st.markdown(f"# {plan.get('title')}")
if plan.get("intro"):
    with st.expander("How to use this playbook", expanded=True):
        st.markdown(plan["intro"])

st.write("---")
left, right = st.columns([3,2])

with left:
    st.markdown(f"## {stage['title']}")
    if stage.get("description"):
        st.info(stage["description"])

    st.markdown(f"### {step['title']}")
    if admin:
        step["goal"] = st.text_area("Goal", value=step.get("goal", ""))
        step["why"] = st.text_area("Why it matters", value=step.get("why", ""))
        step["how"] = st.text_area("How / SOP (one per line)", value="\n".join(step.get("how", []))).splitlines()
        step["kpis"] = st.text_area("KPIs (one per line)", value="\n".join(step.get("kpis", []))).splitlines()
        step["deliverables"] = st.text_area("Deliverables (one per line)", value="\n".join(step.get("deliverables", []))).splitlines()
        if st.button("Save Step"):
            if save_plan_to_github(plan_file, plan, commit_msg=f"Update step {step['title']}"):
                st.success("Step saved successfully!")
    else:
        if step.get("goal"): st.markdown(f"**Goal:** {step['goal']}")
        if step.get("why"): st.markdown(f"**Why it matters:** {step['why']}")
        if step.get("how"):
            st.subheader("SOP / How")
            st.markdown(md_list(step["how"]))
        if step.get("kpis"):
            st.subheader("KPIs")
            st.markdown(md_list(step["kpis"]))
        if step.get("deliverables"):
            st.subheader("Deliverables")
            st.markdown(md_list(step["deliverables"]))

    render_toolbox(step.get("toolbox"))

with right:
    st.markdown("### Stages")
    for s in plan.get("stages", []):
        st.markdown(f"- {s['title']}")

