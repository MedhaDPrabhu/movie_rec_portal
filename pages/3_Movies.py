
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
import tempfile
import os
import json
import io

st.set_page_config(page_title="Movie Library", layout="wide")

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "movie_data.csv"

REQUIRED_COLUMNS = [
    "movie_id", "movie_title", "genres",
    "year_released", "original_language", "runtime"
]


def get_genres(value):
    try:
        genres = json.loads(value) if isinstance(value, str) else []
        if isinstance(genres, list):
            return ", ".join(str(g) for g in genres)
        return ""
    except (ValueError, TypeError):
        return ""

def genre_list(value):
    try:
        genres = json.loads(value) if isinstance(value, str) else []
        if isinstance(genres, list):
            return genres
        return []
    except (ValueError, TypeError):
        return []


class MovieManager:

    def __init__(self, file_path):
        self.file_path = Path(file_path)

    def load_data(self):
        try:
            data = pd.read_csv(self.file_path)

        except FileNotFoundError:
            raise ValueError("Movie CSV file was not found.")

        except pd.errors.EmptyDataError:
            raise ValueError("Movie CSV file is empty.")

        except (PermissionError, UnicodeDecodeError, OSError) as error:
            raise ValueError(f"Cannot read movie CSV: {error}")

        except Exception as error:
            raise ValueError(f"Error reading movie CSV: {error}")

        else:
            missing_columns = [
                col for col in REQUIRED_COLUMNS
                if col not in data.columns
            ]

            if missing_columns:
                raise ValueError(
                    f"Missing required columns: {missing_columns}"
                )

            if "director" not in data.columns:
                data["director"] = ""

            for col in ["movie_id", "movie_title", "genres",
                        "original_language", "director"]:
                data[col] = data[col].astype("string")

            data["year_released"] = pd.to_numeric(
                data["year_released"], errors="coerce"
            )
            data["runtime"] = pd.to_numeric(
                data["runtime"], errors="coerce"
            )

            return data

        finally:
            pass

    def save_data(self, data):
        temp_path = None

        try:
            self.file_path.parent.mkdir(
                parents=True, exist_ok=True
            )

            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="",
                suffix=".tmp",
                dir=self.file_path.parent,
                delete=False
            ) as temp_file:
                temp_path = temp_file.name
                data.to_csv(temp_file, index=False)

            os.replace(temp_path, self.file_path)
            temp_path = None

        except Exception as error:
            raise ValueError(f"Could not save movie data: {error}")

        else:
            return True

        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def create_movie(self, movie_id, title, genres, year,
                     director, language, runtime):
        data = self.load_data()

        movie_id = movie_id.strip()
        title = title.strip()

        if not movie_id or not title:
            raise ValueError("Movie ID and title are required.")

        if data["movie_id"].eq(movie_id).any():
            raise ValueError("This Movie ID already exists.")

        if not 1800 <= year <= datetime.now().year + 5:
            raise ValueError("Enter a valid release year.")

        if runtime < 0:
            raise ValueError("Runtime cannot be negative.")

        genre_values = [
            g.strip() for g in genres.split(",") if g.strip()
        ]

        new_movie = {col: "" for col in data.columns}
        new_movie.update({
            "movie_id": movie_id,
            "movie_title": title,
            "genres": json.dumps(genre_values),
            "year_released": year,
            "director": director.strip(),
            "original_language": language.strip(),
            "runtime": runtime
        })

        data = pd.concat(
            [data, pd.DataFrame([new_movie])],
            ignore_index=True
        )

        self.save_data(data)
        return True

    def update_movie(self, movie_id, title, genres, year,
                     director, language, runtime):
        data = self.load_data()

        movie_id = movie_id.strip()
        title = title.strip()
        matches = data["movie_id"] == movie_id

        if not matches.any():
            raise ValueError("Movie ID was not found.")

        if not title:
            raise ValueError("Movie title is required.")

        if not 1800 <= year <= datetime.now().year + 5:
            raise ValueError("Enter a valid release year.")

        if runtime < 0:
            raise ValueError("Runtime cannot be negative.")

        genre_values = [
            g.strip() for g in genres.split(",") if g.strip()
        ]

        data.loc[matches, "movie_title"] = title
        data.loc[matches, "genres"] = json.dumps(genre_values)
        data.loc[matches, "year_released"] = year
        data.loc[matches, "director"] = director.strip()
        data.loc[matches, "original_language"] = language.strip()
        data.loc[matches, "runtime"] = runtime

        self.save_data(data)
        return True

    def delete_movie(self, movie_id):
        data = self.load_data()

        matches = data["movie_id"] == movie_id.strip()

        if not matches.any():
            raise ValueError("Movie ID was not found.")

        data = data.loc[~matches].copy()
        self.save_data(data)
        return True


