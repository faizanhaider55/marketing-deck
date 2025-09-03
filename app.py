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

# --- Load existing plans dynamically from GitHub ---
def list_github_files():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_PATH}?ref={GITHUB_BRANCH}"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200:
        return [f["name"] for f in resp.json() if f["name"].endswith(".json")]
    return []

plans = {}
for file in list_github_files():
    plan_data = load_plan_from_github(file)
    if plan_data.get("title"):
        plans[plan_data["title"]] = plan_data

# --- Sidebar: Admin Mode ---
st.sidebar.markdown("---")
admin_mode = st.sidebar.checkbox("🛠 Admin Mode (Edit Existing Plans)")

# --- Select existing plan ---
st.sidebar.title("📚 Marketing Masterplans")
plan_key = st.sidebar.selectbox("Plan", list(plans.keys()), index=0)
plan = plans[plan_key]

if admin_mode:
    st.sidebar.markdown("---")
    st.sidebar.subheader("✏️ Edit Plan")

    new_title = st.text_input("Plan Title", value=plan.get("title",""))
    stages = plan.get("stages", [])
    updated_stages = []

    for i, stage in enumerate(stages):
        st.markdown(f"### Stage {i+1}")
        stage_title = st.text_input(f"Stage {i+1} Title", value=stage.get("title",""), key=f"stage_title_{i}")
        steps = stage.get("steps", [])
        updated_steps = []

        for j, step in enumerate(steps):
            st.markdown(f"#### Step {j+1}")
            step_title = st.text_input(f"Step {j+1} Title", value=step.get("title",""), key=f"step_title_{i}_{j}")
            step_goal = st.text_area(f"Step {j+1} Goal", value=step.get("goal",""), key=f"step_goal_{i}_{j}")
            step_why = st.text_area(f"Step {j+1} Why", value=step.get("why",""), key=f"step_why_{i}_{j}")
            step_how = st.text_area(f"Step {j+1} SOP / How (one per line)", value="\n".join(step.get("how",[])), key=f"step_how_{i}_{j}")
            step_kpis = st.text_area(f"Step {j+1} KPIs (one per line)", value="\n".join(step.get("kpis",[])), key=f"step_kpis_{i}_{j}")
            step_deliverables = st.text_area(f"Step {j+1} Deliverables (one per line)", value="\n".join(step.get("deliverables",[])), key=f"step_deliverables_{i}_{j}")

            tb = step.get("toolbox") or {}
            high_tools = tb.get("high_priority") or []
            high_tools = [t for t in high_tools if isinstance(t, dict) and "name" in t and "url" in t]
            tb_high_value = "\n".join([f"{t['name']} - {t['url']}" for t in high_tools])

            low_tools = tb.get("low_priority") or []
            low_tools = [t for t in low_tools if isinstance(t, dict) and "name" in t and "url" in t]
            tb_low_value = "\n".join([f"{t['name']} - {t['url']}" for t in low_tools])

            tb_high = st.text_area(f"High Priority Tools (name - url, one per line)", value=tb_high_value, key=f"tb_high_{i}_{j}")
            tb_low = st.text_area(f"Low Priority Tools (name - url, one per line)", value=tb_low_value, key=f"tb_low_{i}_{j}")

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

            updated_steps.append({
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

        updated_stages.append({
            "title": stage_title,
            "steps": updated_steps,
            "description": stage.get("description","")
        })

    if st.button("Update Plan on GitHub"):
        updated_plan = {
            "title": new_title,
            "intro": plan.get("intro",""),
            "stages": updated_stages
        }
        filename = slugify(new_title) + ".json"
        success = save_plan_to_github(filename, updated_plan, commit_msg=f"Update plan '{new_title}' via Streamlit")
        if success:
            st.success(f"Plan '{new_title}' updated successfully on GitHub!")

else:
    # --- Stage selection ---
    stage_titles = [s["title"] for s in plan.get("stages", [])]
    if not stage_titles:
        st.error("No stages found in the plan.")
        st.stop()
    stage_title = st.selectbox("Select Stage", stage_titles)
    stage = get_stage(plan, stage_title=stage_title)

    # --- Step selection ---
    step_titles = [s["title"] for s in stage.get("steps", [])]
    if not step_titles:
        st.warning("No steps found in this stage.")
        st.stop()
    step_title = st.selectbox("Select Step", step_titles)
    step = get_step(stage, step_title=step_title)

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
