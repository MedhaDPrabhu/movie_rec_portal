
import streamlit as st
import pandas as pd
import numpy as np
import os
import tempfile
from pathlib import Path
from datetime import datetime
from uuid import uuid4


st.set_page_config(
    page_title="User Profiles",
    layout="wide"
)

st.title("User Profiles & Activity")
st.write("Manage user records and explore user activity.")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_FILE = PROJECT_ROOT / "data" / "users_export.csv"

COLUMNS = [
    "_id",
    "display_name",
    "num_ratings_pages",
    "num_reviews",
    "username"
]

NUMERIC_COLUMNS = [
    "num_ratings_pages",
    "num_reviews"
]

class UserManager:

    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self._data = pd.DataFrame(columns=COLUMNS)

    @property
    def data(self):
        return self._data.copy()

    def load_data(self):
        """Read the CSV and handle missing or invalid data."""

        try:
            if not self.file_path.exists():
                raise FileNotFoundError(
                    "users_export.csv was not found in the data folder."
                )

            if self.file_path.stat().st_size == 0:
                raise ValueError("The CSV file is empty.")

            df = pd.read_csv(
                self.file_path,
                dtype={"_id": "string", "username": "string"},
                keep_default_na=True
            )

            if df.empty:
                raise ValueError("The CSV contains no user records.")

            missing_columns = [
                col for col in COLUMNS if col not in df.columns
            ]

            if missing_columns:
                raise ValueError(
                    "Missing required columns: "
                    + ", ".join(missing_columns)
                )

            df = df[COLUMNS].copy()

            df["_id"] = df["_id"].str.strip()
            df["username"] = df["username"].str.strip()

            if df["_id"].isna().any() or df["_id"].eq("").any():
                raise ValueError("Some user IDs are missing.")

            if df["_id"].duplicated().any():
                raise ValueError("Duplicate user IDs exist in the CSV.")

            for col in NUMERIC_COLUMNS:
                original = df[col].copy()
                converted = pd.to_numeric(
                    original, errors="coerce"
                )

                invalid = (
                    original.notna()
                    & original.astype(str).str.strip().ne("")
                    & converted.isna()
                )

                if invalid.any():
                    raise ValueError(
                        f"Column '{col}' contains invalid numbers."
                    )

                if (converted.dropna() < 0).any():
                    raise ValueError(
                        f"Column '{col}' cannot contain negative values."
                    )

                df[col] = converted

            self._data = df

        except FileNotFoundError:
            raise
        except pd.errors.EmptyDataError as exc:
            raise ValueError("The CSV has no readable data.") from exc
        except (pd.errors.ParserError, UnicodeDecodeError) as exc:
            raise ValueError("The CSV format is invalid.") from exc
        except PermissionError as exc:
            raise PermissionError(
                "The CSV cannot be read. Check file permissions."
            ) from exc
        except OSError as exc:
            raise OSError("An error occurred while reading the CSV.") from exc
        else:
            return self.data
        finally:
            pass

    def save_data(self, df):
        """Write to a temporary CSV, then replace the original."""

        temp_path = None

        try:
            if list(df.columns) != COLUMNS:
                raise ValueError("The CSV column structure is incorrect.")

            if df["_id"].isna().any() or df["_id"].duplicated().any():
                raise ValueError("User IDs must be present and unique.")

            for col in NUMERIC_COLUMNS:
                numbers = pd.to_numeric(df[col], errors="coerce")
                if numbers.isna().any() or (numbers < 0).any():
                    raise ValueError(
                        f"Invalid values in column '{col}'."
                    )

            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="",
                suffix=".csv",
                prefix="users_temp_",
                dir=self.file_path.parent,
                delete=False
            ) as temp_file:
                temp_path = Path(temp_file.name)
                df.to_csv(temp_file, index=False)

            os.replace(temp_path, self.file_path)
            self._data = df.copy()

        except PermissionError as exc:
            raise PermissionError(
                "Cannot save the CSV. Check file permissions."
            ) from exc
        except (OSError, ValueError, TypeError) as exc:
            raise RuntimeError(
                f"Could not safely save the CSV: {exc}"
            ) from exc
        else:
            return True
        finally:
            if temp_path is not None and temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass

    def add_user(self, display_name, username,
                 num_ratings_pages, num_reviews):

        df = self.data

        username = username.strip()
        display_name = display_name.strip()

        if not username:
            raise ValueError("Username is required.")

        if not display_name:
            display_name = pd.NA

        if num_ratings_pages < 0 or num_reviews < 0:
            raise ValueError("Activity counts cannot be negative.")

        if df["username"].str.casefold().eq(
            username.casefold()
        ).any():
            raise ValueError("This username already exists.")

        new_id = uuid4().hex

        new_row = pd.DataFrame([{
            "_id": new_id,
            "display_name": display_name,
            "num_ratings_pages": num_ratings_pages,
            "num_reviews": num_reviews,
            "username": username
        }])

        df = pd.concat([df, new_row], ignore_index=True)
        self.save_data(df)
        return new_id

    def update_user(self, user_id, display_name, username,
                    num_ratings_pages, num_reviews):

        df = self.data
        user_id = str(user_id).strip()
        username = username.strip()
        display_name = display_name.strip()

        matches = df.index[df["_id"] == user_id].tolist()

        if not matches:
            raise ValueError("Invalid user ID. Record not found.")

        if not username:
            raise ValueError("Username is required.")

        if num_ratings_pages < 0 or num_reviews < 0:
            raise ValueError("Activity counts cannot be negative.")

        duplicate = (
            df["username"].str.casefold().eq(username.casefold())
            & (df["_id"] != user_id)
        )

        if duplicate.any():
            raise ValueError("Another user has this username.")

        i = matches[0]
        df.loc[i, "display_name"] = (
            display_name if display_name else pd.NA
        )
        df.loc[i, "username"] = username
        df.loc[i, "num_ratings_pages"] = num_ratings_pages
        df.loc[i, "num_reviews"] = num_reviews

        self.save_data(df)
        return True

    def delete_user(self, user_id):
        df = self.data
        user_id = str(user_id).strip()

        if not df["_id"].eq(user_id).any():
            raise ValueError("Invalid user ID. Record not found.")

        df = df[df["_id"] != user_id].copy()
        self.save_data(df)
        return True


