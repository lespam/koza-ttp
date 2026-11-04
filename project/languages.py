"""Languages the site is offered in (the same set as dollarscholars.org).

Mexican Spanish is the project's original language and the only Spanish: it is
served at / (old /es/ links redirect there) and every other language under its
own prefix (/en/, /fr/, /zh-hans/, ...).

This module must stay importable from settings.py, so it has no Django imports.
"""

# (code used in URLs, English name, name in that language)
SITE_LANGUAGES = [
    ("es-mx", "Spanish (Mexico)", "Español de México"),
    # Lenguas indígenas de México: van junto al español para que se encuentren rápido
    ("nhe", "Nahuatl (Eastern Huasteca)", "Náhuatl (Huasteca)"),
    ("yua", "Yucatec Maya", "Maaya t'aan"),
    ("zap", "Zapotec", "Zapoteco"),
    ("otq", "Querétaro Otomi", "Hñäñho"),
    ("en", "English", "English"),
    ("am", "Amharic", "አማርኛ"),
    ("ar", "Arabic", "العربية"),
    ("bn", "Bengali", "বাংলা"),
    ("cs", "Czech", "Čeština"),
    ("da", "Danish", "Dansk"),
    ("de", "German", "Deutsch"),
    ("el", "Greek", "Ελληνικά"),
    ("fa", "Persian", "فارسی"),
    ("fi", "Finnish", "Suomi"),
    ("fr", "French", "Français"),
    ("he", "Hebrew", "עברית"),
    ("hi", "Hindi", "हिन्दी"),
    ("hr", "Croatian", "Hrvatski"),
    ("ht", "Haitian Creole", "Kreyòl ayisyen"),
    ("hu", "Hungarian", "Magyar"),
    ("id", "Indonesian", "Bahasa Indonesia"),
    ("ig", "Igbo", "Asụsụ Igbo"),
    ("it", "Italian", "Italiano"),
    ("ja", "Japanese", "日本語"),
    ("ko", "Korean", "한국어"),
    ("ms", "Malay", "Bahasa Melayu"),
    ("nl", "Dutch", "Nederlands"),
    ("pl", "Polish", "Polski"),
    ("pt", "Portuguese", "Português"),
    ("ro", "Romanian", "Română"),
    ("ru", "Russian", "Русский"),
    ("sk", "Slovak", "Slovenčina"),
    ("sl", "Slovenian", "Slovenščina"),
    ("sq", "Albanian", "Shqip"),
    ("sv", "Swedish", "Svenska"),
    ("sw", "Swahili", "Kiswahili"),
    ("th", "Thai", "ภาษาไทย"),
    ("tl", "Tagalog", "Tagalog"),
    ("tr", "Turkish", "Türkçe"),
    ("uk", "Ukrainian", "Українська"),
    ("ur", "Urdu", "اردو"),
    ("vi", "Vietnamese", "Tiếng Việt"),
    ("yo", "Yoruba", "Yorùbá"),
    ("zh-hans", "Chinese (Simplified)", "简体中文"),
    ("zh-hant", "Chinese (Traditional)", "繁體中文"),
    ("zu", "Zulu", "isiZulu"),
]

SOURCE_LANGUAGE = "es-mx"
# The translation services only know plain Spanish as a source language.
MACHINE_SOURCE_LANGUAGE = "es"

# For settings.LANGUAGES.
LANGUAGES = [(code, english) for code, english, _native in SITE_LANGUAGES]

# Every language except the Mexican Spanish source text.
TARGET_LANGUAGES = [code for code, _e, _n in SITE_LANGUAGES if code != SOURCE_LANGUAGE]

# Mexican indigenous languages. Their machine translations are less reliable, so the
# site shows a notice asking native speakers to review them.
INDIGENOUS_LANGUAGES = ["nhe", "yua", "zap", "otq"]

# Only Google Translate offers these (Azure doesn't). translate_site uses Google for
# them even when the backend is Azure. Sources: machinetranslate.org/nahuatl, /zapotec.
GOOGLE_ONLY_LANGUAGES = ["nhe", "zap"]

# Site language code -> code the machine translation service expects.
LANGUAGE_MAP = {code: code for code in TARGET_LANGUAGES}
LANGUAGE_MAP_AZURE = {**LANGUAGE_MAP, "zh-hans": "zh-Hans", "zh-hant": "zh-Hant", "tl": "fil"}
LANGUAGE_MAP_GOOGLE = {**LANGUAGE_MAP, "zh-hans": "zh-CN", "zh-hant": "zh-TW", "he": "iw"}

# Django doesn't ship locale info for these, so we register it on startup.
EXTRA_LANG_INFO = {
    "am": {"bidi": False, "code": "am", "name": "Amharic", "name_local": "አማርኛ"},
    "ht": {"bidi": False, "code": "ht", "name": "Haitian Creole",
           "name_local": "Kreyòl ayisyen"},
    "tl": {"bidi": False, "code": "tl", "name": "Tagalog", "name_local": "Tagalog"},
    "yo": {"bidi": False, "code": "yo", "name": "Yoruba", "name_local": "Yorùbá"},
    "zu": {"bidi": False, "code": "zu", "name": "Zulu", "name_local": "isiZulu"},
    "nhe": {"bidi": False, "code": "nhe", "name": "Nahuatl (Eastern Huasteca)",
            "name_local": "Náhuatl (Huasteca)"},
    "yua": {"bidi": False, "code": "yua", "name": "Yucatec Maya", "name_local": "Maaya t'aan"},
    "zap": {"bidi": False, "code": "zap", "name": "Zapotec", "name_local": "Zapoteco"},
    "otq": {"bidi": False, "code": "otq", "name": "Querétaro Otomi", "name_local": "Hñäñho"},
}
