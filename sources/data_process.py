import numpy as np
import xarray

from .variables import Variables


def convert_to_probabilities(data_array: xarray.DataArray, variable: Variables) -> xarray.DataArray:
    """
    Given a data array containing a dimension member and a dimension time, create a new dataset in which
    the new dimensions are the time and the variable value, and the actual values are the
    probabilities of that happening.
    :param data_array:
    :param variable:
    :return data_array:
    """
    min_value = data_array.min().values

    max_value = np.nanquantile(data_array.values, .99)
    number_of_steps = 100
    steps = np.linspace(min_value, max_value, number_of_steps)
    times = data_array["time"]
    members = data_array.member
    members = [idx for idx, m in enumerate(members) if m.values != "Main"]
    data_array = data_array.isel(member=members)

    prob_array = np.zeros((len(times), len(steps)))

    for t_idx, t in enumerate(times):
        number_of_members = np.count_nonzero(~np.isnan(data_array.sel(time=t).values))
        for s_idx, s in enumerate(steps):
            prob_array[t_idx, s_idx] = (data_array.sel(time=t) > s).sum() / number_of_members * 100.

    prob_dataArray = xarray.DataArray(prob_array, coords={"time": times, variable.name: steps})
    return prob_dataArray
