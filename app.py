
import streamlit as st

st.set_page_config(
    page_title="Movie Recommendation Portal",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 Movie Recommendation Portal")

st.write(
    "Welcome to our Movie Recommendation Portal. "
    "Explore movie data, manage users, and rate movies."
)

st.subheader("What can you do here?")

col1, col2, col3 = st.columns(3)

with col1:
    st.write("### Users")
    st.write("Manage user records and view user statistics.")

with col2:
    st.write("### Movies")
    st.write("Browse movies and explore genres.")

with col3:
    st.write("### Ratings")
    st.write("Submit ratings and analyze rating patterns.")

st.info(
    "Use the navigation menu to open the Users, Movies, "
    "or Ratings page."
)

st.write(
    "Recommendations are based on simple rating statistics "
    "and popularity, not machine learning."
)
