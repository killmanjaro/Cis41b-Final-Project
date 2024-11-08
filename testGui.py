import tkinter as tk
import tkinter.messagebox as tkmb
from PIL import Image, ImageTk 
import requests
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
import webbrowser
from SpotiBase import SpotiBase
from authRequest import SpOauth

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        super().config(bg="#191414")
        super().title("SpotiFinal")
        icon = ImageTk.PhotoImage(Image.open('Spotify_icon_RGB_Green.png'))
        super().wm_iconphoto(False, icon)

        self._auth = SpOauth()
        self._base = SpotiBase(self._auth.authHeader)

        self._logo = ImageTk.PhotoImage(Image.open('Spotify_logo_RGB_Green.png').resize((70,21), Image.LANCZOS))
        self._icon = ImageTk.PhotoImage(Image.open('Spotify_icon_RGB_Green.png').resize((80,80), Image.LANCZOS))


        self._banner = tk.Label(self, text="Powered by  ", font=("helvetica", 10, "bold"),compound="right",image=self._logo, bg="#191414",fg="#1DB954", justify="left").grid(row=0,column=0, sticky="nw")
        self._title = tk.Label(self, image=self._icon, compound="left", text="Spotifinal", bg="#191414", fg="#1DB954",font=("helvetica", 50, "bold"), justify="center").grid(row=1,column=0)
        self._desc = tk.Label(self, text="Create playlists,\nget recommendations based on your tastes,\nor visualize your playlist's vibes and composition", bg="#191414", fg="#1DB954",font=("helvetica", 18,), justify="center").grid(row=2,column=0)


        self._frame = tk.Frame(self, bg="#191414")
        self._frame.grid(row=3,column=0, pady=50)

        self._playlistButt = tk.Button(self._frame, text="Create a New Playlist", bg="gray19",fg="white", relief="flat", font=("helvetica", 12, "bold"), justify="center", command=self.createPlaylist)
        self._playlistButt.grid(row=0,column=0, padx=10)

        self._reccButt = tk.Button(self._frame, text="Get a Reccomendation", bg="gray19", fg="white",relief="flat", font=("helvetica", 12, "bold"), justify="center", command=self.getRecc)
        self._reccButt.grid(row=0,column=1, padx=10)

        self._visButt = tk.Button(self._frame, text="View Your Tastes", bg="gray19",fg="white", relief="flat", font=("helvetica", 12, "bold"), justify="center", command=self.visData)
        self._visButt.grid(row=0, column=2, padx=10)

    def createPlaylist(self):
        create = NamePlaylist(self)
        self.wait_window(create)
        playlistName = create._name
        playlistDesc = create._desc
        status = self._base.create_playlist(playlistName, playlistDesc, self._auth.authHeader)
        self._base.saves.clear()
        if status == "fail":
            tkmb.showerror(self, message="Something went wrong making your playlist")
        else:
            tkmb.showinfo(self, message=f"Playlist {playlistName} successfull created")
            key, id = status
            Search(self, playlist_key=key, playlist_id=id, dbObj=self._base, authObj=self._auth)

    
    def getRecc(self):
        pass
    def visData(self):
        pass

