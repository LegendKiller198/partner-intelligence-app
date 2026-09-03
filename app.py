import sqlite3
import streamlit as st
from duckduckgo_search import DDGS

# --- DATABASE SETUP & SEEDING ---
DB_NAME = 'partners.db'

def get_db():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_db()
    c = conn.cursor()
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
    
    # Auto-populate seed data if empty
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
    conn.close()

def reset_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS partners')
    conn.commit()
    conn.close()
    init_db()

# Initialize DB on load
init_db()

# --- STREAMLIT UI ---
st.set_page_config(page_title="Partner Intelligence", page_icon="🤝", layout="wide")

# Sidebar Navigation
st.sidebar.title("🤝 Partner Intelligence")
st.sidebar.caption("Workspace for Business Development")

# Web Discovery Status Indicator
st.sidebar.success("🌐 Web Discovery: DuckDuckGo\n(Free / No Key Required)")

nav = st.sidebar.radio("Navigation", ["Dashboard", "Find Partners", "All Partners", "Pipeline Board"])

st.sidebar.markdown("---")
st.sidebar.subheader("Database Management")
if st.sidebar.button("🔄 Reset / Reload Sample Data"):
    reset_db()
    st.sidebar.success("Database reset with fresh sample data!")
    st.rerun()

# --- PAGES ---
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
    query = st.text_input("Enter search query (e.g., 'Top AI Startups in Healthcare')", "Top B2B SaaS Startups")
    
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
        st.info("No partners found. Use the sidebar to reload sample data!")

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
                st.card if hasattr(st, "card") else st.write(f"**{m[0]}** ({m[1]} Priority)")

conn.close()