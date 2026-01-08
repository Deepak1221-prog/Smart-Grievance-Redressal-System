import streamlit as st
import requests
from dotenv import load_dotenv
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

load_dotenv()

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Page configuration
st.set_page_config(
    page_title="SGRS - Smart Grievance Redressal System",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        color: #721c24;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user' not in st.session_state:
    st.session_state.user = None

def get_headers():
    """Get authorization headers"""
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}

def login_user(email, password):
    """Login user and store token"""
    try:
        response = requests.post(
            f"{API_URL}/api/auth/login",
            json={"email": email, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.token = data['access_token']
            
            # Get user info
            headers = get_headers()
            user_response = requests.get(f"{API_URL}/api/auth/me", headers=headers)
            if user_response.status_code == 200:
                st.session_state.user = user_response.json()
            return True
        return False
    except Exception as e:
        st.error(f"Login error: {e}")
        return False

def register_user(email, password, full_name, phone, ward, address, role):
    """Register a new user"""
    try:
        # Debug: Show what we're sending
        payload = {
            "email": email,
            "password": password,
            "full_name": full_name,
            "phone": phone if phone else "",
            "ward": ward if ward else "",
            "address": address if address else "",
            "role": role
        }
        
        print(f"Registering user: {email}")  # Debug
        print(f"Payload: {payload}")  # Debug
        
        response = requests.post(
            f"{API_URL}/api/auth/register",
            json=payload,
            timeout=10
        )
        
        print(f"Response status: {response.status_code}")  # Debug
        print(f"Response body: {response.text}")  # Debug
        
        if response.status_code == 201:
            st.success("✅ Registration successful! Please login.")
            return True
        else:
            error_msg = response.json().get('detail', 'Unknown error')
            st.error(f"❌ Registration failed: {error_msg}")
            return False
            
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to backend. Is it running on http://localhost:8000?")
        return False
    except requests.exceptions.Timeout:
        st.error("❌ Request timeout. Backend is not responding.")
        return False
    except Exception as e:
        st.error(f"❌ Registration error: {str(e)}")
        print(f"Exception: {e}")  # Debug
        return False



def logout():
    """Logout user"""
    st.session_state.token = None
    st.session_state.user = None
    st.rerun()

def create_complaint(title, description, category, ward, location, is_anonymous):
    """Create new complaint"""
    try:
        response = requests.post(
            f"{API_URL}/api/complaints/",
            headers=get_headers(),
            json={
                "title": title,
                "description": description,
                "category": category,
                "ward": ward,
                "location": location,
                "is_anonymous": is_anonymous
            }
        )
        return response.status_code == 201, response.json() if response.status_code == 201 else None
    except Exception as e:
        st.error(f"Error creating complaint: {e}")
        return False, None

def get_complaints(status=None, category=None):
    """Get complaints list"""
    try:
        params = {}
        if status:
            params['status'] = status
        if category:
            params['category'] = category
        
        response = requests.get(
            f"{API_URL}/api/complaints/",
            headers=get_headers(),
            params=params
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching complaints: {e}")
        return []

def get_complaint_details(complaint_id):
    """Get single complaint details"""
    try:
        response = requests.get(
            f"{API_URL}/api/complaints/{complaint_id}",
            headers=get_headers()
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching complaint details: {e}")
        return None

def update_complaint(complaint_id, status=None, assigned_to=None):
    """Update complaint"""
    try:
        update_data = {}
        if status:
            update_data['status'] = status
        if assigned_to:
            update_data['assigned_to'] = assigned_to
        
        response = requests.put(
            f"{API_URL}/api/complaints/{complaint_id}",
            headers=get_headers(),
            json=update_data
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error updating complaint: {e}")
        return False

def add_comment(complaint_id, comment_text, is_internal=False):
    """Add comment to complaint"""
    try:
        response = requests.post(
            f"{API_URL}/api/complaints/{complaint_id}/comments",
            headers=get_headers(),
            json={"comment_text": comment_text, "is_internal": is_internal}
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error adding comment: {e}")
        return False

def submit_feedback(complaint_id, rating, feedback_text, was_resolved):
    """Submit feedback for complaint"""
    try:
        response = requests.post(
            f"{API_URL}/api/complaints/{complaint_id}/feedback",
            headers=get_headers(),
            json={
                "rating": rating,
                "feedback_text": feedback_text,
                "was_resolved": was_resolved
            }
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error submitting feedback: {e}")
        return False

def get_analytics_overview():
    """Get overview analytics"""
    try:
        response = requests.get(
            f"{API_URL}/api/analytics/overview",
            headers=get_headers()
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching analytics: {e}")
        return None

def get_category_analytics():
    """Get category analytics"""
    try:
        response = requests.get(
            f"{API_URL}/api/analytics/category",
            headers=get_headers()
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching category analytics: {e}")
        return None

# ========== PAGE FUNCTIONS ==========

def show_login_page():
    """Display login/register page"""
    st.markdown("<h1 class='main-header'>🏛️ Smart Grievance Redressal System</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login to Your Account")
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if email and password:
                    if login_user(email, password):
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
                else:
                    st.warning("Please fill all fields")
    
    with tab2:
        st.subheader("Create New Account")
        with st.form("register_form"):
            reg_email = st.text_input("Email", key="reg_email")
            reg_password = st.text_input("Password", type="password", key="reg_password")
            reg_full_name = st.text_input("Full Name", key="reg_name")
            reg_phone = st.text_input("Phone Number", key="reg_phone")
            reg_ward = st.text_input("Ward", key="reg_ward")
            reg_address = st.text_area("Address", key="reg_address")
            reg_role = st.selectbox("Role", ["citizen", "officer", "admin", "ngo"], key="reg_role")
            submit_reg = st.form_submit_button("Register")
            
            if submit_reg:
                if reg_email and reg_password and reg_full_name:
                    if register_user(reg_email, reg_password, reg_full_name, reg_phone, reg_ward, reg_address, reg_role):
                        st.success("Registration successful! Please login.")
                    else:
                        st.error("Registration failed")
                else:
                    st.warning("Please fill required fields")

def show_dashboard():
    """Display main dashboard"""
    st.markdown("<h1 class='main-header'>🏛️ Dashboard</h1>", unsafe_allow_html=True)
    
    # Analytics
    analytics = get_analytics_overview()
    if analytics:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Complaints", analytics.get('total_complaints', 0))
        with col2:
            st.metric("Resolved", analytics.get('resolved_complaints', 0))
        with col3:
            st.metric("Resolution Rate", f"{analytics.get('resolution_rate', 0)}%")
        with col4:
            st.metric("Avg Resolution Days", f"{analytics.get('average_resolution_days', 0):.1f}")
        
        # Status distribution
        if analytics.get('status_distribution'):
            st.subheader("Complaints by Status")
            status_df = pd.DataFrame(list(analytics['status_distribution'].items()), 
                                    columns=['Status', 'Count'])
            fig = px.bar(status_df, x='Status', y='Count', color='Status')
            st.plotly_chart(fig, use_container_width=True)
    
    # Recent complaints
    st.subheader("Recent Complaints")
    complaints = get_complaints()
    if complaints:
        for complaint in complaints[:5]:
            with st.expander(f"{complaint['complaint_id']} - {complaint['title']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Status:** {complaint['status']}")
                    st.write(f"**Category:** {complaint['category']}")
                    st.write(f"**Priority:** {complaint['priority']}")
                with col2:
                    st.write(f"**Ward:** {complaint['ward']}")
                    st.write(f"**Created:** {complaint['created_at'][:10]}")
                st.write(f"**Description:** {complaint['description']}")

def show_create_complaint():
    """Display create complaint page"""
    st.subheader("File New Complaint")
    
    with st.form("complaint_form"):
        title = st.text_input("Title", max_chars=200)
        description = st.text_area("Description", height=150)
        
        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox("Category", [
                "water_supply", "garbage_collection", "street_lights",
                "roads", "drainage", "health_services", "other"
            ])
            ward = st.text_input("Ward")
        with col2:
            location = st.text_input("Location (Optional)")
            is_anonymous = st.checkbox("File Anonymously")
        
        submit = st.form_submit_button("Submit Complaint")
        
        if submit:
            if title and description and ward:
                success, complaint_data = create_complaint(
                    title, description, category, ward, location, is_anonymous
                )
                if success:
                    st.success(f"Complaint filed successfully! ID: {complaint_data['complaint_id']}")
                    st.balloons()
                else:
                    st.error("Failed to file complaint")
            else:
                st.warning("Please fill all required fields")

def show_my_complaints():
    """Display user's complaints"""
    st.subheader("My Complaints")
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Filter by Status", 
            ["All", "submitted", "under_review", "in_progress", "resolved", "closed"])
    with col2:
        category_filter = st.selectbox("Filter by Category",
            ["All", "water_supply", "garbage_collection", "street_lights", "roads", "drainage", "health_services", "other"])
    
    # Get complaints
    status = None if status_filter == "All" else status_filter
    category = None if category_filter == "All" else category_filter
    complaints = get_complaints(status=status, category=category)
    
    if complaints:
        for complaint in complaints:
            with st.expander(f"{complaint['complaint_id']} - {complaint['title']} [{complaint['status']}]"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Status:** {complaint['status']}")
                    st.write(f"**Category:** {complaint['category']}")
                with col2:
                    st.write(f"**Priority:** {complaint['priority']}")
                    st.write(f"**Ward:** {complaint['ward']}")
                with col3:
                    st.write(f"**Created:** {complaint['created_at'][:10]}")
                    if complaint.get('resolved_at'):
                        st.write(f"**Resolved:** {complaint['resolved_at'][:10]}")
                
                st.write(f"**Description:** {complaint['description']}")
                
                # Add feedback button for resolved complaints
                if complaint['status'] in ['resolved', 'closed']:
                    with st.form(f"feedback_form_{complaint['id']}"):
                        st.write("**Provide Feedback**")
                        rating = st.slider("Rating", 1, 5, 3)
                        was_resolved = st.checkbox("Issue was resolved satisfactorily")
                        feedback_text = st.text_area("Comments")
                        
                        if st.form_submit_button("Submit Feedback"):
                            if submit_feedback(complaint['id'], rating, feedback_text, was_resolved):
                                st.success("Feedback submitted!")
                            else:
                                st.error("Failed to submit feedback")
    else:
        st.info("No complaints found")

def show_analytics():
    """Display analytics page"""
    st.subheader("Analytics Dashboard")
    
    # Overview
    analytics = get_analytics_overview()
    if analytics:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Complaints", analytics.get('total_complaints', 0),
                     delta=analytics.get('current_month_complaints', 0) - analytics.get('previous_month_complaints', 0))
        with col2:
            st.metric("Resolved", analytics.get('resolved_complaints', 0))
        with col3:
            st.metric("Resolution Rate", f"{analytics.get('resolution_rate', 0)}%")
        with col4:
            st.metric("Avg Resolution Days", f"{analytics.get('average_resolution_days', 0):.1f}")
    
    # Category analytics
    category_data = get_category_analytics()
    if category_data:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Complaints by Category")
            if category_data.get('category_counts'):
                cat_df = pd.DataFrame(list(category_data['category_counts'].items()),
                                     columns=['Category', 'Count'])
                fig = px.pie(cat_df, values='Count', names='Category', title='Category Distribution')
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Avg Resolution Time by Category")
            if category_data.get('avg_resolution_by_category'):
                res_df = pd.DataFrame(list(category_data['avg_resolution_by_category'].items()),
                                     columns=['Category', 'Days'])
                fig = px.bar(res_df, x='Category', y='Days', title='Resolution Time (Days)')
                st.plotly_chart(fig, use_container_width=True)

# ========== MAIN APP ==========

def main():
    # Check if user is logged in
    if not st.session_state.token:
        show_login_page()
    else:
        # Sidebar
        with st.sidebar:
            st.title("Navigation")
            
            # User info
            if st.session_state.user:
                st.write(f"👤 {st.session_state.user['full_name']}")
                st.write(f"📧 {st.session_state.user['email']}")
                st.write(f"🎭 Role: {st.session_state.user['role']}")
            
            st.divider()
            
            # Navigation
            page = st.radio("Go to", [
                "Dashboard",
                "File Complaint",
                "My Complaints",
                "Analytics",
                "Logout"
            ])
            
            st.divider()
            st.caption("Smart Grievance Redressal System v1.0")
        
        # Main content
        if page == "Dashboard":
            show_dashboard()
        elif page == "File Complaint":
            show_create_complaint()
        elif page == "My Complaints":
            show_my_complaints()
        elif page == "Analytics":
            show_analytics()
        elif page == "Logout":
            logout()

if __name__ == "__main__":
    main()
