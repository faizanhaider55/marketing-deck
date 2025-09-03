import os
import json
from urllib.parse import urlparse
import streamlit as st
from slugify import slugify
from github import Github

st.set_page_config(page_title="Marketing Masterplans", page_icon="📚", layout="wide")

# --------------------------
# CONFIG
# --------------------------
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# Hardcoded plans
HARDCODED_PLANS = {
    "B2C": "b2c.json",
    "Product-Based": "product.json",
    "B2B": "b2b.json",
}

# Load all JSON files dynamically
def get_all_plans():
    plans = HARDCODED_PLANS.copy()
    for f in os.listdir(DATA_DIR):
        if f.endswith(".json") and f not in plans.values():
            key = os.path.splitext(f)[0]  # filename without .json
            plans[key] = f
    return plans

# --------------------------
# HELPER FUNCTIONS
# --------------------------
def load_plan(plan_key):
    path = os.path.join(DATA_DIR, PLAN_FILES[plan_key])
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_plan(plan_key, data):
    path = os.path.join(DATA_DIR, PLAN_FILES[plan_key])
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

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

# --------------------------
# DYNAMIC PLAN FILES
# --------------------------
PLAN_FILES = get_all_plans()

# --------------------------
# SIDEBAR - Add New Plan
# --------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("➕ Submit a New Plan")

with st.sidebar.expander("Add Your Own Plan"):
    new_plan_title = st.text_input("Plan Title")
    num_stages = st.number_input("Number of Stages", min_value=1, max_value=10, value=1, step=1)

    new_plan_stages = []
    for i in range(num_stages):
        st.markdown(f"**Stage {i+1}**")
        stage_title = st.text_input(f"Stage {i+1} Title", key=f"stage_title_{i}")
        num_steps = st.number_input(f"Number of Steps in Stage {i+1}", min_value=1, max_value=10, value=1, step=1, key=f"num_steps_{i}")

        steps = []
        for j in range(num_steps):
            st.markdown(f"Step {j+1}")
            step_title = st.text_input(f"Step {j+1} Title", key=f"step_title_{i}_{j}")
            step_goal = st.text_area(f"Step {j+1} Goal", key=f"step_goal_{i}_{j}")
            step_why = st.text_area(f"Step {j+1} Why", key=f"step_why_{i}_{j}")
            step_how = st.text_area(f"Step {j+1} SOP / How (one per line)", key=f"step_how_{i}_{j}")
            step_kpis = st.text_area(f"Step {j+1} KPIs (one per line)", key=f"step_kpis_{i}_{j}")
            step_deliverables = st.text_area(f"Step {j+1} Deliverables (one per line)", key=f"step_deliverables_{i}_{j}")

            tb_high = st.text_area(f"High Priority Tools (name - url, one per line)", key=f"tb_high_{i}_{j}")
            tb_low = st.text_area(f"Low Priority Tools (name - url, one per line)", key=f"tb_low_{i}_{j}")

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
            filepath = os.path.join(DATA_DIR, filename)
            if os.path.exists(filepath):
                st.warning("A plan with this title already exists. Choose a different title.")
            else:
                new_plan = {
                    "title": new_plan_title,
                    "intro": "",
                    "stages": new_plan_stages
                }
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(new_plan, f, indent=2, ensure_ascii=False)
                st.success(f"Plan '{new_plan_title}' submitted successfully!")
                st.experimental_rerun()  # Refresh app to show new plan in dropdown

# --------------------------
# SIDEBAR - Select Plan
# --------------------------
st.sidebar.markdown("---")
st.sidebar.title("📚 Marketing Masterplans")
PLAN_FILES = get_all_plans()  # refresh the list after any new plan
plan_key = st.sidebar.selectbox("Plan", list(PLAN_FILES.keys()), index=0)
plan = load_plan(plan_key)

# --------------------------
# SIDEBAR - Admin / Upload / Export
# --------------------------
st.sidebar.markdown("---")
admin = st.sidebar.toggle("🛠️ Admin Mode", help="Enable editing of the current step")
st.sidebar.markdown("---")
st.sidebar.caption("Import/Export JSON")
colA, colB = st.sidebar.columns(2)
with colA:
    if st.button("⬇️ Export", use_container_width=True):
        st.sidebar.download_button(
            "Download", 
            data=json.dumps(plan, indent=2, ensure_ascii=False), 
            file_name=f"{plan_key.lower()}.json", 
            mime="application/json",
            use_container_width=True
        )
with colB:
    uploaded = st.sidebar.file_uploader("Upload JSON", type=["json"], label_visibility="collapsed")
    if uploaded:
        try:
            new_data = json.loads(uploaded.read().decode("utf-8"))
            save_plan(plan_key, new_data)
            st.sidebar.success("Plan replaced. Reload the page.")
        except Exception as e:
            st.sidebar.error(f"Invalid JSON: {e}")

# --------------------------
# STAGE & STEP SELECTION
# --------------------------
stage_titles = [s["title"] for s in plan.get("stages", [])]
if not stage_titles:
    st.error("No stages found in the plan.")
    st.stop()

stage_title = st.sidebar.selectbox("Stage", stage_titles, index=0)
stage = get_stage(plan, stage_title=stage_title)

step_titles = [s["title"] for s in stage.get("steps", [])]
if not step_titles:
    st.error("This stage has no steps.")
    st.stop()

step_title = st.sidebar.selectbox("Step", step_titles, index=0)
step = get_step(stage, step_title=step_title)

# --------------------------
# MAIN DISPLAY
# --------------------------
st.title(f"{plan.get('title','Plan')} - {stage.get('title','Stage')} / {step.get('title','Step')}")

st.markdown(f"### Goal\n{step.get('goal','')}")
st.markdown(f"### Why\n{step.get('why','')}")
st.markdown(f"### SOP / How\n{md_list(step.get('how'))}")
st.markdown(f"### KPIs\n{md_list(step.get('kpis'))}")
st.markdown(f"### Deliverables\n{md_list(step.get('deliverables'))}")

render_toolbox(step.get("toolbox"))
