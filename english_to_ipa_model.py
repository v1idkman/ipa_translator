import difflib
import csv
import os
import re
import subprocess
import sys

import eng_to_ipa as ipa
import speech_recognition as sr


REQUIRED_PACKAGES = {
    "eng-to-ipa": "eng_to_ipa",
    "cmudict": "cmudict",
    "SpeechRecognition": "speech_recognition",
    "PyAudio": "pyaudio",
}

for package, module_name in REQUIRED_PACKAGES.items():
    try:
        __import__(module_name)
    except ImportError:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])


try:
    import cmudict
except ImportError:
    cmudict = None


ARPABET_TO_IPA = {
    "AA": "ɑ",
    "AE": "æ",
    "AH": "ʌ",
    "AO": "ɔ",
    "AW": "aʊ",
    "AY": "aɪ",
    "B": "b",
    "CH": "tʃ",
    "D": "d",
    "DH": "ð",
    "EH": "ɛ",
    "ER": "ɝ",
    "EY": "eɪ",
    "F": "f",
    "G": "ɡ",
    "HH": "h",
    "IH": "ɪ",
    "IY": "i",
    "JH": "dʒ",
    "K": "k",
    "L": "l",
    "M": "m",
    "N": "n",
    "NG": "ŋ",
    "OW": "oʊ",
    "OY": "ɔɪ",
    "P": "p",
    "R": "ɹ",
    "S": "s",
    "SH": "ʃ",
    "T": "t",
    "TH": "θ",
    "UH": "ʊ",
    "UW": "u",
    "V": "v",
    "W": "w",
    "Y": "j",
    "Z": "z",
    "ZH": "ʒ",
}


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NORTHWEST_OVERRIDES_DATASET = os.path.join(BASE_DIR, "northwest_american_overrides.csv")


def normalize_text_to_words(text):
    return re.findall(r"[a-zA-Z']+", text.lower())


def load_northwest_overrides_from_csv(csv_path=NORTHWEST_OVERRIDES_DATASET):
    overrides = {}

    if not os.path.exists(csv_path):
        return overrides

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            word = (row.get("word") or "").strip().lower()
            arpabet = (row.get("arpabet") or "").strip()
            if word and arpabet:
                overrides[word] = arpabet

    return overrides


def load_northwest_american_lexicon():
    """
    Load a pronunciation dictionary dataset.
    Base dataset: CMU Pronouncing Dictionary (cmudict package).
    Dialect adjustment: lightweight Northwest American override entries.
    """
    lexicon = {}

    if cmudict is not None:
        for word, prons in cmudict.dict().items():
            if prons:
                lexicon[word.lower()] = " ".join(prons[0])

    for word, pron in load_northwest_overrides_from_csv().items():
        lexicon[word.lower()] = pron

    return lexicon


def arpabet_to_ipa(arpabet_pron):
    if not arpabet_pron:
        return ""

    ipa_parts = []
    for raw_token in arpabet_pron.split():
        stress_match = re.search(r"(\d)$", raw_token)
        stress_marker = ""
        if stress_match:
            if stress_match.group(1) == "1":
                stress_marker = "ˈ"
            elif stress_match.group(1) == "2":
                stress_marker = "ˌ"

        token = re.sub(r"\d", "", raw_token)
        ipa_symbol = ARPABET_TO_IPA.get(token, "")
        if ipa_symbol:
            ipa_parts.append(f"{stress_marker}{ipa_symbol}")

    return "".join(ipa_parts)


def text_to_northwest_ipa(text, lexicon):
    words = normalize_text_to_words(text)
    ipa_words = []

    for word in words:
        arpabet_pron = lexicon.get(word)
        if arpabet_pron:
            ipa_words.append(arpabet_to_ipa(arpabet_pron))
        else:
            # Fallback for OOV words if they are not present in the dictionary.
            ipa_words.append(ipa.convert(word))

    return " ".join(ipa_words)


def record_audio(timeout=10, phrase_time_limit=8):
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 1.2

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.8)
        audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

    return audio, recognizer


def validate_audio_backend():
    """Validate microphone dependencies and return (ok, message)."""
    try:
        import pyaudio  # noqa: F401
    except Exception:
        return (
            False,
            "PyAudio is not installed in the active Python environment. "
            "Install it with: pip install PyAudio",
        )

    try:
        mic_names = sr.Microphone.list_microphone_names()
    except Exception as exc:
        return False, f"Microphone initialization failed: {exc}"

    if not mic_names:
        return False, "No microphone device was detected on this system."

    return True, "Audio backend is ready."


