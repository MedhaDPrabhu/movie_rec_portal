
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
import tempfile
import os
import uuid
import io

st.set_page_config(page_title="Ratings Management", layout="wide")

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "ratings_export.csv"

REQUIRED_COLUMNS = ["_id", "movie_id", "rating_val", "user_id"]


class RatingsManager:

    def __init__(self, file_path):
        self.file_path = Path(file_path)

    def load_data(self):
        try:
            data = pd.read_csv(self.file_path)

        except FileNotFoundError:
            raise ValueError("Ratings CSV file was not found.")

        except pd.errors.EmptyDataError:
            raise ValueError("Ratings CSV file is empty.")

        except (PermissionError, UnicodeDecodeError, OSError) as error:
            raise ValueError(f"Cannot read the CSV file: {error}")

        except Exception as error:
            raise ValueError(f"Error reading CSV: {error}")

        else:
            missing_columns = [
                col for col in REQUIRED_COLUMNS
                if col not in data.columns
            ]

            if missing_columns:
                raise ValueError(
                    f"Missing required columns: {missing_columns}"
                )

            for col in ["_id", "movie_id", "user_id"]:
                data[col] = data[col].astype("string").str.strip()

            data["rating_val"] = pd.to_numeric(
                data["rating_val"], errors="coerce"
            )

            return data

        finally:
            pass

    def save_data(self, data):
        temp_path = None

        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

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
            raise ValueError(f"Could not save ratings: {error}")

        else:
            return True

        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def create_rating(self, movie_id, user_id, rating):
        data = self.load_data()

        if not movie_id.strip() or not user_id.strip():
            raise ValueError("User ID and Movie ID are required.")

        if not isinstance(rating, int) or not 1 <= rating <= 10:
            raise ValueError("Rating must be a whole number from 1 to 10.")

        if data["_id"].isna().any() or data["_id"].duplicated().any():
            raise ValueError(
                "Existing rating IDs are missing or duplicated. "
                "Correct them before adding records."
            )

        duplicate = (
            (data["movie_id"] == movie_id)
            & (data["user_id"] == user_id)
        )

        if duplicate.any():
            raise ValueError("This user has already rated this movie.")

        new_record = {
            "_id": uuid.uuid4().hex[:24],
            "movie_id": movie_id,
            "rating_val": rating,
            "user_id": user_id
        }

        data = pd.concat(
            [data, pd.DataFrame([new_record])],
            ignore_index=True
        )

        self.save_data(data)
        return new_record

    def update_rating(self, record_id, movie_id, user_id, rating):
        data = self.load_data()

        if not record_id.strip():
            raise ValueError("Enter a rating record ID.")

        if not movie_id.strip() or not user_id.strip():
            raise ValueError("User ID and Movie ID are required.")

        if not isinstance(rating, int) or not 1 <= rating <= 10:
            raise ValueError("Rating must be a whole number from 1 to 10.")

        matches = data["_id"] == record_id

        if not matches.any():
            raise ValueError("Rating record ID was not found.")

        other_rows = data.loc[~matches]

        duplicate = (
            (other_rows["movie_id"] == movie_id)
            & (other_rows["user_id"] == user_id)
        )

        if duplicate.any():
            raise ValueError(
                "Another record already rates this movie for this user."
            )

        data.loc[matches, "movie_id"] = movie_id
        data.loc[matches, "user_id"] = user_id
        data.loc[matches, "rating_val"] = rating

        self.save_data(data)
        return True

    def delete_rating(self, record_id):
        data = self.load_data()

        if not record_id.strip():
            raise ValueError("Enter a rating record ID.")

        matches = data["_id"] == record_id

        if not matches.any():
            raise ValueError("Rating record ID was not found.")

        updated_data = data.loc[~matches].copy()

        self.save_data(updated_data)
        return True


manager = RatingsManager(CSV_PATH)

st.title("Movie Recommendation Portal")
st.header("Ratings Management")
st.write(
    "Add, view, edit and delete movie ratings. "
    "Ratings use a scale from 1 to 10."
)

try:
    df = manager.load_data()
except ValueError as error:
    st.error(str(error))
    st.stop()


# CREATE

st.subheader("Add a rating")

with st.form("create_rating_form"):
    new_user = st.text_input("User ID")
    new_movie = st.text_input("Movie ID")
    new_rating = st.slider(
        "Select rating", 1, 10, 7
    )
    create_button = st.form_submit_button("Submit Rating")

if create_button:
    try:
        manager.create_rating(
            new_movie.strip(),
            new_user.strip(),
            new_rating
        )
        st.success("Rating added successfully.")
        st.rerun()
    except ValueError as error:
        st.error(str(error))


# READ

st.subheader("View and search ratings")

search_user = st.text_input("Search by User ID")
search_movie = st.text_input("Search by Movie ID")

rating_options = ["All"] + [str(i) for i in range(1, 11)]

selected_rating = st.selectbox(
    "Filter by rating", rating_options
)

filtered = df.copy()

if search_user.strip():
    filtered = filtered[
        filtered["user_id"].str.contains(
            search_user.strip(),
            case=False,
            na=False,
            regex=False
        )
    ]

if search_movie.strip():
    filtered = filtered[
        filtered["movie_id"].str.contains(
            search_movie.strip(),
            case=False,
            na=False,
            regex=False
        )
    ]

if selected_rating != "All":
    filtered = filtered[
        filtered["rating_val"] == int(selected_rating)
    ]

sort_column = st.selectbox(
    "Sort records by",
    ["rating_val", "user_id", "movie_id"]
)

