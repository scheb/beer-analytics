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


def alcohol_by_volume(original_gravity, final_gravity):
    """
    Calculate the Alcohol By Volume (ABV).
    """
    return (original_gravity - final_gravity) / 0.75
