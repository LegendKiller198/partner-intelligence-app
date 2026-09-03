import streamlit as st
import sqlite3
from duckduckgo_search import DDGS

# --- DATABASE SETUP ---
conn = sqlite3.connect('partners.db', check_same_thread=False)
c = conn.cursor()

c.execute('''
    CREATE TABLE IF NOT EXISTS partners (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT UNIQUE,
        industry TEXT,
        target_audience TEXT,
        partnership_type TEXT,
        status TEXT DEFAULT 'Not Contacted',
        priority TEXT DEFAULT 'Medium',
        calculated_score INTEGER DEFAULT 50,
        notes TEXT
    )
''')
conn.commit()

# --- STREAMLIT UI SETUP ---
st.set_page_config(page_title="Partner Intelligence Dashboard", layout="wide")

st.sidebar.title("🤝 Partner Intelligence")
st.sidebar.caption("Workspace for Business Development")
st.sidebar.success("🌐 Web Discovery: DuckDuckGo (Free / No Key Required)")

nav = st.sidebar.radio("Navigation", ["Dashboard", "Find Partners", "All Partners", "Pipeline Board"])

# --- NAVIGATION ROUTING ---
if nav == "Dashboard":
    st.title("📊 Partner Intelligence Dashboard")
    
    c.execute("SELECT COUNT(*) FROM partners")
    total_partners = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM partners WHERE priority = 'High'")
    high_priority = c.fetchone()[0]
    
    col1, col2 = st.columns(2)
    col1.metric("Total Partners in Pipeline", total_partners)
    col2.metric("High Priority Candidates", high_priority)

elif nav == "Find Partners":
    st.title("⌕ Free Live Web Partner Discovery")
    st.caption("Discover real companies live from DuckDuckGo without API keys.")

    industry = st.text_input("Target Industry", "EdTech")
    audience = st.text_input("Target Audience", "Data Science Students")
    p_type = st.selectbox("Partnership Type", ["Co-branding / Joint Certifications", "Content Licensing", "Referral"])

    if st.button("Run Company Discovery"):
        query = f"top companies in {industry} for {audience}"
        st.info(f"Searching DuckDuckGo live for: *{query}*...")
        
        try:
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=5):
                    results.append(r)
            
            if results:
                st.subheader("Discovered Web Results")
                for item in results:
                    title = item.get('title', 'Unknown Title')
                    link = item.get('href', '#')
                    snippet = item.get('body', '')

                    with st.expander(f"🌐 {title}"):
                        st.write(f"**URL:** {link}")
                        st.write(f"**Snippet:** {snippet}")
                        
                        comp_name = title.split("-")[0].split("|")[0].strip()
                        
                        if st.button(f"Add '{comp_name}' to Pipeline", key=link):
                            try:
                                c.execute('''
                                    INSERT INTO partners (company_name, industry, target_audience, partnership_type, notes)
                                    VALUES (?, ?, ?, ?, ?)
                                ''', (comp_name, industry, audience, p_type, snippet[:150] + "..."))
                                conn.commit()
                                st.success(f"Added {comp_name} to database!")
                            except sqlite3.IntegrityError:
                                st.warning(f"{comp_name} is already in your database.")
            else:
                st.warning("No live search results found. Try broadening your keywords.")
                
        except Exception as e:
            st.error(f"Error executing web search: {e}")

elif nav == "All Partners":
    st.title("📋 All Saved Partners")
    c.execute("SELECT company_name, industry, target_audience, status, priority FROM partners")
    data = c.fetchall()
    if data:
        st.table(data)
    else:
        st.info("No partners saved yet. Go to 'Find Partners' to discover and add some!")

elif nav == "Pipeline Board":
    st.title("📌 Pipeline Board")
    c.execute("SELECT id, company_name, status FROM partners")
    partners = c.fetchall()
    for p_id, name, status in partners:
        col1, col2 = st.columns([3, 1])
        col1.write(f"**{name}**")
        new_status = col2.selectbox("Status", ["Not Contacted", "Contacted", "Meeting", "Closed"], index=["Not Contacted", "Contacted", "Meeting", "Closed"].index(status), key=p_id)
        if new_status != status:
            c.execute("UPDATE partners SET status = ? WHERE id = ?", (new_status, p_id))
            conn.commit()
            st.rerun()