def speech_to_text(audio, recognizer):
    try:
        return recognizer.recognize_google(audio, language="en-US")
    except sr.UnknownValueError:
        return None
    except sr.RequestError:
        return None


def similarity_score(text_a, text_b):
    if not text_a and not text_b:
        return 1.0
    return difflib.SequenceMatcher(None, text_a, text_b).ratio()


def remove_stress_marks(ipa_text):
    return ipa_text.replace("ˈ", "").replace("ˌ", "")


def get_ipa_mismatch_segments(expected_ipa, observed_ipa, ignore_stress=True):
    """Return a compact list of IPA segment mismatches between expected and observed forms."""
    if ignore_stress:
        expected_ipa = remove_stress_marks(expected_ipa)
        observed_ipa = remove_stress_marks(observed_ipa)

    if expected_ipa == observed_ipa:
        return []

    mismatches = []
    matcher = difflib.SequenceMatcher(None, expected_ipa, observed_ipa)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        expected_seg = expected_ipa[i1:i2]
        observed_seg = observed_ipa[j1:j2]
        mismatches.append(
            {
                "operation": tag,
                "expected": expected_seg,
                "observed": observed_seg,
            }
        )

    return mismatches


def analyze_spoken_sentence(spoken_text, lexicon):
    """
    Score a single recognized English sentence without requiring a prompt sentence.
    The score is based on dictionary coverage and IPA consistency.
    """
    spoken_words = normalize_text_to_words(spoken_text)

    if not spoken_words:
        return {
            "spoken_text": spoken_text,
            "dictionary_ipa": "",
            "fallback_ipa": "",
            "dictionary_coverage": 0.0,
            "ipa_similarity": 0.0,
            "proficiency_score": 0.0,
            "assessment": "No recognized words to analyze",
            "word_rows": [],
        }

    dictionary_known = 0
    word_rows = []

    for word in spoken_words:
        arpabet_pron = lexicon.get(word)
        known = bool(arpabet_pron)
        if known:
            dictionary_known += 1

        dict_ipa = arpabet_to_ipa(arpabet_pron) if known else ""
        fallback_ipa = ipa.convert(word)
        mismatch_segments = get_ipa_mismatch_segments(dict_ipa, fallback_ipa, ignore_stress=True) if known else []
        has_phoneme_issue = known and bool(mismatch_segments)

        word_rows.append(
            {
                "word": word,
                "in_dictionary": known,
                "dictionary_ipa": dict_ipa,
                "fallback_ipa": fallback_ipa,
                "has_phoneme_issue": has_phoneme_issue,
                "mismatch_segments": mismatch_segments,
            }
        )

    dictionary_ipa = text_to_northwest_ipa(spoken_text, lexicon)
    fallback_ipa = ipa.convert(" ".join(spoken_words))
    dictionary_ipa_no_stress = remove_stress_marks(dictionary_ipa)
    fallback_ipa_no_stress = remove_stress_marks(fallback_ipa)

    dictionary_coverage = dictionary_known / len(spoken_words)
    ipa_similarity = similarity_score(dictionary_ipa_no_stress, fallback_ipa_no_stress)
    proficiency_score = (0.7 * dictionary_coverage) + (0.3 * ipa_similarity)

    if proficiency_score >= 0.85:
        assessment = "Strong Northwest American English lexical-pronunciation fit"
    elif proficiency_score >= 0.65:
        assessment = "Moderate Northwest American English lexical-pronunciation fit"
    else:
        assessment = "Low Northwest American English lexical-pronunciation fit"

    return {
        "spoken_text": spoken_text,
        "dictionary_ipa": dictionary_ipa,
        "fallback_ipa": fallback_ipa,
        "dictionary_ipa_no_stress": dictionary_ipa_no_stress,
        "fallback_ipa_no_stress": fallback_ipa_no_stress,
        "dictionary_coverage": dictionary_coverage,
        "ipa_similarity": ipa_similarity,
        "proficiency_score": proficiency_score,
        "assessment": assessment,
        "word_rows": word_rows,
    }


