def srm_to_ebc(srm: float) -> float:
    """
    Convert from Standard Reference Method (SRM) color system to
    European Brewing Convention (EBC) color system.
    """
    return 1.97 * srm


def ebc_to_srm(ebc: float) -> float:
    """
    Convert from European Brewing Convention (EBC) color system to
    Standard Reference Method (SRM) color system.
    """
    return ebc / 1.97


def plato_to_gravity(degrees_plato: float) -> float:
    """
    Convert degrees plato to gravity.
    """
    return 259.0 / (259.0 - degrees_plato)


def gravity_to_plato(gravity: float) -> float:
    """
    Convert gravity to degrees plato.
    """
    return 259.0 - (259.0 / gravity)


def alcohol_by_volume(original_gravity: float, final_gravity: float):
    """
    Calculate the Alcohol By Volume (ABV).
    """
    return (original_gravity - final_gravity) * 131.25


def attenuation_to_final_plato(attenuation: float, original_plato: float):
    """
    Calculate the final degrees plato based on attenuation and original plato.
    """
    apparent_attenuation = attenuation / 0.81
    return original_plato - original_plato * apparent_attenuation


def abv_to_to_final_plato(abv: float, original_plato: float):
    """
    Calculate the final degrees plato based on abv and original plato.
    """
    fg = plato_to_gravity(original_plato) - (abv / 131.25)
    return gravity_to_plato(fg)