filtered = filtered.sort_values(
    sort_column, na_position="last"
)

st.dataframe(filtered, use_container_width=True)

st.caption(f"Showing {len(filtered):,} of {len(df):,} records.")


# UPDATE

st.subheader("Update a rating")

with st.form("update_rating_form"):
    update_id = st.text_input("Existing rating record ID")
    update_user = st.text_input("New User ID")
    update_movie = st.text_input("New Movie ID")
    update_value = st.slider(
        "New rating", 1, 10, 7, key="update_slider"
    )
    update_button = st.form_submit_button("Update Rating")

if update_button:
    try:
        manager.update_rating(
            update_id.strip(),
            update_movie.strip(),
            update_user.strip(),
            update_value
        )
        st.success("Rating updated successfully.")
        st.rerun()
    except ValueError as error:
        st.error(str(error))


# DELETE

st.subheader("Delete a rating")

with st.form("delete_rating_form"):
    delete_id = st.text_input("Rating record ID to delete")
    confirm_delete = st.checkbox(
        "Yes, I want to delete this rating."
    )
    delete_button = st.form_submit_button("Delete Rating")

if delete_button:
    if not confirm_delete:
        st.warning("Please confirm before deleting.")
    else:
        try:
            manager.delete_rating(delete_id.strip())
            st.success("Rating deleted successfully.")
            st.rerun()
        except ValueError as error:
            st.error(str(error))


# ANALYSIS

st.header("Rating Analysis")

valid_ratings = pd.to_numeric(
    filtered["rating_val"], errors="coerce"
)
valid_ratings = valid_ratings[
    valid_ratings.between(1, 10)
].dropna()

missing_count = int(
    df[REQUIRED_COLUMNS].isna().any(axis=1).sum()
)

invalid_count = int(
    (
        df["rating_val"].notna()
        & ~df["rating_val"].between(1, 10)
    ).sum()
)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Ratings", f"{len(df):,}")
col2.metric(
    "Average Rating",
    f"{valid_ratings.mean():.2f}" if not valid_ratings.empty else "N/A"
)
col3.metric(
    "Median Rating",
    f"{valid_ratings.median():.2f}" if not valid_ratings.empty else "N/A"
)
col4.metric("Unique Users", f"{df['user_id'].nunique():,}")

st.write(f"**Unique movies rated:** {df['movie_id'].nunique():,}")
st.write(f"**Rows with missing required values:** {missing_count:,}")
st.write(f"**Ratings outside the 1–10 range:** {invalid_count:,}")

st.caption(
    "Missing, non-numeric and out-of-range ratings are excluded "
    "from valid rating statistics."
)


# CHART 1: BAR CHART

st.subheader("Chart 1: Rating Distribution")

if not valid_ratings.empty:
    counts = valid_ratings.value_counts().sort_index()

    fig1, ax1 = plt.subplots()
    ax1.bar(counts.index, counts.values)
    ax1.set_xlabel("Rating")
    ax1.set_ylabel("Number of Ratings")
    ax1.set_title("Number of Ratings for Each Score")
    ax1.set_xticks(range(1, 11))

    st.pyplot(fig1)
    plt.close(fig1)
else:
    st.info("No valid ratings are available for this chart.")


# CHART 2: LINE CHART

st.subheader("Chart 2: Average Rating by Movie")

valid_movie_rows = filtered[
    filtered["rating_val"].between(1, 10)
].dropna(subset=["movie_id", "rating_val"])

movie_summary = (
    valid_movie_rows.groupby("movie_id")
    .agg(
        average_rating=("rating_val", "mean"),
        rating_count=("rating_val", "count")
    )
    .sort_values("rating_count", ascending=False)
    .head(10)
    .sort_values("movie_id")
)

if not movie_summary.empty:
    fig2, ax2 = plt.subplots()

    ax2.plot(
        movie_summary.index.astype(str),
        movie_summary["average_rating"],
        marker="o"
    )

    ax2.set_xlabel("Movie ID")
    ax2.set_ylabel("Average Rating")
    ax2.set_ylim(0, 10)
    ax2.set_title("Average Ratings for Up to 10 Movies")
    ax2.tick_params(axis="x", rotation=45)

    fig2.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)
else:
    st.info("No valid movie ratings are available for this chart.")


# EXPORT REPORT

st.header("Download Summary Report")

report = io.StringIO()

report.write("Movie Recommendation Portal - Ratings Report\n")
report.write(
    f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
)
report.write(f"Total rows in CSV: {len(df)}\n")
report.write(f"Rows in current view: {len(filtered)}\n")
report.write(f"User filter: {search_user or 'All'}\n")
report.write(f"Movie filter: {search_movie or 'All'}\n")
report.write(f"Rating filter: {selected_rating}\n")
report.write(f"Sort column: {sort_column}\n")
report.write(
    f"Average rating in view: "
    f"{valid_ratings.mean() if not valid_ratings.empty else 'N/A'}\n"
)
report.write(
    f"Median rating in view: "
    f"{valid_ratings.median() if not valid_ratings.empty else 'N/A'}\n"
)
report.write(f"Unique users in full dataset: {df['user_id'].nunique()}\n")
report.write(f"Unique movies in full dataset: {df['movie_id'].nunique()}\n")
report.write(f"Rows with missing required values: {missing_count}\n")
report.write(f"Invalid ratings: {invalid_count}\n")

st.download_button(
    "Download Ratings Report",
    data=report.getvalue(),
    file_name="ratings_summary_report.txt",
    mime="text/plain"
)

st.caption(
    "Changes are saved to ratings_export.csv. "
    "Keep a backup of the original dataset."
)
