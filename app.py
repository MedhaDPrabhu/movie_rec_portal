
import streamlit as st

st.set_page_config(
    page_title="Movie Recommendation Portal",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 Movie Recommendation Portal")

st.write(
    "Welcome to our Movie Recommendation Portal. "
    "Explore the movie library, manage user profiles, "
    "and analyze movie ratings."
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
        "Manage the movie catalogue, add new movies, "
        "search by title, filter by genre and release year, "
        "update movie details, and delete catalogue entries."
    )

with col3:
    st.write("### ⭐ Ratings")
    st.write(
        "Explore movie ratings, manage rating records, "
        "and analyze rating patterns."
    )

st.divider()

st.subheader("Project Features")

feature1, feature2, feature3 = st.columns(3)

with feature1:
    st.metric("User Dataset", "users_export.csv")
    st.caption("User profiles and activity")

with feature2:
    st.metric("Movie Dataset", "movie_data.csv")
    st.caption("Movie metadata and catalogue management")

with feature3:
    st.metric("Ratings Dataset", "ratings_export.csv")
    st.caption("Rating management and analysis")

st.divider()

st.subheader("Movie Library Features")

movie1, movie2, movie3 = st.columns(3)

with movie1:
    st.write("### 📝 Catalogue Management")
    st.write(
        "Create, view, update, and delete movie records."
    )

with movie2:
    st.write("### 🔎 Search and Filter")
    st.write(
        "Find movies by title, genre, and release year."
    )

with movie3:
    st.write("### 📊 Movie Analytics")
    st.write(
        "Explore the most common genres and movie "
        "distribution across decades."
    )

st.info(
    "Use the navigation menu to open the Users, Movies, "
    "or Ratings page."
)

st.write(
    "The portal uses simple data analysis and rating statistics. "
    "It does not use machine learning."
)
