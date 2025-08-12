
import os, json, re
from urllib.parse import urlparse
import streamlit as st
from slugify import slugify

st.set_page_config(page_title="Marketing Masterplans", page_icon="📚", layout="wide")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
PLAN_FILES = {
    "B2C": "b2c.json",
    "Product-Based": "product.json",
    "B2B": "b2b.json",
}

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

def render_toolbox(tools):
    if not tools:
        return
    st.subheader("🔧 Toolbox")
    cols = st.columns(4)
    for i, t in enumerate(tools):
        with cols[i % 4]:
            logo = clearbit_logo(t.get("url", ""))
            if logo:
                st.image(logo, use_column_width=True)
            name = t.get("name","Tool")
            url = t.get("url","#")
            st.markdown(f"[{name}]({url})", unsafe_allow_html=True)

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

st.sidebar.title("📚 Marketing Masterplans")
plan_key = st.sidebar.selectbox("Plan", list(PLAN_FILES.keys()), index=0)
plan = load_plan(plan_key)

st.sidebar.markdown("---")
admin = st.sidebar.toggle("🛠️ Admin Mode", help="Enable editing of the current step")
st.sidebar.markdown("---")
st.sidebar.caption("Import/Export JSON")
colA, colB = st.sidebar.columns(2)
with colA:
    if st.button("⬇️ Export", use_container_width=True):
        st.sidebar.download_button("Download", data=json.dumps(plan, indent=2, ensure_ascii=False), file_name=f"{plan_key.lower()}.json", mime="application/json", use_container_width=True)
with colB:
    uploaded = st.sidebar.file_uploader("Upload JSON", type=["json"], label_visibility="collapsed")
    if uploaded:
        try:
            new_data = json.loads(uploaded.read().decode("utf-8"))
            save_plan(plan_key, new_data)
            st.sidebar.success("Plan replaced. Reload the page.")
        except Exception as e:
            st.sidebar.error(f"Invalid JSON: {e}")

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

st.markdown(f"### {plan.get('title', plan_key)}")
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

    if step.get("goal"):
        st.markdown(f"**Goal:** {step['goal']}")

    if step.get("why"):
        st.markdown(f"**Why it matters:** {step['why']}")

    if step.get("how"):
        st.subheader("SOP / How")
        st.markdown(md_list(step["how"]))

    if step.get("kpis"):
        st.subheader("KPIs")
        st.markdown(md_list(step["kpis"]))

    if step.get("deliverables"):
        st.subheader("Deliverables")
        st.markdown(md_list(step["deliverables"]))

with right:
    render_toolbox(step.get("toolbox", []))

if admin:
    st.write("---")
    st.subheader("✍️ Edit Current Step")
    with st.form("edit_step"):
        title = st.text_input("Title", step.get("title",""))
        goal = st.text_area("Goal", step.get("goal",""))
        why = st.text_area("Why it matters", step.get("why",""))
        how_text = st.text_area("SOP / How (one item per line)", "\n".join(step.get("how", [])))
        kpis_text = st.text_area("KPIs (one per line)", "\n".join(step.get("kpis", [])))
        deliv_text = st.text_area("Deliverables (one per line)", "\n".join(step.get("deliverables", [])))
        tb_text = st.text_area("Toolbox (Format: Name - https://...)",
                               "\n".join([f"{t.get('name','')} - {t.get('url','')}" for t in step.get('toolbox', [])]))
        submitted = st.form_submit_button("Save Step")
        if submitted:
            step["title"] = title
            step["goal"] = goal
            step["why"] = why
            step["how"] = [ln.strip() for ln in how_text.splitlines() if ln.strip()]
            step["kpis"] = [ln.strip() for ln in kpis_text.splitlines() if ln.strip()]
            step["deliverables"] = [ln.strip() for ln in deliv_text.splitlines() if ln.strip()]
            tools = []
            for ln in tb_text.splitlines():
                if not ln.strip(): continue
                if " - " in ln:
                    name, url = ln.split(" - ", 1)
                elif "|" in ln:
                    name, url = ln.split("|", 1)
                else:
                    name, url = ln, ln
                tools.append({"name": name.strip(), "url": url.strip()})
            step["toolbox"] = tools
            save_plan(plan_key, plan)
            st.success("Saved. Switch steps or reload to see updated logos.")
