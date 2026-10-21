
import streamlit as st

st.set_page_config(
    page_title="Movie Recommendation Portal",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 Movie Recommendation Portal")

st.write(
    "Welcome to our Movie Recommendation Portal. "
    "Explore movie data, manage user profiles, and analyze ratings."
)

st.subheader("What can you do here?")

col1, col2, col3 = st.columns(3)

with col1:
    st.write("### 👤 Users")
    st.write(
        "Manage user records, search and filter users, "
        "view user statistics, and export reports."
    )

with col2:
    st.write("### 🎞️ Movies")
    st.write(
        "Browse movies and explore movie information and genres."
    )

with col3:
    st.write("### ⭐ Ratings")
    st.write(
        "Explore movie ratings and analyze rating patterns."
    )

st.divider()

st.subheader("Project Features")

feature1, feature2, feature3 = st.columns(3)

with feature1:
    st.metric("User Dataset", "users_export.csv")
    st.caption("User profiles and activity")

with feature2:
    st.write("**Data Management**")
    st.caption("Create, view, update, and delete records.")

with feature3:
    st.write("**Data Analysis**")
    st.caption(
        "Summary statistics, interactive charts, "
        "and downloadable reports."
    )

st.info(
    "Use the navigation menu to open the Users, Movies, "
    "or Ratings page."
)

st.write(
    "Recommendations use simple rating statistics and popularity, "
    "not machine learning."
)
