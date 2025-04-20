import speech_recognition as sr
import eng_to_ipa as ipa
import time
import tempfile
import subprocess
import sys

# Install required packages if not already installed
required_packages = ['eng_to_ipa']
for package in required_packages:
    try:
        __import__(package.replace('-', '_'))
    except ImportError:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def record_audio():
    """Record audio from microphone and return the audio data"""
    r = sr.Recognizer()
    r.pause_threshold = 2.0  
    with sr.Microphone() as source:
        print("Please speak something in English...")
        r.adjust_for_ambient_noise(source, duration=1)
        audio = r.listen(source)
        print("Recording complete!")
    return audio, r

def record_audio_to_file():
    """Record audio from microphone and save to a temporary file"""
    r = sr.Recognizer()
    r.pause_threshold = 2.0
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    
    with sr.Microphone() as source:
        print("Please speak something...")
        r.adjust_for_ambient_noise(source, duration=1)
        print("Recording... (speak now)")
        audio = r.listen(source)
        print("Recording complete!")
    
    with open(temp_file.name, "wb") as f:
        f.write(audio.get_wav_data())
    
    return temp_file.name


def speech_to_text(audio, recognizer):
    """Convert speech to text using Google Speech Recognition"""
    try:
        text = recognizer.recognize_google(audio, language="en-US")
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
        return None
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        return None

def text_to_ipa(text):
    """Convert English text to IPA notation"""
    try:
        ipa_text = ipa.convert(text)
        return ipa_text
    except Exception as e:
        print(f"Error converting to IPA: {e}")
        return None

def voice_to_ipa():
    """Main function to convert English voice to IPA"""
    audio, recognizer = record_audio()
    text = speech_to_text(audio, recognizer)
    
    if text:
        ipa_text = text_to_ipa(text)
        if ipa_text:
            print(f"IPA Transcription: {ipa_text}")
            
            save_option = input("Save this transcription to file? (y/n): ").lower()
            if save_option == 'y':
                filename = input("Enter filename (or press Enter for default): ")
                if not filename:
                    filename = f"english_ipa_transcription_{time.strftime('%Y%m%d_%H%M%S')}.txt"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"Original English text: {text}\n")
                    f.write(f"IPA transcription: {ipa_text}\n")
                print(f"Transcription saved to {filename}")
                
            return ipa_text
    
    return None

if __name__ == "__main__":
    print("English Voice to IPA Translator")
    print("===============================")
    
    while True:
        print("\nOptions:")
        print("1. Transcribe English speech to IPA")
        print("2. Exit")
        
        choice = input("Select an option (1-2): ")
        
        if choice == '1':
            voice_to_ipa()
        elif choice == '2':
            print("Exiting program. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")