manager = UserManager(CSV_FILE)

try:
    data = manager.load_data()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.info("Create the data folder and add users_export.csv.")
    st.stop()
except PermissionError as exc:
    st.error(str(exc))
    st.stop()
except (ValueError, OSError) as exc:
    st.error(str(exc))
    st.stop()
except Exception:
    st.error("An unexpected error occurred while loading users.")
    st.stop()


missing_names = int(data["display_name"].isna().sum())
missing_pages = int(data["num_ratings_pages"].isna().sum())

st.subheader("Data Quality")
st.write(
    f"Missing display names: {missing_names} | "
    f"Missing rating-page counts: {missing_pages}"
)

st.caption(
    "Missing display names are shown as 'Unknown' in tables. "
    "Missing numeric values remain blank in the CSV and are "
    "excluded from averages and charts that require those values."
)

display_data = data.copy()
display_data["display_name"] = (
    display_data["display_name"].fillna("Unknown")
)


st.subheader("Summary Statistics")

total_users = len(data)
average_reviews = data["num_reviews"].mean()
average_pages = data["num_ratings_pages"].mean()

c1, c2, c3 = st.columns(3)

c1.metric("Total Users", f"{total_users:,}")

c2.metric(
    "Average Reviews",
    f"{average_reviews:,.2f}"
    if pd.notna(average_reviews) else "N/A"
)

c3.metric(
    "Average Rating Pages",
    f"{average_pages:,.2f}"
    if pd.notna(average_pages) else "N/A"
)


st.subheader("Search and Filter Users")

search_text = st.text_input(
    "Search by username or display name"
)

minimum_reviews = st.slider(
    "Minimum number of reviews",
    min_value=0,
    max_value=max(1, int(data["num_reviews"].max())),
    value=0
)

filtered = display_data[
    display_data["num_reviews"].ge(minimum_reviews)
    & (
        display_data["username"].str.contains(
            search_text, case=False, na=False, regex=False
        )
        | display_data["display_name"].str.contains(
            search_text, case=False, na=False, regex=False
        )
    )
].copy()

st.write(f"Matching records: {len(filtered):,}")
st.dataframe(filtered, use_container_width=True)


st.subheader("User Activity Charts")

chart_data = filtered.copy()

chart_data["Activity Level"] = pd.cut(
    chart_data["num_reviews"],
    bins=[-1, 100, 500, float("inf")],
    labels=["Low (0–100)", "Medium (101–500)", "High (501+)"]
)

activity_counts = (
    chart_data["Activity Level"]
    .value_counts(sort=False)
    .rename_axis("Activity Level")
    .reset_index(name="Number of Users")
)

left, right = st.columns(2)

with left:
    st.write("**Chart 1: Users by Activity Level**")
    st.bar_chart(
        activity_counts.set_index("Activity Level")
    )