manager = MovieManager(CSV_PATH)

st.title("Movie Recommendation Portal")
st.header("Movie Library and Metadata Management")
st.write(
    "Add, search, filter, update and delete movie records."
)

try:
    df = manager.load_data()
except ValueError as error:
    st.error(str(error))
    st.stop()


st.subheader("Add a new movie")

with st.form("create_movie"):
    new_id = st.text_input("Movie ID")
    new_title = st.text_input("Movie Title")
    new_genres = st.text_input(
        "Genres, separated by commas",
        placeholder="Drama, Comedy"
    )
    new_year = st.number_input(
        "Release Year", min_value=1800,
        max_value=datetime.now().year + 5,
        value=2020
    )
    new_director = st.text_input("Director")
    new_language = st.text_input("Language", value="en")
    new_runtime = st.number_input(
        "Runtime in minutes", min_value=0, value=90
    )

    create_button = st.form_submit_button("Add Movie")

if create_button:
    try:
        manager.create_movie(
            new_id, new_title, new_genres, int(new_year),
            new_director, new_language, int(new_runtime)
        )
        st.success("Movie added successfully.")
        st.rerun()
    except ValueError as error:
        st.error(str(error))

st.subheader("Browse and search movies")

search_title = st.text_input("Search by title")
genre_values = sorted({
    genre
    for value in df["genres"].dropna()
    for genre in genre_list(value)
})

genre_options = ["All"] + genre_values
selected_genre = st.selectbox("Filter by genre", genre_options)

valid_years = df["year_released"].dropna()

if not valid_years.empty:
    min_year = int(valid_years.min())
    max_year = int(valid_years.max())

    year_range = st.slider(
        "Filter by release year",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year)
    )
else:
    year_range = (1800, datetime.now().year + 5)

filtered = df.copy()

if search_title.strip():
    filtered = filtered[
        filtered["movie_title"].str.contains(
            search_title.strip(),
            case=False, na=False, regex=False
        )
    ]

if selected_genre != "All":
    filtered = filtered[
        filtered["genres"].apply(
            lambda value: selected_genre in genre_list(value)
        )
    ]

filtered = filtered[
    filtered["year_released"].between(
        year_range[0], year_range[1]
    )
]

sort_by = st.selectbox(
    "Sort movies by",
    ["movie_title", "year_released", "runtime"]
)

filtered = filtered.sort_values(sort_by, na_position="last")

display_data = filtered.copy()
display_data["genres"] = display_data["genres"].apply(get_genres)

st.dataframe(
    display_data[
        ["movie_id", "movie_title", "genres",
         "year_released", "director",
         "original_language", "runtime"]
    ],
    use_container_width=True
)

st.caption(
    f"Showing {len(filtered):,} of {len(df):,} movies."
)

st.subheader("Update a movie")

with st.form("update_movie"):
    edit_id = st.text_input("Movie ID to update")
    edit_title = st.text_input("Updated title")
    edit_genres = st.text_input(
        "Updated genres, separated by commas"
    )
    edit_year = st.number_input(
        "Updated release year",
        min_value=1800,
        max_value=datetime.now().year + 5,
        value=2020,
        key="edit_year"
    )
    edit_director = st.text_input("Updated director")
    edit_language = st.text_input("Updated language")
    edit_runtime = st.number_input(
        "Updated runtime in minutes",
        min_value=0,
        value=90,
        key="edit_runtime"
    )

    update_button = st.form_submit_button("Update Movie")

