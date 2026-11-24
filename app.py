"""Main entry point for the Household Electricity Consumption Analysis app."""

import streamlit as st


def main() -> None:
    """Render the initial placeholder page to verify the environment."""
    st.set_page_config(
        page_title="Household Electricity Consumption Analysis",
        layout="wide",
    )
    st.title("Household Electricity Consumption Analysis")
    st.info("Environment setup verified. Next step: implement authentication and dashboard.")


if __name__ == "__main__":
    main()
