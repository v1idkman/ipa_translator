# Northwest American English Accent Checker

This app provides a GUI that:

- Asks the user to enter the sentence they plan to pronounce.
- Records the user's speech.
- Transcribes speech to text.
- Loads a pronunciation dictionary dataset (CMUdict) and applies a Northwest American override dataset from `northwest_american_overrides.csv`.
- Compares recognized speech against the user-entered target sentence to keep analysis useful even when recognition misses words.
- Produces a proficiency/alignment score for Northwest American English pronunciation.
- Highlights words with potential incorrect phoneme segments and shows target vs observed IPA to guide practice.
- Uses stress-aware dictionary IPA (primary/secondary stress markers) and computes similarity on stress-neutral forms to avoid unfair score drops from stress-mark formatting differences.

## Files

- `ipa_transcription_gui.py`: Tkinter GUI app.
- `english_to_ipa_model.py`: speech recognition, lexicon loading, IPA conversion, and scoring logic.
- `northwest_american_overrides.csv`: dialect override dataset layered on top of CMUdict.

## Install

The app auto-installs required Python packages if they are missing:

- `SpeechRecognition`
- `eng-to-ipa`
- `cmudict`

If microphone capture fails on your machine, install `pyaudio` manually.

### Fix for "Could not find PyAudio; check installation"

This means SpeechRecognition cannot access the microphone backend in the active interpreter.

1. Activate your project virtual environment.
2. Install PyAudio into that same environment:

```bash
pip install PyAudio
```

3. Verify installation:

```bash
python -c "import pyaudio; print(pyaudio.__version__)"
```

4. In VS Code, make sure the selected Python interpreter is your project `.venv`.
5. Restart VS Code after installation.

## Run

```bash
python ipa_transcription_gui.py
```

## React Web Interface (Recommended UI)

The project now includes a React-based interface with a modern design and larger score presentation.

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start the web backend:

```bash
python web_backend.py
```

3. Open your browser:

- `http://127.0.0.1:8000`

### Web UI notes

- Enter the sentence you intend to pronounce.
- Use `Start Mic` (browser speech recognition) or type recognized speech manually.
- Click `Analyze` to get IPA and word-level feedback.
- The score gauge visualizes overall pronunciation score.
- The interactive consonant model uses a side-profile place-of-articulation map with expected vs observed zone highlighting.
- The interactive vowel model uses an IPA-style tongue-position chart (front/central/back and high/mid/low) with expected vs observed vowel targets.

## Notes

- This approach is dictionary- and transcription-based. It estimates dialect alignment from recognized words and IPA similarity, not a full acoustic phonetics model.
- Stress handling: ARPABET stress digits from CMUdict are converted to IPA stress markers (`ˈ`, `ˌ`) for display, while scoring uses a stress-neutral comparison to reduce dictionary-vs-transcriber notation mismatch.
- Recognition fallback: if speech recognition misses words, the app still evaluates IPA targets from the entered sentence and lists target words that were not recognized.
