# api/routers/system.py
from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/status/")
async def check_status():
    try:
        is_ready = router.model is not None
        return {
            "status": "ready" if is_ready else "not_ready",
            "device": router.model.device if is_ready else None
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@router.get("/languages/")
async def get_languages():
    # Return supported languages
    return {
        "languages": [
            {"code": "af", "name": "Afrikaans"},
            {"code": "am", "name": "Amharic"},
            {"code": "ar", "name": "Arabic"},
            {"code": "ast", "name": "Asturian"},
            {"code": "az", "name": "Azerbaijani"},
            {"code": "ba", "name": "Bashkir"},
            {"code": "be", "name": "Belarusian"},
            {"code": "bg", "name": "Bulgarian"},
            {"code": "bn", "name": "Bengali"},
            {"code": "br", "name": "Breton"},
            {"code": "bs", "name": "Bosnian"},
            {"code": "ca", "name": "Catalan"},
            {"code": "ceb", "name": "Cebuano"},
            {"code": "cs", "name": "Czech"},
            {"code": "cy", "name": "Welsh"},
            {"code": "da", "name": "Danish"},
            {"code": "de", "name": "German"},
            {"code": "el", "name": "Greek"},
            {"code": "en", "name": "English"},
            {"code": "es", "name": "Spanish"},
            {"code": "et", "name": "Estonian"},
            {"code": "fa", "name": "Persian"},
            {"code": "ff", "name": "Fulah"},
            {"code": "fi", "name": "Finnish"},
            {"code": "fr", "name": "French"},
            {"code": "fy", "name": "Western Frisian"},
            {"code": "ga", "name": "Irish"},
            {"code": "gd", "name": "Scottish Gaelic"},
            {"code": "gl", "name": "Galician"},
            {"code": "gu", "name": "Gujarati"},
            {"code": "ha", "name": "Hausa"},
            {"code": "he", "name": "Hebrew"},
            {"code": "hi", "name": "Hindi"},
            {"code": "hr", "name": "Croatian"},
            {"code": "ht", "name": "Haitian Creole"},
            {"code": "hu", "name": "Hungarian"},
            {"code": "hy", "name": "Armenian"},
            {"code": "id", "name": "Indonesian"},
            {"code": "ig", "name": "Igbo"},
            {"code": "ilo", "name": "Iloko"},
            {"code": "is", "name": "Icelandic"},
            {"code": "it", "name": "Italian"},
            {"code": "ja", "name": "Japanese"},
            {"code": "jv", "name": "Javanese"},
            {"code": "ka", "name": "Georgian"},
            {"code": "kk", "name": "Kazakh"},
            {"code": "km", "name": "Central Khmer"},
            {"code": "kn", "name": "Kannada"},
            {"code": "ko", "name": "Korean"},
            {"code": "lb", "name": "Luxembourgish"},
            {"code": "lg", "name": "Ganda"},
            {"code": "ln", "name": "Lingala"},
            {"code": "lo", "name": "Lao"},
            {"code": "lt", "name": "Lithuanian"},
            {"code": "lv", "name": "Latvian"},
            {"code": "mg", "name": "Malagasy"},
            {"code": "mk", "name": "Macedonian"},
            {"code": "ml", "name": "Malayalam"},
            {"code": "mn", "name": "Mongolian"},
            {"code": "mr", "name": "Marathi"},
            {"code": "ms", "name": "Malay"},
            {"code": "my", "name": "Burmese"},
            {"code": "ne", "name": "Nepali"},
            {"code": "nl", "name": "Dutch"},
            {"code": "no", "name": "Norwegian"},
            {"code": "ns", "name": "Northern Sotho"},
            {"code": "oc", "name": "Occitan"},
            {"code": "or", "name": "Oriya"},
            {"code": "pa", "name": "Punjabi"},
            {"code": "pl", "name": "Polish"},
            {"code": "ps", "name": "Pashto"},
            {"code": "pt", "name": "Portuguese"},
            {"code": "ro", "name": "Romanian"},
            {"code": "ru", "name": "Russian"},
            {"code": "sd", "name": "Sindhi"},
            {"code": "si", "name": "Sinhala"},
            {"code": "sk", "name": "Slovak"},
            {"code": "sl", "name": "Slovenian"},
            {"code": "so", "name": "Somali"},
            {"code": "sq", "name": "Albanian"},
            {"code": "sr", "name": "Serbian"},
            {"code": "ss", "name": "Swati"},
            {"code": "su", "name": "Sundanese"},
            {"code": "sv", "name": "Swedish"},
            {"code": "sw", "name": "Swahili"},
            {"code": "ta", "name": "Tamil"},
            {"code": "th", "name": "Thai"},
            {"code": "tl", "name": "Tagalog"},
            {"code": "tn", "name": "Tswana"},
            {"code": "tr", "name": "Turkish"},
            {"code": "uk", "name": "Ukrainian"},
            {"code": "ur", "name": "Urdu"},
            {"code": "uz", "name": "Uzbek"},
            {"code": "vi", "name": "Vietnamese"},
            {"code": "wo", "name": "Wolof"},
            {"code": "xh", "name": "Xhosa"},
            {"code": "yi", "name": "Yiddish"},
            {"code": "yo", "name": "Yoruba"},
            {"code": "zh", "name": "Chinese"},
            {"code": "zu", "name": "Zulu"}
        ]
    }