class NamePlaylist(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        super().config(bg="#191414")

        self._name = None
        self._desc = None

        self._nameVar = tk.StringVar()
        self._entryLabel = tk.Label(self, text="Name: ", font=("helvetica", 12, "bold"), bg="#191414", fg="white").grid(row=0,column=0)
        self._nameEntry = tk.Entry(self, textvariable=self._nameVar, font=("helvetica", 12), relief="flat", fg="white", bg="gray19")
        self._nameEntry.grid(row=0, column=1)

        self._descVar = tk.StringVar()
        self._descLabel = tk.Label(self, text="Description: ", font=("helvetica", 12, "bold"), bg="#191414", fg="white").grid(row=1,column=0)
        self._descEntry = tk.Entry(self, textvariable=self._descVar, font=("helvetica", 12), relief="flat", fg="white", bg="gray19" )
        self._descEntry.grid(row=1,column=1)

        self._submit = tk.Button(self, text="Submit", fg="white", bg="gray19", font=("helvetica", 12), command=self.createPlaylist)
        self._submit.grid(row=2,column=1)

    def createPlaylist(self):
        self._name = self._nameVar.get()
        self._desc = self._descVar.get()
        self.destroy()

class Search(tk.Toplevel):
    def __init__(self, master, playlist_key:int, playlist_id:str, dbObj:object, authObj:object):
        super().__init__(master)
        super().config(bg="#191414")

        self._base2 = dbObj
        self._auth2 = authObj
        self._playlistDB = playlist_key
        self._spotifID = playlist_id

        self._title = tk.Label(self, text="Search for Songs", bg="#191414", fg="#1DB954",font=("helvetica", 24, "bold"), justify="center").grid(row=0,column=0)
        
        self._searchFrame = tk.Frame(self, bg="#191414")
        self._searchFrame.grid(row=1, column=0)

        self._searchVar = tk.StringVar()
        self._searchLabel = tk.Label(self._searchFrame, text="Search: ", font=("helvetica", 12, "bold"), bg="#191414", fg="white").grid(row=0,column=0)
        self._searchEntry = tk.Entry(self._searchFrame, textvariable=self._searchVar, font=("helvetica", 12), relief="flat", fg="white", bg="gray19")
        self._searchEntry.grid(row=0, column=1)

        self._submit = tk.Button(self, text="Submit", fg="white", bg="gray19", relief="flat",font=("helvetica", 12, "bold"), command=self.fetchResults)
        self._submit.grid(row=2,column=0)

        self.protocol("WM_DELETE_WINDOW", self.saveToPlaylist)
        
    def fetchResults(self):
        userIn = self._searchVar.get().strip()
        if userIn:
            results = self._base2.search_songs(userIn, self._auth2.authHeader)
            if results == "fail":
                tkmb.showerror(self, message="No Results")
            SearchResults(self, results, self._playlistDB, self._base2)
        else:
            tkmb.showerror(self, message="Invalid Search")
        
    def saveToPlaylist(self):
        status = self._base2.addItems(auth=self._auth2.authHeader, playlist_id = self._spotifID)

        if status == 200:
            tkmb.showinfo(self, message="Tracks successfully added to your new playlist.")

        elif status == 401:
            accept = tkmb.askokcancel(self, message="You haven't saved any tracks in your search. 'ok' to continue without saving or continue searching")
            if accept:
                self.destroy()

        elif status == 400:
            accept = tkmb.askretrycancel(self, message="Something went wrong. Would you like to retry the submission, or exit without saving to playlist.")
            if accept:
                self.saveToPlaylist()
            else:
                self.destroy()

class SearchResults(tk.Toplevel):
    def __init__(self, master, data, playlist_key, dbObj):
        super().__init__(master)
        super().config(bg="#191414")
        super().resizable(False, False)
        self._base3 = dbObj
        self._playlistKey = playlist_key
        self._resultsTable = data

        self._logo = ImageTk.PhotoImage(Image.open('Spotify_Logo_RGB_Green.png').resize((350,105), Image.LANCZOS))
        #self._banner = tk.Label(self, image=self._logo, bg='#191414')
        #self._banner.grid(row=0,column=0,padx=10, pady=10)

        self._results = tk.Label(self, image=self._logo, compound="top", text="Spotifinal", bg="#191414", fg="#1DB954",font=("helvetica", 50, "bold"), justify="center").grid(row=0,column=0)
        
        self._resultBox = tk.Listbox(self, height=10, width=50, selectmode="single", font=("helvetica", 12), bg="gray19", fg="white")
        self._resultBox.grid(row=1, column=0)

        for row in self._resultsTable:
            self._resultBox.insert(tk.END, f"{row[1]} - {', '.join(row[7])}")
        
        self._resultBox.bind("<<ListboxSelect>>", self.showResults)

    def showResults(self, event):
        selection = self._resultBox.curselection()
        self._resultBox.selection_clear(0, tk.END)
        DisplayWindow(self, self._resultsTable[selection[0]], playlist_key=self._playlistKey, dbObj=self._base3)

class DisplayWindow(tk.Toplevel):
    def __init__(self, master, trackData, playlist_key, dbObj):
        super().__init__(master)
        super().config(bg='#191414')
        #super().geometry("410x550")
        super().resizable(False, False)

        self._trackData = trackData
        self._playlistKey = playlist_key
        self._base4 = dbObj

        self._logo = ImageTk.PhotoImage(Image.open('Spotify_Logo_RGB_Green.png').resize((350,105), Image.LANCZOS))
        self._banner = tk.Label(self, image=self._logo, bg='#191414')
        self._banner.grid(row=0,column=0,padx=10, pady=10)

        self._frame = tk.Frame(self, bg='#191414')
        self._frame.grid(row=2,column=0, padx=10)

        self._im = ImageTk.PhotoImage(Image.open(requests.get(self._trackData[6], stream=True).raw))
        self._album = tk.Label(self._frame, image=self._im, justify="center")
        self._album.grid(row=0,column=0)

        ms = self._trackData[4]
        total_seconds = ms // 1000
        minutes = total_seconds // 60
        seconds= total_seconds % 60

        self._desc = tk.Label(self._frame, text = self._trackData[1], bg='#191414', fg="white", font=('helvetica', 14, "bold"), wraplength=390,justify="left").grid(row=1,column=0,sticky="w")
        artistNames = ", ".join(self._trackData[7])
        self._desc2 =tk.Label(self._frame, text = artistNames, bg='#191414', fg="white", font=('helvetica', 12),wraplength=390, justify="left").grid(row=2,column=0, sticky="w")
        self._desc3 = tk.Label(self._frame, text = self._trackData[5], bg='#191414', fg="white", font=('helvetica', 12),wraplength=390, justify="left").grid(row=3,column=0, sticky="w")
        self._desc4 = tk.Label(self._frame, text = f"{minutes}:{seconds:02d}", bg='#191414', fg="white", font=('helvetica', 12),wraplength=390, justify="left").grid(row=4,column=0, sticky="w")
        #\nNewJeans 1st EP 'New Jeans'\n{minutes}:{seconds:02d}

        self._buttonFrame = tk.Frame(self._frame, bg='#191414')
        self._buttonFrame.grid(row=5,column=0, pady=10, sticky="ew")

        if self._trackData[2]:
            self._preview = tk.Button(self._buttonFrame, text="Preview",bg= 'white', fg="#191414", font=("helvetica", 14, "bold"), relief="flat",command=lambda: webbrowser.open(self._trackData[2]))
            self._preview.grid(row=0,column=0, sticky="w")

        self._save = tk.Button(self._buttonFrame, text="Save",bg= 'white', fg="#191414", font=("helvetica", 14, "bold"), relief="flat", command=self.saveToDb)
        self._save.grid(row=0,column=1, padx=5, sticky="e")

    def saveToDb(self):
        status = self._base4.updatePlaylist(trackData=self._trackData, playlist_id=self._playlistKey)
        if status==200:
            tkmb.showinfo(self, message="Track prepared for saving, exit search window to commit changes")
        elif status == 400:
            tkmb.showerror(self, message="50 Track Limit Reached. Only adding first 50 saved tracks.\nYou are still free to continue searching, or close the search window to commit your changes.")
        
class PlaylistResults(tk.Toplevel):
    def __init__(self, master):
        pass
    
class PlotWindow(tk.Toplevel):
    def __init__(self, master, authObj):
        pass

w = MainWindow()
w.mainloop()