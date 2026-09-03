import sqlite3
import os
import streamlit as st
from duckduckgo_search import DDGS

DB_NAME = 'partners.db'

def get_db():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('''
            CREATE TABLE IF NOT EXISTS partners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                industry TEXT,
                priority TEXT,
                status TEXT,
                notes TEXT
            )
        ''')
        conn.commit()
        
        c.execute('SELECT COUNT(*) FROM partners')
        if c.fetchone()[0] == 0:
            seed_data = [
                ("Apex Solutions", "Enterprise Software", "High", "Prospect", "Discovered via web search for SaaS integration."),
                ("Nexus Systems", "Cloud Infrastructure", "High", "Outreach Sent", "Sent initial partnership inquiry email."),
                ("Quantum Analytics", "Data & AI", "Medium", "In Discussion", "Scheduled follow-up demo call."),
                ("Vanguard Labs", "Cybersecurity", "Low", "Prospect", "Potential co-marketing partner.")
            ]
            c.executemany('''
                INSERT INTO partners (name, industry, priority, status, notes)
                VALUES (?, ?, ?, ?, ?)
            ''', seed_data)
            conn.commit()
    except sqlite3.OperationalError:
        conn.close()
        if os.path.exists(DB_NAME):
            os.remove(DB_NAME)
        return init_db()
    
    conn.close()

def reset_db():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    init_db()

# Initialize DB on startup
init_db()

# --- STREAMLIT UI ---
st.set_page_config(page_title="Partner Intelligence", page_icon="🤝", layout="wide")

st.sidebar.title("🤝 Partner Intelligence")
st.sidebar.caption("Workspace for Business Development")
st.sidebar.success("🌐 Web Discovery: DuckDuckGo\n(Free / No Key Required)")

nav = st.sidebar.radio("Navigation", ["Dashboard", "Find Partners", "All Partners", "Pipeline Board", "Manage Partners"])

st.sidebar.markdown("---")
st.sidebar.subheader("Database Management")
if st.sidebar.button("🔄 Reset / Reload Sample Data"):
    reset_db()
    st.sidebar.success("Database reset with fresh sample data!")
    st.rerun()

conn = get_db()
c = conn.cursor()

if nav == "Dashboard":
    st.title("📊 Partner Intelligence Dashboard")
    
    c.execute('SELECT COUNT(*) FROM partners')
    total_partners = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM partners WHERE priority = 'High'")
    high_priority = c.fetchone()[0]
    
    col1, col2 = st.columns(2)
    col1.metric("Total Partners in Pipeline", total_partners)
    col2.metric("High Priority Candidates", high_priority)

elif nav == "Find Partners":
    st.title("🔍 Find Partners (DuckDuckGo)")
    query = st.text_input("Enter search query", "Top B2B SaaS Startups")
    
    if st.button("Search Web"):
        with st.spinner("Searching..."):
            try:
                results = list(DDGS().text(query, max_results=5))
                for r in results:
                    st.subheader(r['title'])
                    st.write(r['body'])
                    st.caption(r['href'])
                    st.markdown("---")
            except Exception as e:
                st.error(f"Search error: {e}")

elif nav == "All Partners":
    st.title("📋 All Partners")
    c.execute('SELECT name, industry, priority, status, notes FROM partners')
    rows = c.fetchall()
    
    if rows:
        st.table([{"Name": r[0], "Industry": r[1], "Priority": r[2], "Status": r[3], "Notes": r[4]} for r in rows])
    else:
        st.info("No partners found. Use the sidebar button to load sample data.")

elif nav == "Pipeline Board":
    st.title("📌 Pipeline Board")
    c.execute('SELECT name, priority, status FROM partners')
    rows = c.fetchall()
    
    statuses = ["Prospect", "Outreach Sent", "In Discussion"]
    cols = st.columns(len(statuses))
    
    for i, s in enumerate(statuses):
        with cols[i]:
            st.subheader(s)
            matching = [r for r in rows if r[2] == s]
            for m in matching:
                st.write(f"**{m[0]}** ({m[1]} Priority)")

elif nav == "Manage Partners":
    st.title("⚙️ Manage Partners (CRUD)")
    
    tab_add, tab_edit, tab_delete = st.tabs(["➕ Add New Partner", "✏️ Edit Partner Status", "🗑️ Delete Partner"])
    
    # --- CREATE (ADD) ---
    with tab_add:
        st.subheader("Add a New Partner")
        with st.form("add_partner_form", clear_on_submit=True):
            new_name = st.text_input("Partner Name*")
            new_industry = st.text_input("Industry", "Technology")
            new_priority = st.selectbox("Priority", ["High", "Medium", "Low"])
            new_status = st.selectbox("Status", ["Prospect", "Outreach Sent", "In Discussion"])
            new_notes = st.text_area("Notes", "Initial discovery entry.")
            
            submit_add = st.form_submit_button("Add Partner")
            if submit_add:
                if new_name.strip() == "":
                    st.error("Partner Name is required!")
                else:
                    c.execute('''
                        INSERT INTO partners (name, industry, priority, status, notes)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (new_name.strip(), new_industry.strip(), new_priority, new_status, new_notes.strip()))
                    conn.commit()
                    st.success(f"Added **{new_name}** to partners!")
                    st.rerun()

    # --- UPDATE (EDIT) ---
    with tab_edit:
        st.subheader("Update Existing Partner")
        c.execute('SELECT id, name, status, notes FROM partners')
        all_partners = c.fetchall()
        
        if not all_partners:
            st.info("No partners in the database to edit.")
        else:
            partner_dict = {f"{p[1]} (ID: {p[0]})": p for p in all_partners}
            selected_label = st.selectbox("Select Partner to Edit", list(partner_dict.keys()))
            selected_partner = partner_dict[selected_label]
            
            p_id, p_name, current_status, current_notes = selected_partner
            
            status_options = ["Prospect", "Outreach Sent", "In Discussion"]
            status_index = status_options.index(current_status) if current_status in status_options else 0
            
            with st.form("edit_partner_form"):
                updated_status = st.selectbox("Pipeline Status", status_options, index=status_index)
                updated_notes = st.text_area("Notes", value=current_notes)
                
                submit_edit = st.form_submit_button("Update Partner")
                if submit_edit:
                    c.execute('''
                        UPDATE partners 
                        SET status = ?, notes = ?
                        WHERE id = ?
                    ''', (updated_status, updated_notes.strip(), p_id))
                    conn.commit()
                    st.success(f"Updated status for **{p_name}**!")
                    st.rerun()

    # --- DELETE ---
    with tab_delete:
        st.subheader("Delete Partner")
        c.execute('SELECT id, name FROM partners')
        all_partners_del = c.fetchall()
        
        if not all_partners_del:
            st.info("No partners in the database to delete.")
        else:
            partner_del_dict = {f"{p[1]} (ID: {p[0]})": p for p in all_partners_del}
            del_label = st.selectbox("Select Partner to Remove", list(partner_del_dict.keys()))
            selected_del_partner = partner_del_dict[del_label]
            
            if st.button("🚨 Permanently Delete Partner", type="primary"):
                c.execute('DELETE FROM partners WHERE id = ?', (selected_del_partner[0],))
                conn.commit()
                st.success(f"Deleted **{selected_del_partner[1]}** successfully.")
                st.rerun()

conn.close()