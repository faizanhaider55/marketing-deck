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

def list_github_files():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_PATH}?ref={GITHUB_BRANCH}"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200:
        return [f["name"] for f in resp.json() if f["name"].endswith(".json")]
    return []

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
                name = t.get("name","Tool")
                url = t.get("url","#")
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

def md_list(items):
    return "\n".join([f"- {it}" for it in items]) if items else ""

def get_stage(plan, stage_id=None, stage_title=None):
    for s in plan.get("stages", []):
        if (stage_id and s.get("id")==stage_id) or (stage_title and s.get("title")==stage_title):
            return s
    return None

def get_step(stage, step_id=None, step_title=None):
    for s in stage.get("steps", []):
        if (step_id and s.get("id")==step_id) or (step_title and s.get("title")==step_title):
            return s
    return None

# --- Load plans from GitHub ---
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
    base_plan_choice = st.selectbox("Import from existing plan (optional)", ["None"] + list(plans.keys()))
    
    base_plan_data = plans.get(base_plan_choice) if base_plan_choice != "None" else None
    num_stages = st.number_input("Number of Stages", min_value=1, max_value=10, value=len(base_plan_data["stages"]) if base_plan_data else 1, step=1)
    
    new_plan_stages = []
    for i in range(num_stages):
        st.markdown(f"**Stage {i+1}**")
        stage_title = st.text_input(f"Stage {i+1} Title", value=(base_plan_data["stages"][i]["title"] if base_plan_data and i < len(base_plan_data["stages"]) else ""), key=f"stage_title_{i}")
        num_steps = st.number_input(f"Number of Steps in Stage {i+1}", min_value=1, max_value=10, value=(len(base_plan_data["stages"][i]["steps"]) if base_plan_data and i < len(base_plan_data["stages"]) else 1), step=1, key=f"num_steps_{i}")
        
        steps = []
        for j in range(num_steps):
            st.markdown(f"Step {j+1}")
            step_title = st.text_input(f"Step {j+1} Title", value=(base_plan_data["stages"][i]["steps"][j]["title"] if base_plan_data and i < len(base_plan_data["stages"]) and j < len(base_plan_data["stages"][i]["steps"]) else ""), key=f"step_title_{i}_{j}")
            step_goal = st.text_area(f"Step {j+1} Goal", value=(base_plan_data["stages"][i]["steps"][j]["goal"] if base_plan_data and i < len(base_plan_data["stages"]) and j < len(base_plan_data["stages"][i]["steps"]) else ""), key=f"step_goal_{i}_{j}")
            step_why = st.text_area(f"Step {j+1} Why", value=(base_plan_data["stages"][i]["steps"][j]["why"] if base_plan_data and i < len(base_plan_data["stages"]) and j < len(base_plan_data["stages"][i]["steps"]) else ""), key=f"step_why_{i}_{j}")
            step_how = st.text_area(f"Step {j+1} SOP / How (one per line)", value="\n".join(base_plan_data["stages"][i]["steps"][j]["how"]) if base_plan_data and i < len(base_plan_data["stages"]) and j < len(base_plan_data["stages"][i]["steps"]) else "", key=f"step_how_{i}_{j}")
            step_kpis = st.text_area(f"Step {j+1} KPIs (one per line)", value="\n".join(base_plan_data["stages"][i]["steps"][j]["kpis"]) if base_plan_data and i < len(base_plan_data["stages"]) and j < len(base_plan_data["stages"][i]["steps"]) else "", key=f"step_kpis_{i}_{j}")
            step_deliverables = st.text_area(f"Step {j+1} Deliverables (one per line)", value="\n".join(base_plan_data["stages"][i]["steps"][j]["deliverables"]) if base_plan_data and i < len(base_plan_data["stages"]) and j < len(base_plan_data["stages"][i]["steps"]) else "", key=f"step_deliverables_{i}_{j}")

            # Toolbox
            tb_high = st.text_area(f"High Priority Tools (name - url, one per line)", value="\n".join([f"{t['name']} - {t['url']}" for t in (base_plan_data["stages"][i]["steps"][j]["toolbox"].get("high_priority", []) if base_plan_data and i < len(base_plan_data["stages"]) and j < len(base_plan_data["stages"][i]["steps"]) else [])]), key=f"tb_high_{i}_{j}")
            tb_low = st.text_area(f"Low Priority Tools (name - url, one per line)", value="\n".join([f"{t['name']} - {t['url']}" for t in (base_plan_data["stages"][i]["steps"][j]["toolbox"].get("low_priority", []) if base_plan_data and i < len(base_plan_data["stages"]) and j < len(base_plan_data["stages"][i]["steps"]) else [])]), key=f"tb_low_{i}_{j}")

            def parse_tools(text):
                tools = []
                for ln in text.splitlines():
                    if not ln.strip(): continue
                    if " - " in ln:
                        name, url = ln.split(" - ", 1)
                        tools.append({"name": name.strip(), "url": url.strip()})
                return tools

            steps.append({
                "title": step_title,
                "goal": step_goal,
                "why": step_why,
                "how": [h for h in step_how.splitlines() if h.strip()],
                "kpis": [k for k in step_kpis.splitlines() if k.strip()],
                "deliverables": [d for d in step_deliverables.splitlines() if d.strip()],
                "toolbox": {
                    "high_priority": parse_tools(tb_high),
                    "low_priority": parse_tools(tb_low)
                }
            })
        new_plan_stages.append({
            "title": stage_title,
            "steps": steps
        })
    
    if st.button("Save New Plan"):
        if not new_plan_title:
            st.error("Plan title is required")
        else:
            new_plan_data = {"title": new_plan_title, "stages": new_plan_stages}
            filename = f"{slugify(new_plan_title)}.json"
            if save_plan_to_github(filename, new_plan_data, commit_msg=f"Add/Update {new_plan_title}"):
                st.success(f"Plan '{new_plan_title}' saved to GitHub!")
                plans[new_plan_title] = new_plan_data

# --- Main App ---
st.title("📚 Marketing Masterplans")
plan_choice = st.selectbox("Choose a Plan", ["Select"] + list(plans.keys()))
if plan_choice != "Select":
    plan_data = plans[plan_choice]
    st.markdown(f"# {plan_data['title']}")
    for stage in plan_data.get("stages", []):
        st.markdown(f"## 🏁 {stage['title']}")
        for step in stage.get("steps", []):
            st.markdown(f"### {step['title']}")
            if step.get("goal"): st.markdown(f"**Goal:** {step['goal']}")
            if step.get("why"): st.markdown(f"**Why:** {step['why']}")
            if step.get("how"): st.markdown(f"**How:**\n{md_list(step['how'])}")
            if step.get("kpis"): st.markdown(f"**KPIs:**\n{md_list(step['kpis'])}")
            if step.get("deliverables"): st.markdown(f"**Deliverables:**\n{md_list(step['deliverables'])}")
            render_toolbox(step.get("toolbox"))
