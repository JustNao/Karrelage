from .utils import load

i18n = load("i18n_fr")


def id_to_name(id):
    if str(id) in i18n["texts"]:
        return i18n["texts"][str(id)]
    return None
