import os
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

import english_to_ipa_model as model


class NorthwestAccentCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Northwest American English Accent Checker")
        self.root.geometry("1200x900")
        self.root.minsize(980, 780)
        
        # Set theme colors
        self.bg_color = "#0f172a"
        self.surface_color = "#e2e8f0"
        self.panel_color = "#f8fafc"
        self.accent_color = "#0ea5e9"
        self.accent_hover = "#0284c7"
        self.text_bg = "#ffffff"
        self.button_fg = "#f8fafc"
        
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
        self.recording_duration_var = tk.StringVar(value="Recording: 0s")
        self.start_time = 0
        self.analysis_result = None
        self.lexicon = model.load_northwest_american_lexicon()
        
    def create_widgets(self):
        # Create a style
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Use a modern theme
        
        # Configure styles
        self.style.configure("TFrame", background=self.bg_color)
        self.style.configure("Card.TFrame", background=self.panel_color)
        self.style.configure("TLabel", font=("Bahnschrift", 12), background=self.panel_color, foreground="#0f172a")
        self.style.configure("Header.TLabel", font=("Bahnschrift", 24, "bold"), background=self.bg_color, foreground="#f8fafc")
        self.style.configure("Subheader.TLabel", font=("Bahnschrift", 11), background=self.bg_color, foreground=self.surface_color)
        self.style.configure("Status.TLabel", font=("Bahnschrift", 10), background=self.bg_color, foreground="#cbd5e1")
        self.style.configure("PanelTitle.TLabel", font=("Bahnschrift", 12, "bold"), background=self.panel_color, foreground="#0f172a")
        
        # Custom button style
        self.style.configure(
            "Accent.TButton",
            font=("Bahnschrift", 12, "bold"),
            background=self.accent_color,
            foreground=self.button_fg,
        )
        self.style.map(
            "Accent.TButton",
            background=[('active', self.accent_hover), ('pressed', '#0369a1')],
            foreground=[('active', '#ffffff'), ('pressed', '#ffffff')],
        )

        self.style.configure("Ghost.TButton", font=("Bahnschrift", 11), padding=(8, 5))
        
        # Header with logo/icon
        self.header_frame = ttk.Frame(self.root, style="TFrame")
        
        self.header_label = ttk.Label(
            self.header_frame, 
            text="Northwest American English Accent Checker", 
            style="Header.TLabel"
        )
        self.subheader_label = ttk.Label(
            self.header_frame,
            text="Speak naturally. The app analyzes pronunciation using a Northwest-oriented dictionary with stress-aware IPA.",
            style="Subheader.TLabel"
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
            style="Ghost.TButton",
            width=15
        )
        
        # Save button
        self.save_button = ttk.Button(
            self.button_frame,
            text="Save Report",
            command=self.save_report,
            style="Ghost.TButton",
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
        self.text_frame = ttk.Frame(self.root, style="Card.TFrame", padding=(18, 14))

        self.prompt_label = ttk.Label(
            self.text_frame,
            text="Sentence you will pronounce:",
            style="PanelTitle.TLabel"
        )
        self.prompt_text_box = scrolledtext.ScrolledText(
            self.text_frame,
            wrap=tk.WORD,
            width=50,
            height=3,
            font=("Bahnschrift", 12),
            background=self.text_bg,
            borderwidth=1,
            relief="solid"
        )

        # English text display
        self.english_label = ttk.Label(
            self.text_frame, 
            text="Recognized speech:",
            style="PanelTitle.TLabel"
        )
        self.english_text_box = scrolledtext.ScrolledText(
            self.text_frame, 
            wrap=tk.WORD, 
            width=50, 
            height=4,
            font=("Bahnschrift", 12),
            background=self.text_bg,
            borderwidth=1,
            relief="solid"
        )
        
        # IPA text display
        self.ipa_label = ttk.Label(
            self.text_frame, 
            text="IPA output:",
            style="PanelTitle.TLabel"
        )
        self.ipa_text_box = scrolledtext.ScrolledText(
            self.text_frame, 
            wrap=tk.WORD, 
            width=50, 
            height=7,
            font=("Bahnschrift", 12),
            background=self.text_bg,
            borderwidth=1,
            relief="solid"
        )

        self.score_label = ttk.Label(
            self.text_frame,
            text="Score summary:",
            style="PanelTitle.TLabel"
        )
        self.score_text_box = scrolledtext.ScrolledText(
            self.text_frame,
            wrap=tk.WORD,
            width=50,
            height=22,
            font=("Consolas", 11),
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
        self.subheader_label.grid(row=1, column=0, pady=(4, 2))
        
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
        self.text_frame.grid_rowconfigure(3, weight=1)
        self.text_frame.grid_rowconfigure(5, weight=1)
        self.text_frame.grid_rowconfigure(7, weight=3)

        self.prompt_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.prompt_text_box.grid(row=1, column=0, sticky="nsew", pady=(0, 12))
        
        self.english_label.grid(row=2, column=0, sticky="w", pady=(0, 5))
        self.english_text_box.grid(row=3, column=0, sticky="nsew", pady=(0, 12))
        
        self.ipa_label.grid(row=4, column=0, sticky="w", pady=(0, 5))
        self.ipa_text_box.grid(row=5, column=0, sticky="nsew", pady=(0, 12))

        self.score_label.grid(row=6, column=0, sticky="w", pady=(0, 5))
        self.score_text_box.grid(row=7, column=0, sticky="nsew")
        
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
        prompt_text = self.prompt_text_box.get(1.0, tk.END).strip()
        if not prompt_text:
            messagebox.showwarning("Sentence Required", "Please enter the sentence you will pronounce.")
            self.status_var.set("Sentence required")
            return

        audio_ok, audio_msg = model.validate_audio_backend()
        if not audio_ok:
            self.status_var.set("Audio setup issue")
            messagebox.showerror(
                "Audio Backend Error",
                f"{audio_msg}\n\n"
                "If you are using a virtual environment, install PyAudio in that same environment "
                "and restart VS Code.",
            )
            return

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
            audio, recognizer = model.record_audio()
            
            # Signal that recording has stopped
            if not self.is_recording:
                self.root.after(0, lambda: self.status_var.set("Processing transcription..."))
                
                self.english_text = model.speech_to_text(audio, recognizer)
                prompt_text = self.prompt_text_box.get(1.0, tk.END).strip()
                
                self.analysis_result = model.analyze_prompt_vs_recognized(
                        prompt_text=prompt_text,
                        recognized_text=self.english_text,
                        lexicon=self.lexicon,
                    )

                self.ipa_text = (
                    f"Expected IPA (from your sentence):   {self.analysis_result['expected_dictionary_ipa']}\n"
                    f"Recognized IPA (from audio text):    {self.analysis_result['recognized_dictionary_ipa']}\n\n"
                    f"Expected IPA stress-neutral:         {self.analysis_result['expected_dictionary_ipa_no_stress']}\n"
                    f"Recognized IPA stress-neutral:       {self.analysis_result['recognized_dictionary_ipa_no_stress']}"
                )

                self.root.after(0, self.update_text_displays)
            
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
        self.score_text_box.delete(1.0, tk.END)

        if self.analysis_result:
            lexical = self.analysis_result["lexical_accuracy"] * 100
            ipa_sim = self.analysis_result["ipa_similarity"] * 100
            prof = self.analysis_result["proficiency_score"] * 100
            issue_words = [row for row in self.analysis_result["word_rows"] if row.get("has_phoneme_issue")]
            missing_words = [row for row in self.analysis_result["word_rows"] if row.get("missing_from_recognition")]

            summary = [
                f"Assessment: {self.analysis_result['assessment']}",
                f"Sentence match accuracy: {lexical:.1f}%",
                f"IPA similarity: {ipa_sim:.1f}%",
                f"Northwest proficiency score: {prof:.1f}%",
                "",
                f"Words with potential incorrect phonemes: {len(issue_words)}",
                f"Words missing from recognition: {len(missing_words)}",
                "",
                "Phoneme correction targets:",
            ]

            if self.analysis_result.get("recognition_failed"):
                summary.append("- Speech recognition did not decode your audio clearly.")
                summary.append("- The app still analyzed your intended sentence IPA as a target.")
                summary.append("")

            if issue_words:
                for row in issue_words:
                    summary.append(
                        f"- {row['expected_word']}: target {row['expected_ipa']} | observed {row['recognized_ipa']}"
                    )
                    for mismatch in row["mismatch_segments"]:
                        summary.append(
                            f"  expected '{mismatch['expected']}' but heard-like '{mismatch['observed']}'"
                        )
            else:
                summary.append("- No phoneme mismatch was detected for in-dictionary words.")

            if missing_words:
                summary.append("")
                summary.append("Words not recognized from your target sentence:")
                for row in missing_words:
                    summary.append(f"- {row['expected_word']} (target IPA: {row['expected_ipa']})")

            summary.extend([
                "",
                "Word-by-word target vs recognized mapping:",
            ])

            for row in self.analysis_result["word_rows"]:
                if row["missing_from_recognition"]:
                    marker = "MISS"
                elif row["word_match"]:
                    marker = "OK"
                else:
                    marker = "DIFF"
                summary.append(
                    f"[{marker}] target '{row['expected_word']}' ({row['expected_ipa']}) "
                    f"recognized '{row['recognized_word']}' ({row['recognized_ipa']})"
                )

            self.score_text_box.insert(tk.END, "\n".join(summary))

        self.status_var.set("Analysis complete")
        
    def clear_text(self):
        self.prompt_text_box.delete(1.0, tk.END)
        self.english_text_box.delete(1.0, tk.END)
        self.ipa_text_box.delete(1.0, tk.END)
        self.score_text_box.delete(1.0, tk.END)
        self.english_text = ""
        self.ipa_text = ""
        self.analysis_result = None
        self.status_var.set("Cleared")
        
    def save_report(self):
        if not self.analysis_result:
            messagebox.showinfo("No Report", "Run an analysis before saving.")
            return
            
        # Ask for file location
        default_filename = f"northwest_accent_report_{time.strftime('%Y%m%d_%H%M%S')}.txt"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=default_filename,
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("Northwest American English Accent Report\n")
                    f.write("========================================\n\n")
                    f.write(f"Target Sentence: {self.analysis_result['prompt_text']}\n")
                    f.write(f"Recognized Speech: {self.analysis_result['spoken_text']}\n\n")
                    f.write(f"Expected IPA with stress:   {self.analysis_result['expected_dictionary_ipa']}\n")
                    f.write(f"Recognized IPA with stress: {self.analysis_result['recognized_dictionary_ipa']}\n")
                    f.write(f"Expected IPA stress-neutral:   {self.analysis_result['expected_dictionary_ipa_no_stress']}\n")
                    f.write(f"Recognized IPA stress-neutral: {self.analysis_result['recognized_dictionary_ipa_no_stress']}\n\n")
                    f.write(f"Sentence match accuracy: {self.analysis_result['lexical_accuracy'] * 100:.1f}%\n")
                    f.write(f"IPA similarity: {self.analysis_result['ipa_similarity'] * 100:.1f}%\n")
                    f.write(f"Northwest proficiency score: {self.analysis_result['proficiency_score'] * 100:.1f}%\n")
                    f.write(f"Assessment: {self.analysis_result['assessment']}\n")
                    f.write("\nPhoneme correction targets:\n")
                    issue_words = [row for row in self.analysis_result["word_rows"] if row.get("has_phoneme_issue")]
                    if issue_words:
                        for row in issue_words:
                            f.write(
                                f"- {row['expected_word']}: target {row['expected_ipa']} | observed {row['recognized_ipa']}\n"
                            )
                            for mismatch in row["mismatch_segments"]:
                                f.write(
                                    f"  expected '{mismatch['expected']}' but heard-like '{mismatch['observed']}'\n"
                                )
                    else:
                        f.write("- No phoneme mismatch was detected for in-dictionary words.\n")

                    missing_words = [row for row in self.analysis_result["word_rows"] if row.get("missing_from_recognition")]
                    if missing_words:
                        f.write("\nWords not recognized from target sentence:\n")
                        for row in missing_words:
                            f.write(f"- {row['expected_word']} (target IPA: {row['expected_ipa']})\n")
                messagebox.showinfo("Success", f"Report saved to {file_path}")
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
    root = tk.Tk()
    app = NorthwestAccentCheckerApp(root)
    root.mainloop()