with right:
    st.write("**Chart 2: Reviews vs Rating Pages**")
    scatter_data = chart_data[
        chart_data["num_reviews"].notna()
        & chart_data["num_ratings_pages"].notna()
    ]

    if not scatter_data.empty:
        st.scatter_chart(
            scatter_data,
            x="num_ratings_pages",
            y="num_reviews"
        )
    else:
        st.info("No complete numeric records match these filters.")


st.subheader("Add a New User")

with st.form("add_user_form"):
    new_name = st.text_input("Display Name")
    new_username = st.text_input("Username")

    new_pages = st.number_input(
        "Number of Rating Pages",
        min_value=0,
        value=0,
        step=1
    )

    new_reviews = st.number_input(
        "Number of Reviews",
        min_value=0,
        value=0,
        step=1
    )

    add_clicked = st.form_submit_button("Add User")

if add_clicked:
    try:
        new_id = manager.add_user(
            new_name, new_username, int(new_pages), int(new_reviews)
        )
    except (ValueError, RuntimeError, PermissionError) as exc:
        st.error(str(exc))
    except Exception:
        st.error("Could not add the user. Please check your inputs.")
    else:
        st.success(f"User added successfully. ID: {new_id}")
        st.rerun()


st.subheader("Update User Details")

user_ids = data["_id"].astype(str).tolist()

if user_ids:
    selected_id = st.selectbox(
        "Select the user ID to edit",
        user_ids,
        key="edit_user_id"
    )

    selected_row = data.loc[
        data["_id"] == selected_id
    ].iloc[0]

    with st.form("edit_user_form"):
        edit_name = st.text_input(
            "Display Name",
            value=(
                "" if pd.isna(selected_row["display_name"])
                else str(selected_row["display_name"])
            )
        )

        edit_username = st.text_input(
            "Username",
            value=str(selected_row["username"])
        )

        edit_pages = st.number_input(
            "Number of Rating Pages",
            min_value=0,
            value=(
                0 if pd.isna(selected_row["num_ratings_pages"])
                else int(selected_row["num_ratings_pages"])
            ),
            step=1
        )

        edit_reviews = st.number_input(
            "Number of Reviews",
            min_value=0,
            value=int(selected_row["num_reviews"]),
            step=1
        )

        update_clicked = st.form_submit_button("Save Changes")

    if update_clicked:
        try:
            manager.update_user(
                selected_id,
                edit_name,
                edit_username,
                int(edit_pages),
                int(edit_reviews)
            )
        except (ValueError, RuntimeError, PermissionError) as exc:
            st.error(str(exc))
        except Exception:
            st.error("Could not update the user.")
        else:
            st.success("User details updated.")
            st.rerun()
else:
    st.info("There are no users to edit.")


st.subheader("Delete a User")

if user_ids:
    delete_id = st.selectbox(
        "Select the user ID to delete",
        user_ids,
        key="delete_user_id"
    )

    confirm_delete = st.checkbox(
        "I confirm that I want to delete this user."
    )

    if st.button("Delete Selected User", type="primary"):
        if not confirm_delete:
            st.warning("Please confirm before deleting.")
        else:
            try:
                manager.delete_user(delete_id)
            except (ValueError, RuntimeError, PermissionError) as exc:
                st.error(str(exc))
            except Exception:
                st.error("Could not delete the user.")
            else:
                st.success("User deleted successfully.")
                st.rerun()


st.subheader("Download Summary Report")

report_time = datetime.now().astimezone().strftime(
    "%Y-%m-%d %H:%M:%S %Z"
)

report_lines = [
    "MOVIE RECOMMENDATION PORTAL - USER REPORT",
    f"Generated at: {report_time}",
    f"CSV file: {CSV_FILE.name}",
    f"Rows in current dataset: {len(data)}",
    f"Rows after current filters: {len(filtered)}",
    f"Search text: {search_text or 'None'}",
    f"Minimum reviews filter: {minimum_reviews}",
    f"Missing display names: {missing_names}",
    f"Missing rating-page counts: {missing_pages}",
    f"Average reviews: {average_reviews}",
    f"Average rating pages: {average_pages}",
    "",
    "FILTERED USER RECORDS",
    filtered.to_csv(index=False)
]

report_text = "\n".join(report_lines)

st.download_button(
    label="Download User Report (.txt)",
    data=report_text,
    file_name="user_summary_report.txt",
    mime="text/plain"
)

st.caption(
    "Changes are saved to users_export.csv. "
    "The report reflects the current dataset and active filters."
)
