import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk 
from tkinter import font
import requests
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from SpotiBase import SpotiBase
from authRequest import SpOauth
import sqlite3
import io
from io import BytesIO
import pygame
### Main Gui for SpotiFinal by: Alyssa Goldgeisser


def fonts():
    ''' uses tkinter fonts to have font object, outside of classes so all class can use them'''
    available_fonts = list(font.families())
    if 'Gotham Medium' in available_fonts:
        return font.Font(family='Gotham Medium', size=18), font.Font(family='Gotham Medium', size=12)
    else:
        return font.Font(family='Arial', size=18), font.Font(family='Arial', size=12)  # Fallback to Arial if Gothic is not available
 

class MainWindow(tk.Tk):
    def __init__(self):
        ''' mainwindow for spotify class, has 4 main buttons for each of the functions. '''
        super().__init__()
        super().configure(bg='gray8')
        self.title("Spotify Window")
        self.configure(bg='#191414')
        self.font_l, self.font_s = fonts()
        
        self._Icon = ImageTk.PhotoImage(Image.open('Spotify_Icon_RGB_Green.png').resize((70,70), Image.LANCZOS))
        self._logo = tk.Label(self, image=self._Icon, text='Main Menu', font=self.font_l, fg='#1DB954', bg='#191414', relief='flat', compound='left')
        self._logo.grid(row=0, column=0, padx=10, columnspan=4, pady=10, sticky='ew')

        self._newPlaylistButt = tk.Button(self, text='Create new Playlist', font=self.font_s, fg='#1DB954', bg='#191414', command=self.goNewPlaylist)
        self._newPlaylistButt.grid(row=1, sticky='w', padx=10, pady=10)

        self._getReccomendationButt = tk.Button(self, text='Get reccomendations', font=self.font_s, fg='#1DB954', bg='#191414', command=self.goSearch)
        self._getReccomendationButt.grid(row=1, column=1, padx=10, pady=10)

        self._visualizePlaylistButt = tk.Button(self, text='Visualize Playlist', font=self.font_s, fg='#1DB954', bg='#191414', command=self.goVisualize)
        self._visualizePlaylistButt.grid(row=1, column=2, padx=10, pady=10)

        self._searchSongButt = tk.Button(self, text='Search for a song', font=self.font_s, fg='#1DB954', bg='#191414', command=self.goSong)
        self._searchSongButt.grid(row=1, column=3, padx=10, pady=10)

    def goSong(self):
        ''' searches for a song'''
        SearchSong(self)
        
    def goVisualize(self):
        ''' goes to Visualize a plot window '''
        var = 'plot'
        SearchWindow(self, var)

    def goNewPlaylist(self):
        ''' creates NewPlaylist window'''
        NewPlaylist(self)

    def goSearch(self):
        ''' creates SearchWindow window, with option None'''
        SearchWindow(self, None)


class NewPlaylist(tk.Toplevel):
    def __init__(self, master):
        ''' 
        constructor for NewPlaylist class, class asks user for playlist name and description and upon validation,
        calls spotiBase to make a new playlist.
        '''
        super().__init__(master)
        self.title("Name new playlist")
        self.configure(bg='#191414')
        self.font_l, self.font_s = fonts()
        self.transient()
        self.grab_set()
        self.focus_set()
  
        self.new_playlist_label = tk.Label(self,  text='Enter a playlist name: ', font=self.font_s , fg='#1DB954', bg='#191414')
        self.new_playlist_label.grid(row=0, column=0, padx=10, pady=10)

        self.new_playlist_nameVar = tk.StringVar()
        self.new_playlist_name = tk.Entry(self, textvariable=self.new_playlist_nameVar)
        self.new_playlist_name.grid(row=0, column=1, padx=5, pady=5)
 
        self._description_label = tk.Label(self,  text='Enter a description (not required): ', font=self.font_s , fg='#1DB954', bg='#191414')
        self._description_label.grid(row=1, column=0, padx=10, pady=10)

        self._descriptionVar = tk.StringVar()
        self.description_name = tk.Entry(self, textvariable=self._descriptionVar)
        self.description_name.grid(row=1, column=1, padx=5, pady=5)

        self.continueBttn = tk.Button(self, text='Continue', font=self.font_s , fg='#1DB954', bg='#191414', command=self.get_playlist_name)
        self.continueBttn.grid(row=2, column=0, padx=5, pady=5)

    def get_playlist_name(self):
        '''gets the new name of a playlist and upon validation calls sp.create_playlist to create it'''
        self.new_playlist = self.new_playlist_nameVar.get()
        if self.new_playlist == "":
            messagebox.showerror("Error", "Playlist name cannot be empty!")
            self.destroy()
        else:
            self._description = self._descriptionVar.get()
            sp.create_playlist(self.new_playlist, self._description, a.authHeader)
            answer = messagebox.askquestion('Confirmation', f'New playlist: {self.new_playlist} saved, would you like to add songs to the playlist?')
            if answer == 'yes':
                SearchSong(self)
            elif answer == 'no':
                self.destroy()
        
        
