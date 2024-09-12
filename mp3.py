import os
import tkinter as tk
from tkinter import ttk
import pygame
from tkinter import PhotoImage
import random
import threading
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class SashifyPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Sashify Player")
        self.shuffle_state = False
        self.current_playlist = None
        self.current_artist = None

        pygame.mixer.init()
        self.liked_songs = {}
        self.volume = tk.DoubleVar()
        self.volume.set(0.5)  # Initial volume (0.0 to 1.0)
        self.paused = False

        # Artist information
        self.artist_info = {
            'Taylor Swift': "Taylor Swift is an American singer-songwriter known for her narrative songs "
                             "about her personal life. She has received various awards and recognition "
                             "for her work, including 11 Grammy Awards.",
            'Ed Sheeran': "Ed Sheeran is an English singer-songwriter known for his acoustic pop and R&B style. "
                           "He has achieved great success with hits like 'Shape of You' and 'Thinking Out Loud'.",
            'Arijit Singh': "Arijit Singh is an Indian playback singer known for his soulful and melodious voice. "
                             "He has sung numerous hit songs in various languages.",
            'Pritam': "Pritam is an Indian music director and composer known for his work in Bollywood. "
                       "He has composed music for a wide range of films and genres."
        }

        # Initialize the player with pre-loaded songs
        self.playlists = {
            'Hindi': {
                'Arijit Singh': ['/Users/shauryayaduvanshi/Desktop/media/music/Hin/as/Chaleya.mp3',''],
                'Pritam': ['//Users/shauryayaduvanshi/Desktop/media/music/Hin/P/Khaiyriat.mp3']
            },
            'English': {
                'Taylor Swift': ['/Users/shauryayaduvanshi/Desktop/media/music/Eng/ts/Blank Space.mp3'],
                'Ed Sheeran': ['/Users/shauryayaduvanshi/Desktop/media/music/Eng/Ed/Perfect.mp3']
            }
        }

        self.setup_background()
        self.create_ui()
        self.setup_visualizer()

    def setup_background(self):
        background_image = PhotoImage(file="/Users/shauryayaduvanshi/Desktop/media/Background/a.png")
        background_label = tk.Label(self.root, image=background_image)
        background_label.place(relwidth=1, relheight=1)
        background_label.image = background_image

    def create_ui(self):
        control_frame = tk.Frame(self.root, bg="#2E4053")  # Dark Blue
        control_frame.pack()

        style = ttk.Style()
        style.configure("TButton", padding=5, font=("Helvetica", 14), background="#5D6D7E")  # Light Blue

        self.play_button = ttk.Button(control_frame, text="Play", command=self.play_music)
        self.pause_button = ttk.Button(control_frame, text="Pause", command=self.pause_music)
        self.stop_button = ttk.Button(control_frame, text="Stop", command=self.stop_music)
        self.shuffle_button = ttk.Button(control_frame, text="Shuffle", command=self.toggle_shuffle)
        self.skip_forward_button = ttk.Button(control_frame, text="Skip +10s", command=self.skip_forward)
        self.skip_backward_button = ttk.Button(control_frame, text="Skip -10s", command=self.skip_backward)

        self.play_button.grid(row=0, column=0, padx=5, pady=5)
        self.pause_button.grid(row=0, column=1, padx=5, pady=5)
        self.stop_button.grid(row=0, column=2, padx=5, pady=5)
        self.shuffle_button.grid(row=0, column=3, padx=5, pady=5)
        self.skip_backward_button.grid(row=0, column=4, padx=5, pady=5)
        self.skip_forward_button.grid(row=0, column=5, padx=5, pady=5)

        self.current_playlist_label = tk.Label(self.root, text="Current Playlist: None", bg="#2E4053", fg="white")  # Dark Blue
        self.current_playlist_label.pack(fill=tk.X)

        self.artist_title_label = tk.Label(self.root, text="About the Artist", bg="#2E4053", fg="white", font=("Helvetica", 16))  # Dark Blue
        self.artist_title_label.pack()

        self.artist_info_text = tk.Text(
            self.root,
            height=5,
            width=50,
            wrap=tk.WORD,
            bg="#2E4053",
            fg="white",
            font=("Helvetica", 14),  # Adjust the text size as needed
        )
        self.artist_info_text.pack()

        self.playlist_selector = ttk.Combobox(self.root, values=list(self.playlists.keys()), style="TButton")
        self.playlist_selector.set("Select Playlist")
        self.playlist_selector.bind("<<ComboboxSelected>>", self.change_playlist)
        self.playlist_selector.pack(pady=10)

        self.artist_selector = ttk.Combobox(self.root, style="TButton")
        self.artist_selector.set("Select Artist")
        self.artist_selector.bind("<<ComboboxSelected>>", self.change_artist)
        self.artist_selector.pack(pady=10)

        self.playlist_box = tk.Listbox(self.root, bg="#34495E", fg="white", selectbackground="#5D6D7E", selectmode=tk.SINGLE)  # Dark Blue
        self.playlist_box.pack(fill=tk.BOTH, expand=True)

        # Volume Slider
        volume_frame = tk.Frame(self.root, bg="#2E4053")  # Dark Blue
        volume_frame.pack(pady=10)

        volume_label = tk.Label(volume_frame, text="Volume", bg="#2E4053", fg="white")  # Dark Blue
        volume_label.pack(side=tk.LEFT, padx=10)

        volume_scale = ttk.Scale(volume_frame, orient=tk.HORIZONTAL, variable=self.volume, from_=0.0, to=1.0, command=self.change_volume)
        volume_scale.pack(side=tk.LEFT, padx=10)
        volume_scale.set(0.5)  # Set initial volume position

        # Initialize the playlist box with songs from the selected playlist and artist
        self.change_playlist(None)

    def setup_visualizer(self):
        visualizer_frame = tk.Frame(self.root, bg="#000000")  # Black
        visualizer_frame.pack(fill=tk.BOTH, expand=True)

        self.fig, self.ax = plt.subplots(subplot_kw=dict(polar=True), figsize=(6, 6), tight_layout=True)
        self.canvas = FigureCanvasTkAgg(self.fig, master=visualizer_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Start a separate thread for the visualizer
        self.visualizer_thread = threading.Thread(target=self.update_visualizer)
        self.visualizer_thread.daemon = True
        self.visualizer_thread.start()

    def update_visualizer(self):
        while True:
            if pygame.mixer.music.get_busy():
                current_time = pygame.mixer.music.get_pos() / 1000.0
                angle = (current_time % 10) / 10 * 2 * np.pi
                values = np.random.rand(10)  # You can replace this with actual frequency data
                self.ax.clear()
                self.ax.plot(np.linspace(0, 2 * np.pi, 10), values, color='blue', linewidth=2)
                self.ax.set_rmax(1)
                self.ax.set_rticks([])
                self.ax.set_yticklabels([])
                self.ax.set_xticklabels([])
                self.ax.set_rlabel_position(0)
                self.ax.set_theta_offset(angle)
                self.canvas.draw()
                self.canvas.flush_events()

    def play_music(self):
        if self.paused:
            pygame.mixer.music.unpause()
            self.paused = False
        else:
            if self.shuffle_state:
                self.shuffle_playlist()

            selected_song = self.playlist_box.curselection()
            if selected_song:
                selected_song = selected_song[0]
                song = self.playlists[self.current_playlist][self.current_artist][selected_song]
                pygame.mixer.music.load(song)
                pygame.mixer.music.set_volume(self.volume.get())
                pygame.mixer.music.play()

                self.current_playlist_label.config(text=f"Current Playlist: {self.current_playlist} - {self.current_artist}")

                # Display artist information when an artist is selected
                artist_info = self.artist_info.get(self.current_artist, "")
                self.artist_info_text.delete(1.0, tk.END)
                self.artist_info_text.insert(tk.END, artist_info)

    def pause_music(self):
        pygame.mixer.music.pause()
        self.paused = True

    def stop_music(self):
        pygame.mixer.music.stop()

    def toggle_shuffle(self):
        if self.shuffle_state:
            self.shuffle_state = False
        else:
            self.shuffle_state = True

    def shuffle_playlist(self):
        random.shuffle(self.playlists[self.current_playlist][self.current_artist])

    def skip_forward(self):
        current_time = pygame.mixer.music.get_pos() // 1000  # Current time in seconds
        new_time = current_time + 10
        pygame.mixer.music.set_pos(new_time)

    def skip_backward(self):
        current_time = pygame.mixer.music.get_pos() // 1000  # Current time in seconds
        new_time = max(0, current_time - 10)
        pygame.mixer.music.set_pos(new_time)

    def change_volume(self, value):
        pygame.mixer.music.set_volume(float(value))

    def change_playlist(self, event):
        self.current_playlist = self.playlist_selector.get()
        artists = list(self.playlists.get(self.current_playlist, {}).keys())
        self.artist_selector['values'] = artists
        self.artist_selector.set("Select Artist")

        # Automatically load all songs into the sub-playlist (artist) when selecting a playlist
        self.playlist_box.delete(0, tk.END)
        for artist_name, songs in self.playlists.get(self.current_playlist, {}).items():
            self.playlist_box.insert(tk.END, *map(os.path.basename, songs))

    def change_artist(self, event):
        self.current_artist = self.artist_selector.get()

        # Show only the songs from the selected sub-playlist (artist)
        self.playlist_box.delete(0, tk.END)
        for song in self.playlists.get(self.current_playlist, {}).get(self.current_artist, []):
            self.playlist_box.insert(tk.END, os.path.basename(song))

if __name__ == "__main__":
    root = tk.Tk()
    app = SashifyPlayer(root)
    root.mainloop()
