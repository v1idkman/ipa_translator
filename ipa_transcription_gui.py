import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import time
import os
import sys
import importlib

# Ensure required packages are installed
try:
    import speech_recognition as sr
    import eng_to_ipa as ipa
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "SpeechRecognition", "eng-to-ipa", "pyaudio"])

# Import the model file (assuming it's named english_to_ipa_model.py)
try:
    import english_to_ipa_model as model
except ImportError:
    print("Error: Could not import the model file 'english_to_ipa_model.py'")
    print("Make sure it's in the same directory as this GUI file.")
    sys.exit(1)

class IPATranscriptionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("English Voice to IPA Transcription")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)
        
        # Set theme colors
        self.bg_color = "#f5f5f5"
        self.accent_color = "#3498db"
        self.text_bg = "#ffffff"
        self.button_bg = "#3498db"
        self.button_fg = "#ffffff"
        
        self.root.configure(bg=self.bg_color)
        
        self.setup_variables()
        self.create_widgets()
        self.setup_layout()
        
        # Set up a protocol for when the window is closed
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_variables(self):
        self.is_recording = False
        self.english_text = ""
        self.ipa_text = ""
        self.recording_thread = None
        self.status_var = tk.StringVar(value="Ready")
        self.recording_duration_var = tk.StringVar(value="Recording Duration: 0s")
        self.start_time = 0
        
    def create_widgets(self):
        # Create a style
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Use a modern theme
        
        # Configure styles
        self.style.configure("TFrame", background=self.bg_color)
        self.style.configure("TLabel", font=("Segoe UI", 12), background=self.bg_color, foreground="#333333")
        self.style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"), background=self.bg_color, foreground="#2c3e50")
        self.style.configure("Status.TLabel", font=("Segoe UI", 10), background=self.bg_color, foreground="#7f8c8d")
        
        # Custom button style
        self.style.configure("Accent.TButton", 
                            font=("Segoe UI", 12), 
                            background=self.button_bg, 
                            foreground=self.button_fg)
        self.style.map("Accent.TButton",
                      background=[('active', '#2980b9'), ('pressed', '#1f618d')])
        
        # Header with logo/icon
        self.header_frame = ttk.Frame(self.root, style="TFrame")
        
        self.header_label = ttk.Label(
            self.header_frame, 
            text="English Voice to IPA Transcription", 
            style="Header.TLabel"
        )
        
        self.divider = ttk.Separator(self.root, orient="horizontal")
        
        # Button frame
        self.button_frame = ttk.Frame(self.root, style="TFrame")
        
        # Record button
        self.record_button = ttk.Button(
            self.button_frame,
            text="Start Recording",
            command=self.toggle_recording,
            style="Accent.TButton",
            width=20
        )
        
        # Clear button
        self.clear_button = ttk.Button(
            self.button_frame,
            text="Clear",
            command=self.clear_text,
            style="TButton",
            width=15
        )
        
        # Save button
        self.save_button = ttk.Button(
            self.button_frame,
            text="Save Transcription",
            command=self.save_transcription,
            style="TButton",
            width=20
        )
        
        # Status bar
        self.status_frame = ttk.Frame(self.root, style="TFrame")
        self.status_label = ttk.Label(
            self.status_frame, 
            textvariable=self.status_var,
            style="Status.TLabel"
        )
        self.recording_duration_label = ttk.Label(
            self.status_frame, 
            textvariable=self.recording_duration_var,
            style="Status.TLabel"
        )
        
        # Text display frame
        self.text_frame = ttk.Frame(self.root, style="TFrame")
        
        # English text display
        self.english_label = ttk.Label(
            self.text_frame, 
            text="Original English Text:",
            style="TLabel"
        )
        self.english_text_box = scrolledtext.ScrolledText(
            self.text_frame, 
            wrap=tk.WORD, 
            width=50, 
            height=5,
            font=("Segoe UI", 12),
            background=self.text_bg,
            borderwidth=1,
            relief="solid"
        )
        
        # IPA text display
        self.ipa_label = ttk.Label(
            self.text_frame, 
            text="IPA Transcription:",
            style="TLabel"
        )
        self.ipa_text_box = scrolledtext.ScrolledText(
            self.text_frame, 
            wrap=tk.WORD, 
            width=50, 
            height=10,
            font=("Segoe UI", 12),
            background=self.text_bg,
            borderwidth=1,
            relief="solid"
        )
        
    def setup_layout(self):
        # Configure grid layout
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(3, weight=1)
        
        # Place widgets
        self.header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        self.header_frame.columnconfigure(0, weight=1)
        self.header_label.grid(row=0, column=0)
        
        self.divider.grid(row=1, column=0, sticky="ew", padx=20)
        
        # Button frame layout
        self.button_frame.grid(row=2, column=0, pady=15, sticky="ew")
        self.button_frame.columnconfigure(0, weight=1)
        self.button_frame.columnconfigure(1, weight=1)
        self.button_frame.columnconfigure(2, weight=1)
        
        self.record_button.grid(row=0, column=0, padx=10)
        self.clear_button.grid(row=0, column=1, padx=10)
        self.save_button.grid(row=0, column=2, padx=10)
        
        # Text frame layout
        self.text_frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        self.text_frame.grid_columnconfigure(0, weight=1)
        self.text_frame.grid_rowconfigure(1, weight=1)
        self.text_frame.grid_rowconfigure(3, weight=2)
        
        self.english_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.english_text_box.grid(row=1, column=0, sticky="nsew", pady=(0, 15))
        
        self.ipa_label.grid(row=2, column=0, sticky="w", pady=(0, 5))
        self.ipa_text_box.grid(row=3, column=0, sticky="nsew")
        
        # Status frame layout
        self.status_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        self.status_frame.grid_columnconfigure(0, weight=1)
        self.status_frame.grid_columnconfigure(1, weight=1)
        
        self.status_label.grid(row=0, column=0, sticky="w")
        self.recording_duration_label.grid(row=0, column=1, sticky="e")
        
    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
            
    def start_recording(self):
        self.is_recording = True
        self.record_button.configure(text="Stop Recording")
        self.status_var.set("Recording... (speak now)")
        self.start_time = time.time()
        
        # Start a timer to update recording duration
        self.update_recording_duration()
        
        # Start recording in a separate thread
        self.recording_thread = threading.Thread(target=self.record_and_transcribe)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
    def update_recording_duration(self):
        if self.is_recording:
            elapsed = int(time.time() - self.start_time)
            self.recording_duration_var.set(f"Recording Duration: {elapsed}s")
            self.root.after(1000, self.update_recording_duration)
        
    def stop_recording(self):
        self.is_recording = False
        self.record_button.configure(text="Start Recording")
        self.status_var.set("Processing...")
        
    def record_and_transcribe(self):
        try:
            # Use the model's record_audio function
            audio, recognizer = model.record_audio()
            
            # Signal that recording has stopped
            if not self.is_recording:
                self.root.after(0, lambda: self.status_var.set("Processing transcription..."))
                
                # Use the model's speech_to_text function
                self.english_text = model.speech_to_text(audio, recognizer)
                
                if self.english_text:
                    # Use the model's text_to_ipa function
                    self.ipa_text = model.text_to_ipa(self.english_text)
                    
                    # Update UI with results
                    self.root.after(0, self.update_text_displays)
                else:
                    self.root.after(0, lambda: self.status_var.set("No speech detected or could not understand audio"))
            
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Error: {str(e)}"))
            print(f"Error in recording: {str(e)}")
        finally:
            self.root.after(0, lambda: self.status_var.set("Ready"))
            
    def update_text_displays(self):
        self.english_text_box.delete(1.0, tk.END)
        self.english_text_box.insert(tk.END, self.english_text)
        
        self.ipa_text_box.delete(1.0, tk.END)
        self.ipa_text_box.insert(tk.END, self.ipa_text)
        self.status_var.set("Transcription complete")
        
    def clear_text(self):
        self.english_text_box.delete(1.0, tk.END)
        self.ipa_text_box.delete(1.0, tk.END)
        self.english_text = ""
        self.ipa_text = ""
        self.status_var.set("Cleared")
        
    def save_transcription(self):
        if not self.english_text or not self.ipa_text:
            messagebox.showinfo("No Transcription", "There is no transcription to save.")
            return
            
        # Ask for file location
        default_filename = f"english_ipa_transcription_{time.strftime('%Y%m%d_%H%M%S')}.txt"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=default_filename,
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"Original English text: {self.english_text}\n")
                    f.write(f"IPA transcription: {self.ipa_text}\n")
                messagebox.showinfo("Success", f"Transcription saved to {file_path}")
                self.status_var.set(f"Saved to {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file: {str(e)}")
                
    def on_closing(self):
        if self.is_recording:
            if messagebox.askokcancel("Quit", "Recording in progress. Are you sure you want to quit?"):
                self.is_recording = False
                self.root.destroy()
        else:
            self.root.destroy()

if __name__ == "__main__":
    # Start the application
    root = tk.Tk()
    app = IPATranscriptionApp(root)
    root.mainloop()