class SearchSong(tk.Toplevel):
    def __init__(self, master):
        ''' 
        constructor of the SearchSong class, which calls the SpotiBase search song
        function to search for songs
        '''
        super().__init__(master)
        self.title("Search Window")

        self.configure(bg='#191414')
        self.font_l, self.font_s = fonts()
        self.transient()
        self.grab_set()
        self.focus_set()

        self.label = tk.Label(self, text='Enter a song name', font=self.font_s,  fg='#1DB954', bg='#191414')
        self.label.grid()

        self.song_nameVar = tk.StringVar()
        self.song_name = tk.Entry(self, textvariable=self.song_nameVar)
        self.song_name.grid(padx=5, pady=5)

        self.continueBttn = tk.Button(self, text='Continue', command=self.search_song, font=self.font_s,  fg='#1DB954', bg='#191414')
        self.continueBttn.grid(row=2, column=0, padx=5, pady=5)
        
    def search_song(self):
        ''' gets song var and calls search song function'''
        self.song_var = self.song_nameVar.get()
        result = sp.search_songs(self.song_var, a.authHeader)
        if result == 'fail': 
            messagebox.showinfo('Error', f'{result} is not a valid song name/ No song name was inputted. please try again')
        else:
            ResultWin(self, result)
                   


class SearchWindow(tk.Toplevel):
    def __init__(self, master, new_song):

        ''' 
        constructor for Search window class, has two types of search windows:
        if new_song = None, then we move onto the reccomendation feature
        if new_song is not None, this means that the user wants this song to be
        saved into the playlist, causing a different result.
        This is done to avoid duplicate code.
        '''
        super().__init__(master)
        self.title("listbox window")
        self.configure(bg='#191414')
        self.new_song = new_song

        self.font_l, self.font_s = fonts()
        
        conn = sqlite3.connect('user.db')
        self.cur = conn.cursor()
        self.cur.execute("SELECT * FROM Playlists")
        rows = self.cur.fetchall()

        self.selection_label = tk.Label(self, text='Select one of your playlists', font=self.font_s,  fg='#1DB954', bg='#191414')
        self.selection_label.grid(row=0, column=0, padx=10, columnspan=4, pady=10, sticky='ew')
        
        self.listbox = tk.Listbox(self, font=self.font_l,  fg='#1DB954', bg='#191414')
        for row in rows:
            self.listbox.insert(tk.END, row[2])
        self.listbox.grid(row=1, column=0, padx=10, columnspan=4, pady=10, sticky='ew')

        self.continueBttn = tk.Button(self, text='Continue', command=self.continue_search, font=self.font_s, fg='#1DB954', bg='#191414')
        self.continueBttn.grid(row=2, column=0, padx=10, columnspan=4, pady=10, sticky='ew')

        if self.new_song == 'plot':
            self.selected_option = tk.StringVar()
            self.selected_option.set("1")
            self.radio_button1 = tk.Radiobutton(self, text="Plot AudioFeatures", variable=self.selected_option, value="1", font=self.font_s,  fg='#1DB954', bg='#191414')
            self.radio_button2 = tk.Radiobutton(self, text="Plot Genres ", variable=self.selected_option, value="2", font=self.font_s,  fg='#1DB954', bg='#191414')

            self.radio_button1.grid(row=3, column=0, padx=10, pady=10, sticky='w')
            self.radio_button2.grid(row=3, column=1, padx=10, pady=10, sticky='e')
        
    def continue_search(self):
        ''' 
        fetches from database the playlists data, and depending 
        on the value of new_song, either calls resultWin or just
        adds to playlist. 
        '''
        item = self.listbox.get(self.listbox.curselection())
        self.cur.execute("SELECT * FROM Playlists WHERE name = ?", (item,))
        row = self.cur.fetchone()
        if self.new_song == None:
            try:
                _, table = sp.recommend(playlist_id=row[0], auth=a.authHeader)
                ResultWin(self, table)
            except TypeError: # since the return from SpotiBase is a status code integer not something iterable, we can have this exception
                messagebox.showinfo('Error', f'{item} is empty playlist. Please try again ')
        elif self.new_song == 'plot':
            result = sp.is_playlist_empty(row[0])
            if result == 'not empty':
                choice = self.selected_option.get()
                display = tk.Toplevel()
                if choice == '1':
                    self.fig = sp.plotFeatures(playlist_id=row[0], auth=a.authHeader)
                else:
                    self.fig = sp.plotPie(playlist_id=row[0], auth=a.authHeader)
                canvas = FigureCanvasTkAgg(self.fig, master=display)
                canvas.get_tk_widget().grid()
                canvas.draw()
            else:
                messagebox.showinfo('Error', f'{item} is empty playlist. Please try again ')
        else:
            print(row)
            sp.updatePlaylist(playlist_id=row[0], trackData=self.new_song)
            sp.addItems(auth=a.authHeader, playlist_id=row[1])
            messagebox.showinfo('Confirmation', f'Your song was saved in {row[2]}')
            self.destroy()


