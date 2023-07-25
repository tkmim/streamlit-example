from enum import Enum


class Variables(Enum):
    precipitation = "niederschlag"
    accumulated_precipitation = "niederschlagssumme"
    snow = "schnee"
    temperature = "temperatur"
    humidity = "relfeuchte"
    dew_point = "taupunkt"
    pressure = "luftdruck"
    wind_gusts = "windboeen"
    radar_reflectivity = "reflektivitaet"
    cape = "mlcape"
    # FIXME: the variable super cell index was giving problems due to a member with a different size.
    # super_cell_index = "supercellindex"