def analyze_prompt_vs_recognized(prompt_text, recognized_text, lexicon):
    """
    Compare user-provided intended sentence against recognized speech.
    This keeps evaluation available even when recognizer misses words.
    """
    expected_words = normalize_text_to_words(prompt_text)
    recognized_words = normalize_text_to_words(recognized_text or "")

    expected_dictionary_ipa = text_to_northwest_ipa(prompt_text, lexicon)
    recognized_dictionary_ipa = text_to_northwest_ipa(" ".join(recognized_words), lexicon)

    expected_no_stress = remove_stress_marks(expected_dictionary_ipa)
    recognized_no_stress = remove_stress_marks(recognized_dictionary_ipa)

    matched_words = 0
    word_rows = []

    def word_to_ipa(word):
        if not word:
            return ""
        arpabet = lexicon.get(word, "")
        return arpabet_to_ipa(arpabet) if arpabet else ipa.convert(word)

    # Align expected and recognized words to avoid cascading mismatches when one word is inserted/deleted.
    matcher = difflib.SequenceMatcher(None, expected_words, recognized_words)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for e_word, r_word in zip(expected_words[i1:i2], recognized_words[j1:j2]):
                matched_words += 1
                word_rows.append(
                    {
                        "expected_word": e_word,
                        "recognized_word": r_word,
                        "expected_ipa": word_to_ipa(e_word),
                        "recognized_ipa": word_to_ipa(r_word),
                        "word_match": True,
                        "missing_from_recognition": False,
                        "has_phoneme_issue": False,
                        "mismatch_segments": [],
                    }
                )
            continue

        e_chunk = expected_words[i1:i2]
        r_chunk = recognized_words[j1:j2]
        pair_len = min(len(e_chunk), len(r_chunk))

        for idx in range(pair_len):
            e_word = e_chunk[idx]
            r_word = r_chunk[idx]
            e_ipa = word_to_ipa(e_word)
            r_ipa = word_to_ipa(r_word)
            mismatch_segments = get_ipa_mismatch_segments(e_ipa, r_ipa, ignore_stress=True)
            word_rows.append(
                {
                    "expected_word": e_word,
                    "recognized_word": r_word,
                    "expected_ipa": e_ipa,
                    "recognized_ipa": r_ipa,
                    "word_match": False,
                    "missing_from_recognition": False,
                    "has_phoneme_issue": bool(mismatch_segments),
                    "mismatch_segments": mismatch_segments,
                }
            )

        for e_word in e_chunk[pair_len:]:
            word_rows.append(
                {
                    "expected_word": e_word,
                    "recognized_word": "",
                    "expected_ipa": word_to_ipa(e_word),
                    "recognized_ipa": "",
                    "word_match": False,
                    "missing_from_recognition": True,
                    "has_phoneme_issue": False,
                    "mismatch_segments": [],
                }
            )

        for r_word in r_chunk[pair_len:]:
            word_rows.append(
                {
                    "expected_word": "",
                    "recognized_word": r_word,
                    "expected_ipa": "",
                    "recognized_ipa": word_to_ipa(r_word),
                    "word_match": False,
                    "missing_from_recognition": False,
                    "has_phoneme_issue": False,
                    "mismatch_segments": [],
                }
            )

    lexical_accuracy = matched_words / len(expected_words) if expected_words else 0.0
    ipa_similarity = similarity_score(expected_no_stress, recognized_no_stress)
    proficiency_score = (0.65 * lexical_accuracy) + (0.35 * ipa_similarity)

    if proficiency_score >= 0.85:
        assessment = "Strong Northwest pronunciation"
    elif proficiency_score >= 0.65:
        assessment = "Moderate Northwest pronunciation"
    else:
        assessment = "Poor Northwest pronunciation"

    return {
        "prompt_text": prompt_text,
        "spoken_text": recognized_text or "",
        "expected_dictionary_ipa": expected_dictionary_ipa,
        "recognized_dictionary_ipa": recognized_dictionary_ipa,
        "expected_dictionary_ipa_no_stress": expected_no_stress,
        "recognized_dictionary_ipa_no_stress": recognized_no_stress,
        "lexical_accuracy": lexical_accuracy,
        "ipa_similarity": ipa_similarity,
        "proficiency_score": proficiency_score,
        "assessment": assessment,
        "word_rows": word_rows,
        "recognition_failed": len(recognized_words) == 0,
    }