if update_button:
    try:
        manager.update_movie(
            edit_id, edit_title, edit_genres, int(edit_year),
            edit_director, edit_language, int(edit_runtime)
        )
        st.success("Movie updated successfully.")
        st.rerun()
    except ValueError as error:
        st.error(str(error))

st.subheader("Delete a movie")

with st.form("delete_movie"):
    delete_id = st.text_input("Movie ID to delete")
    confirm_delete = st.checkbox(
        "I confirm that I want to delete this movie."
    )
    delete_button = st.form_submit_button("Delete Movie")

if delete_button:
    if not confirm_delete:
        st.warning("Please confirm before deleting.")
    else:
        try:
            manager.delete_movie(delete_id)
            st.success("Movie deleted successfully.")
            st.rerun()
        except ValueError as error:
            st.error(str(error))

st.header("Movie Analytics")

year_data = pd.to_numeric(df["year_released"], errors="coerce")
runtime_data = pd.to_numeric(df["runtime"], errors="coerce")

col1, col2, col3 = st.columns(3)

col1.metric("Total Movies", f"{len(df):,}")
col2.metric("Unique Genres", f"{len(genre_values):,}")
col3.metric(
    "Average Runtime",
    f"{runtime_data[runtime_data > 0].mean():.1f} min"
    if (runtime_data > 0).any() else "N/A"
)

st.write(
    f"**Movies with missing titles:** "
    f"{df['movie_title'].isna().sum():,}"
)
st.write(
    f"**Movies with missing release years:** "
    f"{year_data.isna().sum():,}"
)
st.write(
    f"**Movies with missing runtimes:** "
    f"{runtime_data.isna().sum():,}"
)

st.subheader("Chart 1: Top Genres")

genre_counts = (
    df["genres"].dropna()
    .apply(genre_list)
    .explode()
    .dropna()
    .value_counts()
    .head(10)
)

if not genre_counts.empty:
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    genre_counts.sort_values().plot(
        kind="barh", ax=ax1
    )
    ax1.set_xlabel("Number of Movies")
    ax1.set_ylabel("Genre")
    ax1.set_title("Top 10 Genres")
    fig1.tight_layout()
    st.pyplot(fig1)
    plt.close(fig1)
else:
    st.info("No genre information is available.")

st.subheader("Chart 2: Movies Across Decades")

decades = (year_data.dropna() // 10 * 10).astype(int)
decade_counts = decades.value_counts().sort_index()

if not decade_counts.empty:
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    ax2.bar(
        decade_counts.index.astype(str) + "s",
        decade_counts.values
    )
    ax2.set_xlabel("Decade")
    ax2.set_ylabel("Number of Movies")
    ax2.set_title("Distribution of Movies Across Decades")
    ax2.tick_params(axis="x", rotation=45)
    fig2.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)
else:
    st.info("No release-year information is available.")

st.header("Download Movie Report")

report = io.StringIO()

report.write("Movie Library Report\n")
report.write(
    f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
)
report.write(f"Total movies: {len(df)}\n")
report.write(f"Movies in current view: {len(filtered)}\n")
report.write(f"Title search: {search_title or 'All'}\n")
report.write(f"Genre filter: {selected_genre}\n")
report.write(f"Release-year range: {year_range}\n")
report.write(f"Sort order: {sort_by}\n")
report.write(f"Unique genres: {len(genre_values)}\n")
report.write(
    f"Average runtime: "
    f"{runtime_data[runtime_data > 0].mean() if (runtime_data > 0).any() else 'N/A'}\n"
)
report.write(
    f"Missing titles: {df['movie_title'].isna().sum()}\n"
)
report.write(f"Missing release years: {year_data.isna().sum()}\n")
report.write(f"Missing runtimes: {runtime_data.isna().sum()}\n")

st.download_button(
    "Download Movie Report",
    data=report.getvalue(),
    file_name="movie_library_report.txt",
    mime="text/plain"
)
