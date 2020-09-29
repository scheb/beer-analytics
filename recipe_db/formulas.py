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


def lovibond_to_srm(lovibond: float) -> float:
    """
    Convert from Degrees Lovibond color system to
    Standard Reference Method (SRM) color system.
    """
    return 1.3546 * lovibond - 0.76


def srm_to_lovibond(srm: float) -> float:
    """
    Convert from Degrees Lovibond color system to
    Standard Reference Method (SRM) color system.
    """
    return (srm + 0.76) / 1.3546


def ebc_to_lovibond(ebc: float) -> float:
    """
    Convert from European Brewing Convention (EBC) color system to
    Degrees Lovibond color system.
    """
    return srm_to_lovibond(ebc_to_srm(ebc))


def lovibond_to_ebc(lovibond: float) -> float:
    """
    Convert from Degrees Lovibond color system to
    European Brewing Convention (EBC) color system.
    """
    return srm_to_ebc(lovibond_to_srm(lovibond))


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


def fluid_ounces_to_liters(oz: float) -> float:
    """
    Calculate fluid ounces to gallons
    """
    return oz / 33.814


def ounces_to_gramms(oz: float) -> float:
    """
    Calculate ounces to gramms
    """
    return oz * 28.3495


def kg_to_lbs(kg: float) -> float:
    return kg * 2.20462


def yield_to_ppg(_yield: float) -> float:
    return _yield * 0.46214


def liters_to_gallons(liters: float) -> float:
  return liters * 0.264172