class ResultWin(tk.Toplevel):
    def __init__(self, master, table):

        ''' 
        constructor for ResultWin class, which uses the dictionary given to it by SpotiBase
        from the other classes. Then, takes all the songs from this dictionary and stores
        it into a listbox for user selection.     
        '''
        super().__init__(master)
        self.title("Display")
        self.configure(bg='#191414')
        self.font_l, self.font_s = fonts()
        self.table = table

        self.song_listbox = tk.Listbox(self, font=self.font_s, height=10, width=40,  fg='#1DB954', bg='#191414')
        for key in table:
            self.song_listbox.insert(tk.END, key)
        self.song_listbox.grid(row=1, column=1, padx=10, pady=10)

        self.continueBttn = tk.Button(self, text='Continue', command=self.continue_search, font=self.font_s, fg='#1DB954', bg='#191414')
        self.continueBttn.grid(row=2, column=1, padx=10, pady=10)
        
    def continue_search(self):
        ''' gets the item of the listbox, and passes that specific key and value into the songWin'''
        item = self.song_listbox.get(self.song_listbox.curselection())
        SongWin(self, item, self.table[item])
        

class SongWin(tk.Toplevel):
    def __init__(self, master, title, info):
        ''' 
        Constructor for SongWin class, simple window that displays song information and allows
        user to play the song (if the song has a preview) and save the song into a playlist.
        '''
        super().__init__(master)
        self.title("Display")
        self.configure(bg='#191414')
        self.font_l, self.font_s = fonts()
        self.info = info
        self.title = title

        self.song_label = tk.Label(self, text=title, font=self.font_s, fg='#1DB954', bg='#191414')
        self.song_label.grid()

        self.album_label = tk.Label(self, text=info[4], font=self.font_s, fg='#1DB954', bg='#191414')
        self.album_label.grid()

        self.artist_label = tk.Label(self, text=info[6][0], font=self.font_s, fg='#1DB954', bg='#191414')
        self.artist_label.grid()

        duration = self.format_duration(info[3]) # duration is given in ms, calls function to format into minutes:seconds
        self.duration_label = tk.Label(self, text=duration, font=self.font_s, fg='#1DB954', bg='#191414')
        self.duration_label.grid()

        self.createImage() 

        if info[1] != None: # checking if the song has a preview, otherwise no need to create the play button
            play_button = tk.Button(self, text="Play Audio", command=lambda: self.on_play_button_click(self.info[1]))
            play_button.grid()

        self.save_button = tk.Button(self, text="Save to playlist?", command=self.save_to_playlist)
        self.save_button.grid()

    def save_to_playlist(self):
        combined_list = [self.title] + self.info
        print(combined_list)
        SearchWindow(self, combined_list)

    def format_duration(self, milliseconds):
        ''' changes ms to minutes:seconds'''
        total_seconds = milliseconds // 1000
        minutes = total_seconds // 60
        remaining_seconds = total_seconds % 60
        return f"{minutes}:{remaining_seconds:02}"

    def createImage(self):
        ''' creates image from link using various python modules'''
        try:
            response = requests.get(self.info[5])
            response.raise_for_status()  # Check that the request was successful
            img_data = BytesIO(response.content)
            img = Image.open(img_data)
            self._albumImage = ImageTk.PhotoImage(img.resize((200,200)))
            label = tk.Label(self, image=self._albumImage)
            label.grid()
        except requests.exceptions.HTTPError as err:
            raise SystemExit(f"Error processing request:  {err}")

    def fetch_audio(self, url):
        ''' does a request to fetch the audio for the player'''
        try:
            response = requests.get(url)
            response.raise_for_status()  # Check that the request was successful
            # TODO: same as above
            return io.BytesIO(response.content)
        except requests.exceptions.HTTPError as err:
            raise SystemExit(f"Error processing request:  {err}")
            
    def play_audio(self, audio_data):
        ''' plays audio '''
        pygame.mixer.init()
        pygame.mixer.music.load(audio_data)
        pygame.mixer.music.play()

    def on_play_button_click(self, url):
        ''' command on play button '''
        audio_data = self.fetch_audio(url)
        self.play_audio(audio_data)
    

if __name__ == "__main__":
    a = SpOauth()
    sp = SpotiBase(a.authHeader)
    if a:
        win = MainWindow()
        win.mainloop()

