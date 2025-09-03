import os, json, requests
from urllib.parse import urlparse
import streamlit as st
from slugify import slugify
import base64

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

# --- Hardcoded plan filenames ---
PLAN_FILES = {
    "B2C": "b2c.json",
    "Product-Based": "product.json",
    "B2B": "b2b.json",
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

def save_plan_to_github(filename, data, commit_msg="Add new plan via Streamlit"):
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

# --- Load existing plans ---
plans = {}
for key, file in PLAN_FILES.items():
    plans[key] = load_plan_from_github(file)

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
            f"Number of Steps in Stage {i+1}", min_value=1, max_value=10,
            value=(len(base_plan_data["stages"][i]["steps"]) if base_plan_data and i < len(base_plan_data["stages"]) else 1),
            key=f"num_steps_{i}"
        )
        
        steps = []
        for j in range(num_steps):
            st.markdown(f"Step {j+1}")
            step_title = st.text_input(
                f"Step {j+1} Title",
                key=f"step_title_{i}_{j}",
                value=(base_plan_data["stages"][i]["steps"][j]["title"] if base_plan_data and i < len(base_plan_data["stages"]) and j < len(base_plan_data["stages"][i]["steps"]) else "")
            )
            step_goal = st.text_area(
                f"Step {j+1} Goal",
                key=f"step_goal_{i}_{j}",
                value=(base_plan_data["stages"][i]["steps"][j]["goal"] if base_plan_data and i < len(base_plan_data["stages"]) and j < len(base_plan_data["stages"][i]["steps"]) else "")
            )
            step_why = st.text_area(
                f"Step {j+1} Why",
                key=f"step_why_{i}_{j}",
                value=(base_plan_data["stages"][i]["steps"][j]["why"] if base_plan_data and i < len(base_plan_data["stages"]) and j < len(base_plan_data["stages"][i]["steps"]) else "")
            )
            step_how = st.text_area(
                f"Step {j+1} SOP / How (one per line)",
                key=f"step_how_{i}_{j}",
                value="\n".join(base_plan_data["stages"][i]["steps"][j]["how"]) if base_plan_data and i < len(base_plan_data["stages"]) and j < len(base_plan_data["stages"][i]["steps"]) else ""
            )
            step_kpis = st.text_area(
                f"Step {j+1} KPIs (one per line)",
                key=f"step_kpis_{i}_{j}",
                value="\n".join(base_plan_data["stages"][i]["steps"][j]["kpis"]) if base_plan_data and i < len(base_plan_data["stages"]) and j < len(base_plan_data["stages"][i]["steps"]) else ""
            )
            step_deliverables = st.text_area(
                f"Step {j+1} Deliverables (one per line)",
                key=f"step_deliverables_{i}_{j}",
                value="\n".join(base_plan_data["stages"][i]["steps"][j]["deliverables"]) if base_plan_data and i < len(base_plan_data["stages"]) and j < len(base_plan_data["stages"][i]["steps"]) else ""
            )

            tb_high = st.text_area(
                f"High Priority Tools (name - url, one per line)",
                key=f"tb_high_{i}_{j}",
                value="\n".join([f"{t['name']} - {t['url']}" for t in base_plan_data["stages"][i]["steps"][j].get("toolbox", {}).get("high_priority", [])]) if base_plan_data and i < len(base_plan_data["stages"]) and j < len(base_plan_data["stages"][i]["steps"]) else ""
            )
            tb_low = st.text_area(
                f"Low Priority Tools (name - url, one per line)",
                key=f"tb_low_{i}_{j}",
                value="\n".join([f"{t['name']} - {t['url']}" for t in base_plan_data["stages"][i]["steps"][j].get("toolbox", {}).get("low_priority", [])]) if base_plan_data and i < len(base_plan_data["stages"]) and j < len(base_plan_data["stages"][i]["steps"]) else ""
            )

            def parse_tools(text):
                tools = []
                for ln in text.splitlines():
                    if not ln.strip(): continue
                    if " - " in ln:
                        name, url = ln.split(" - ",1)
                    else:
                        name, url = ln, ln
                    tools.append({"name": name.strip(), "url": url.strip()})
                return tools

            steps.append({
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
            })
        new_plan_stages.append({
            "title": stage_title,
            "steps": steps,
            "description": ""
        })

    if st.button("Submit Plan"):
        if not new_plan_title:
            st.warning("Please enter a plan title")
        else:
            filename = slugify(new_plan_title) + ".json"
            new_plan = {
                "title": new_plan_title,
                "intro": "",
                "stages": new_plan_stages
            }
            success = save_plan_to_github(filename, new_plan)
            if success:
                st.success(f"Plan '{new_plan_title}' submitted successfully! Check GitHub.")
                # --- Reload plans dynamically ---
                plans[slugify(new_plan_title)] = new_plan

# --- Select existing plan ---
st.sidebar.markdown("---")
st.sidebar.title("📚 Marketing Plans")
plan_key = st.sidebar.selectbox("Choose a Plan", list(plans.keys()))
plan = plans[plan_key]

# --- Display Plan ---
st.title(plan.get("title", "Marketing Plan"))
st.markdown(plan.get("intro",""))

for stage in plan.get("stages", []):
    st.header(stage.get("title",""))
    if stage.get("description"):
        st.markdown(stage["description"])
    for step in stage.get("steps", []):
        st.subheader(step.get("title",""))
        st.markdown(f"**Goal:** {step.get('goal','')}")
        st.markdown(f"**Why:** {step.get('why','')}")
        if step.get("how"):
            st.markdown("**SOP / How:**\n" + md_list(step["how"]))
        if step.get("kpis"):
            st.markdown("**KPIs:**\n" + md_list(step["kpis"]))
        if step.get("deliverables"):
            st.markdown("**Deliverables:**\n" + md_list(step["deliverables"]))
        render_toolbox(step.get("toolbox"))
