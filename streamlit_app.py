from datetime import datetime, timedelta
from typing import List

import streamlit as st

from sources.data_plotting import plot_data
from sources.data_process import convert_to_probabilities
from sources.data_retriever import get_data, cache
from sources.location_retriever import location_widget
from sources.models import Models
from sources.variables import Variables


def run_case(location: int, variable: Variables, models: List[Models]):
    # Get the data
    is_new, data = get_data(location, variable, models)

    # Convert the data
    if is_new or (location, variable, tuple(models)) not in cache.probabilities:
        prob_data = convert_to_probabilities(data, variable)
        cache.probabilities[(location, variable, tuple(models))] = prob_data
    else:
        prob_data = cache.probabilities[(location, variable, tuple(models))]

    times = prob_data.time.values.astype(datetime)
    times = [datetime.fromtimestamp(int(t / 1000000000)) for t in times]

    plot_mean = st.sidebar.checkbox("Plot Mean", value=True)
    time_slice = st.sidebar.slider(
        "Adjust Time",
        min_value=min(times),
        max_value=max(times),
        value=(min(times), max(times)),
        format="MM/DD hh",
        step=timedelta(hours=1)
    )

    if is_new or (location, variable, tuple(models), time_slice, plot_mean) not in cache.figures:
        figure = plot_data(data, prob_data, time_slice, plot_mean)
        cache.figures[(location, variable, tuple(models), time_slice, plot_mean)] = figure
    else:
        figure = cache.figures[(location, variable, tuple(models), time_slice, plot_mean)]

    st.pyplot(fig=figure)


def main():
    st.set_page_config(
        page_title="Weather Probability App!",
    )

    hide_menu = False
    if hide_menu:
        st.markdown('''
        <style>
        .stApp [data-testid="stToolbar"]{
            display:none;
        }
        </style>
        ''', unsafe_allow_html=True)

    st.title("Weather Probability App!")
    st.sidebar.title("Select Location:")
    loc_name, loc_id = location_widget()
    st.sidebar.markdown("---")
    st.sidebar.title("Select Variable:")
    var = st.sidebar.selectbox("Variable", [_var.name.capitalize() for _var in Variables])
    st.sidebar.markdown("---")
    st.sidebar.title("Select Model:")

    initial_selection = [_mod.name.capitalize() for _mod in [Models.icon_d2, Models.ecmwf]]
    models_selector = st.sidebar.multiselect("Models", [_mod.name.capitalize() for _mod in Models],
                                             default=initial_selection)
    if models_selector:
        models = [Models[model.lower()] for model in models_selector]
        st.sidebar.markdown("---")
        st.subheader(f"{str(var).capitalize()} at {str(loc_name)}")

        with st.spinner():
            try:
                run_case(loc_id, Variables[var.lower()], models)
            except AssertionError as err:
                st.warning(err)
        if len(models) == 1:
            st.markdown(f"**Model**: {str(models[0]).capitalize()}")
        else:
            st.markdown(f"**Models**: {'+'.join([str(model.name).capitalize() for model in models])}")


if __name__ == "__main__":
    main()
