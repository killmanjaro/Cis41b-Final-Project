#Web Access Module, request and organize data into a database, works with authRequest(provides the access token)
#Authored by Eric Dong, with some additions made by Alyssa
import sqlite3
import json
import requests
import pickle
import urllib.parse
from authRequest import SpOauth
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from collections import Counter
import threading

#this class handles a lot of the functionality, requests user data (playlists, tracks, user's id) and stores it in an sqlite3 database, fetches track recommendations and organizes/prepares them, fetches tracks via search by track name, gets user data from the database (with on-demand data fetching) and plots them 
class SpotiBase:
    DATABASE = "user.db"
    def __init__ (self, initAuth):
        '''
        The intention in mind is that SpotiBase works in conjunction with authRequest.SpOauth, 
        on start-up up we will request the user's profile and store their ID so down the line, we can create playlists (these would also be updated onto the Spotify app)
        we'll also request the user's playlists and load them into the database
        then for each playlist we make requests to get data for all the tracks in each playlist (done serially, so it's really slow, especially with really large playlists), if we had the time it would've been optimized but I guess that's for another time :( but hey it works
        The database is structured with a many-to-many relationship. 
        There are a lot of playlists, each with a lot of tracks, so we can't simply have a track ID column. to solve this, I used a junction/mapping table to relate the Playlists and Tracks table. 
        '''
        
        self._conn = sqlite3.connect(SpotiBase.DATABASE)
        self._cur = self._conn.cursor()
        self._lock = threading.Lock()
        
        self._userID = self.getUserID(initAuth)

        self._cur.execute("DROP TABLE IF EXISTS Playlists")
        self._cur.execute('''CREATE TABLE Playlists(
                    id INTEGER NOT NULL PRIMARY KEY UNIQUE,
                    spotifID TEXT UNIQUE ON CONFLICT IGNORE,
                    name TEXT,
                    tracksHref TEXT,
                    totalTracks INTEGER)''')
        
        self._cur.execute("DROP TABLE IF EXISTS Tracks")
        self._cur.execute('''CREATE TABLE Tracks(
                    id INTEGER NOT NULL PRIMARY KEY UNIQUE,
                    trackID TEXT UNIQUE ON CONFLICT IGNORE,
                    name TEXT,
                    preview TEXT,
                    uri TEXT,
                    duration INTEGER,
                    albumName TEXT,
                    images TEXT,
                    artists BLOB,
                    artistID BLOB)''')
        
        #in the Tracks table, i use a datatype we haven't used yet, BLOB (Binary large object)
        #because there can be multiple artists/artist ids per track I didn't want to have to create another mapping table because of time 
        #and since there typically aren't that many artists per track 1-3, I decided that pickling the small lists and inserting them in as BLOBs is quick and good enough, given the circumstances
        
        self._cur.execute("DROP TABLE IF EXISTS PlaylistTracks")
        self._cur.execute('''CREATE TABLE PlaylistTracks(
                    playlist_id INTEGER,
                    track_id INTEGER,
                    FOREIGN KEY (playlist_id) REFERENCES Playlists(id),
                    FOREIGN KEY (track_id) REFERENCES Tracks(id),
                    PRIMARY KEY (playlist_id, track_id) ON CONFLICT IGNORE)''')
        self._conn.commit()
        
        self.loadPlaylists(initAuth)
        self.paginateTracks(initAuth)
        
        self._savedTracks=[]
        #self._savedTracks will store track uris so they can be added to a playlist
    
    @property
    def connection(self):
        #get method for the sql connection
        return self._conn
    
    @property
    def cursor(self):
        #get method for the cursor, most likely won't need this because SpotiBase does everything for us
        return self._cur
    
    @property
    def saves(self):
        #this is important for the search feature, i guess so we can check if the user added 10 songs or not 
        #(we could honestly up the limit if we want, spotify lets up to 100)
        return self._savedTracks

    def getUserID(self, auth:dict):
        url = "https://api.spotify.com/v1/me"
        response = requests.get(url, headers=auth)
        if response.status_code == 200:
            data = response.json()
            user_id = data['id']
            return user_id

    def create_playlist(self, playlist_name:str, playlist_description:str, auth:dict):
        '''
        Alyssa actually wrote this method herself, I just came in to implement the database portion at the end (after creating a playlist its inserted into our database, if successful)
        
        auth is an argument you will see a lot, its where the header containing the access token will go, we need it to make requests
        '''
        ENDPOINT = f'https://api.spotify.com/v1/users/{self._userID}/playlists'
    
        DATA = {
                "name": playlist_name,
                "description": playlist_description,
                "public": True
                }

        response = requests.post(ENDPOINT, headers=auth, json=DATA)

        if response.status_code == 201:
            playlist = response.json()
            if "error" in playlist:
                return "fail"
            with open("newPlaylist.json", "w") as c:
                json.dump(playlist, c, indent=3)

            self._cur.execute('''INSERT INTO Playlists(spotifID, name, tracksHref, totalTracks) VALUES(?, ?, ?, ?)''', (playlist['id'], playlist['name'], playlist['tracks']['href'], playlist['tracks']['total']))
            self._cur.execute("SELECT id from Playlists WHERE spotifID = ?", (playlist['id'],))
            id = self._cur.fetchone()[0]
            self._conn.commit()
            print("Playlist Created")
            return (id, playlist['id'])
        else:
            return "fail"


    def search_songs(self, song_name:str, auth:dict):
        '''
        Spotify has a search endpoint that we're using for our search feature
        The API returns thiss large json which is an array of dictionaries and more nested dictionaries and a lot of fields
        we basically have to scrape/parse the Json and format it into more manageable data, at one point i formatted it into a list of tuples but Alyssa prefers the dictionary approach
        '''
        baseURL = "https://api.spotify.com/v1/search"
        query = f"q={song_name}&type=track&limit=10"
        endpoint = f"{baseURL}?{query}"
        response = requests.get(endpoint, headers=auth)
        
        if response.status_code == 200:
            data = response.json()
            song_d = {}
            for track in data['tracks']['items']:
                song_d[track['name']] = [
                      track['id'], #0
                      track['preview_url'], #1
                      track['uri'],  #2
                      track['duration_ms'],  #3
                      track['album']['name'], #4
                      track['album']['images'][1]['url'], #5
                      [artist['name'] for artist in track['artists']], #6
                      [artist['id'] for artist in track['artists']]] #7
            return song_d
        else:
            return "fail"
            #fail status, later i chose to use integers (like http status codes)


    def updatePlaylist(self, trackData:tuple, playlist_id:int):
        
        #this method is for adding a singular track to the database (part of the actual user interaction process, not for database initialization) and preparing it for being saved to a playlist officially on Spotify
        #in the proposal we said we'd limit the user to 10 songs per playlist but decided that 50 wouldn't be that bad (we'd been through the thick of it already at this point)
        if len(self._savedTracks) == 50:
            return 400

        #As mentioned in search_songs, I had intended for lists of tuples (a table/array) to be the format of choice and this is kind of like a remnant of that
        name, track_id, preview, uri, duration, album_name, images, artists, artistIDs = trackData


        #insert track metadata into the Tracks table
        self._cur.execute('''INSERT INTO Tracks (trackID, name, preview, uri, duration, albumName, images, artists, artistID)
                                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', (track_id, name, preview, uri, duration, album_name, images, pickle.dumps(artists), pickle.dumps(artistIDs)))
        #get the track ID (Spotify's track id/code, not like a database primary key)
        self._cur.execute("SELECT id FROM Tracks WHERE trackID = ?", (track_id,))
        trackID_DB = self._cur.fetchone()[0]

        #we had alo been passed a playlist's id (database primary key), we then use that to create the relationship between track and playlist in the PlaylistTrack mapping table
        self._cur.execute("INSERT INTO PlaylistTracks (playlist_id, track_id) VALUES (?, ?)", (playlist_id, trackID_DB))
        self._conn.commit()

        #we append the uri to a list, as part of preparing each track for saving on Spotify
        #we pass these uris later to another method to use as a field in a post request
        self._savedTracks.append(uri)
        print(f"{uri} added")
        return 201

    def addItems(self, auth, playlist_id):
        #this method is for officially adding tracks to a playlist on Spotify

        #check if the user hasn't prepared any tracks to save (pressing the save button on a track in GUI)
        #we return a 401 status
        if len(self._savedTracks) == 0:
            return 401

        #we pass the id of the playlist they will add the tracks to (Spotify Id not primary key, i really have to rewrite these variables like what the heck)
        baseURL = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        body = {"uris":self._savedTracks[:50]}

        response = requests.post(baseURL, json=body, headers=auth)
        print(response.content)
        print(response.status_code)
        if response.status_code == 200:
            self._savedTracks.clear()
            return 200
        else:
            return 400
            
    def loadPlaylists(self, auth):
        '''
        initializes the playlists table, requests API for 10 of the user's playlists
        '''

        url = "https://api.spotify.com/v1/me/playlists?limit=10&offset=0"
        response = requests.get(url, headers=auth)

        #if we got a good response, then we prepare convert the contents into a dict and parse the data into the Playlists table
        if response.status_code == 200:
            data = response.json()

            for playlist in data['items']:
                self._cur.execute('''INSERT INTO Playlists(spotifID, name, tracksHref, totalTracks) 
                                    VALUES(?, ?, ?, ?)''', (playlist['id'], playlist['name'], playlist['tracks']['href'], playlist['tracks']['total']))
                
            self._conn.commit()
        else:
            raise SystemExit("Something went wrong in loadPlaylists")
        #this could've been done better but since it's part of the initialization process we have the GUI/frontend also catch and handle this pretty early on

    def paginateTracks(self, auth):
        '''
        Since playlists can have a lot of tracks, and each track can have a lot of information, tracks in a playlist aren't returned all at once
        instead the requests are paginated (split into multiple pages)
        in one request for a playlist's tracks up to 100 are returned, if there are more songs then there is a next page endpoint for the next 100 songs

        the requests portion could most definitely implement threading but I don't think we have the time (we couldn't dwell on this portion and had to keep pushing for overall functionality)

        we query the database for each playlist's primary key, and the tracks href (endpoint for the playlist's tracks) in a list of tuple pairs
        for each playlist in the table, we make a request for tracks starting at the tracks href, then for each track object in the response we parse and insert the track data into the database (with relationship to the playlist)
        we do this for each playlist WHILE the "next" endpoint isn't none (ie, no more tracks in the playlist)
        there's a lot of nested looping and it lowkey annoys me looking at it... but it works -_-
        '''
        self._cur.execute("SELECT id, tracksHref FROM Playlists")
        playlists = self._cur.fetchall()
        fields = {'fields':"next,items(track(album(name,images(url)),artists(name,id),duration_ms,id,name,preview_url,uri))"}
        iterOut = 0
        iterIn = 0

        for playlist_id, link in playlists:
            endpoint= f"{link}?{urllib.parse.urlencode(fields)}"
            iterOut +=1
            while endpoint:
                response = requests.get(endpoint, headers=auth)

                if response.status_code != 200:
                    raise SystemExit("can't load tracks")
                
                data = response.json()
                if not data['items']:
                    break
                iterIn += 1              
                
                try:
                    #print("data items: ",data['items'], len(data['items']))
                    for track in data['items']:
                        if track['track']:
                            track_id = track['track']['id']
                            name = track['track']['name']
                            preview = track['track']['preview_url']
                            uri = track['track']['uri']
                            duration = track['track']['duration_ms']
                            album_name = track['track']['album']['name']
                            images = track['track']['album']['images'][1]['url']
                            artists = pickle.dumps([artist['name'] for artist in track['track']['artists']])
                            artistIDs = pickle.dumps([artist['id'] for artist in track['track']['artists']])
                                
                            self._cur.execute('''INSERT INTO Tracks (trackID, name, preview, uri, duration, albumName, images, artists, artistID)
                                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', (track_id, name, preview, uri, duration, album_name, images, artists, artistIDs))
                            self._cur.execute("SELECT id FROM Tracks WHERE trackID = ?", (track_id,))
                            trackID_DB = self._cur.fetchone()[0]

                            self._cur.execute("INSERT INTO PlaylistTracks (playlist_id, track_id) VALUES (?, ?)", (playlist_id, trackID_DB))

                            endpoint = data.get('next')
                        else:
                            continue
                except TypeError:
                    print("IterOUt", iterOut) #this for debugging, had to check which iteration the method was in to determine which playlist and at which track something broke, I believe we've got the Nonetype/faulty data thing covered
                    print("iterIn", iterIn)

        self._conn.commit()

    def recommend(self, auth, playlist_id):
        '''
        this method makes a request for track recommendations (10 of them) using existing data from the database
        to get a recommendation we need to provide a seed of either  5 track ids (Spotify id, not primary key), genres, or artist ids; no combinations of the three

        to get the 5 track ids, we select the track id based on its playlist's primary key (we're getting a recommendation based on what's in a user's playlist)
        I limit the selection to 5 IDs and have it randomized. 
        '''
        baseURL = "https://api.spotify.com/v1/recommendations"
        queryTrackIDs = '''SELECT Tracks.trackID
                        FROM Tracks
                        JOIN PlaylistTracks ON Tracks.id = PlaylistTracks.track_id
                        JOIN Playlists ON Playlists.id = PlaylistTracks.playlist_id
                        WHERE Playlists.id = ?
                        ORDER BY RANDOM()
                        LIMIT 5'''
        self._cur.execute(queryTrackIDs, (playlist_id,))
        track_seed = ",".join([row[0] for row in self._cur.fetchall()])

        
        if not track_seed:
            print("no track seeds, user either has no tracks or playlists saved")

        PARAMS = {"limit":10, "seed_tracks":track_seed}
        
        response = requests.get(baseURL, params=PARAMS, headers=auth)
        print("recommendation", response.status_code)
        print("recommendation content", response.content)
        if response.status_code == 200:
            data = response.json()
            data_d = {}

        #we make the request for 10 recommendations and format into into a dictionary, just like with the search
            for track in data['tracks']:
                data_d[track['name']] = [
                      track['id'], #0
                      track['preview_url'], #1
                      track['uri'],  #2
                      track['duration_ms'],  #3
                      track['album']['name'], #4
                      track['album']['images'][1]['url'], #5
                      [artist['name'] for artist in track['artists']], #6
                      [artist['id'] for artist in track['artists']]] #7

            
            return playlist_id, data_d
        else:
            return response.status_code
        
        
        #print(self._cur.fetchall()) #list of tuples containing the track ids and pickled list of artist ids
    
    def is_playlist_empty(self, play_id):
        ''' checks if the playlist is empty'''
        self._cur.execute('''SELECT Tracks.trackID
                          FROM Tracks 
                          JOIN PlaylistTracks ON Tracks.id = PlaylistTracks.track_id
                          WHERE PlaylistTracks.playlist_id = ?''', (play_id,))
        tracks = [row[0] for row in self._cur.fetchall()]
        if len(tracks) == 0:
            return 'empty'
        else:
            return 'not empty'
        


    def compileGenres(self, id:int, auth:dict):
        '''
        this is one of 6 methods in our data visualization method
        first it queries the database for all artistIDs in a playlist, the artistIDs are pickled lists that are unpickled and dumped into a list via comprehension

        here i figured that I could do some really simple threading to request each artist's profile information, (we're only after the list of genres tied to each artist)
        instead of making possibly hundreds of requests, I make batch requests, one request for every 50 artists, i could go up to 100 but I found that I got a lot of bad responses despite fewer requests
        each batch request is done on a thread (in fetchGenres) so it's being done semi concurrently, each thread parses the responses for the genres and compiles them into a list
        .extend() isn't thread-safe list operation so I chose to use a threading lock, in theory all the threads compile the genres in one massive list (most definitely terrible memory-wise)
        but we quickly throw it into a collections Counter to count each genre occurrence so that we can plot a pie chart representing a very general distribution/composition of genres in a playlist
        '''
        audioFeaturesTable = []
        threads = []
        self._cur.execute('''SELECT Tracks.artistID
                          FROM Tracks 
                          JOIN PlaylistTracks ON Tracks.id = PlaylistTracks.track_id
                          WHERE PlaylistTracks.playlist_id = ?''', (id,))
        
        artistIDS = [artist for row in self._cur.fetchall() for artist in pickle.loads(row[0])]
        
        for i in range(0, len(artistIDS), 50):
            artistBatch = artistIDS[i:i+50]
            t = threading.Thread(target=self.fetchGenres, args=(auth, artistBatch, audioFeaturesTable))
            t.start()
            threads.append(t)

        for thread in threads:
            thread.join()
       
        counter = Counter(audioFeaturesTable)
        
        return counter
    
    def fetchGenres(self, auth:dict, ids:list, container:dict):
        baseURL = "https://api.spotify.com/v1/artists"
        response = requests.get(baseURL, headers=auth, params={"ids": ",".join(ids)})
        print(response.status_code)
        if response.status_code == 200:
            data = response.json()
            genres=[]
            for artist in data['artists']:
                if artist:
                    genres.extend(artist['genres'])
            with self._lock:
                container.extend(genres)
        elif response.status_code == 429:
            print("too many requests")

    def plotPie(self, playlist_id, auth):
        #we call compileGenres to get the counter dict of genres, that we then use for plotting on a pie chart (a Matplotlib feature we haven't learned in class)
        #on top of that I'm using Matplotlib's subplot method. It allows us to have multiple charts/graphs on a single figure, but it also has a more object-oriented approach to plotting
        counter = self.compileGenres(playlist_id, auth)
        
        genres=[]
        values=[]
        other_count = 0
        totalCount = sum(counter.values())
        threshold = max(1, totalCount // 75)
        
        for genre, count in counter.items():
            if count >= threshold:
                genres.append(genre.title())
                values.append(count)
            else:
                other_count += count

        genres.append('other')
        values.append(other_count)

        fig, ax = plt.subplots(figsize=(10,10), layout='constrained') #subplot is nice because of the "constrained" layout which helps with reducing label overlap
        ax.pie(values, labels=genres, radius=1, colors=['#1f77b4', '#aec7e8', '#2ca02c', '#98df8a', '#9467bd', '#c5b0d5',  '#ff7f0e', '#ffbb78', '#d62728', '#ff9896', '#17becf', '#9edae5', '#7f7f7f', '#c7c7c7'], textprops={'color': 'white', 'fontsize': 50, 'fontweight': 'bold', "font":"arial"}, startangle=75)
        fig.patch.set_facecolor("#191414")

        return fig 
        #since we're using subplots, we don't call plt.figure() like normal, instead we have to return the figure object which we then pass to the tkinter canvas, it's very different compared to what we've done but I kind of prefer this object-oriented approach

    
    def compileFeatures(self, id, auth):
        '''
        just like compileGenres, we need to fetch a lot of data on demand, so we implement threading and batch requests just like before
        instead of genres this time, we're requesting the audio features of tracks in a playlist to get the overall features/attributes of a playlist
        In this case we want to display the "danceability," "energy," and "valence" of a playlist. These features collectively represent the "vibes" of a playlist
        Danceability - having a rhythm and style that people can dance to
        Energy - a perceptual measure of intensity and activity
        valence kind of refers to the mood, the higher the happier, the lower the sadder a song is

        fetchTrackIDs fetches the audio feature of the ideas and formats the values of the three features we want into a table (lists of tuples containing the features)
        then I used numpy to quickly condense the values into a 1D array (averaged values of each audio feature) and return it
        '''
        featuresTable = []
        threads = []
        self._cur.execute('''SELECT Tracks.trackID
                          FROM Tracks 
                          JOIN PlaylistTracks ON Tracks.id = PlaylistTracks.track_id
                          WHERE PlaylistTracks.playlist_id = ?''', (id,))
        trackIDS = [row[0] for row in self._cur.fetchall()]
        
        for i in range(0, len(trackIDS), 100):
            trackBatch = trackIDS[i:i+100]
            t = threading.Thread(target=self.fetchTrackIDs, args = (auth, trackBatch, featuresTable))
            t.start()
            threads.append(t)
        for thread in threads:
            thread.join()

        return np.mean(featuresTable, axis=0)
        
    def fetchTrackIDs(self, auth, ids, container):
        baseURL = "https://api.spotify.com/v1/audio-features"
        response = requests.get(baseURL, headers=auth, params={"ids":",".join(ids)})
        if response.status_code == 200:
            data = response.json()
            featuresBatch = [(track['danceability'], track['energy'], track['valence']) for track in data['audio_features'] if data['audio_features'] and track]
            with self._lock:
                container.extend(featuresBatch)
        

    def plotFeatures(self, playlist_id, auth):
        #call compileFeatures (mean array of audio features), we graph the audio features on a bar chart
        featuresArray = self.compileFeatures(playlist_id, auth)
        featureNames = ("Danceability", "Energy", "Valence")
        
        #create subplots so we can have a bar graph and a color bar, taking advantage of having multiple plots on a figure
        fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(10,10), gridspec_kw={"width_ratios":[10,1]})
        
        ax1.bar(featureNames, featuresArray, color=['skyblue', 'lightgreen', 'lightcoral'])
        ax1.set_ylim(0,1)
        
        #configure the color map and the color bar, the color bar doesn't necessarily represent real data (it's kind of there for the aesthetic), but it kind of helps you gauge the "vibes" of your playlist
        cmap = mpl.cm.cool
        norm = mpl.colors.Normalize(vmin=0, vmax=1)
        cbar = fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap), cax=ax2, orientation='vertical', label='Vibes')

        #configure tick, labels, and frame colors 
        ax1.yaxis.label.set_color('white')
        ax1.xaxis.label.set_color('white')
        ax1.spines['left'].set_color("white")
        ax1.spines['bottom'].set_color("white")
        ax1.tick_params(axis='x', colors='white')
        ax1.tick_params(axis='y', colors='white')

        # Set color bar label color and tick colors
        cbar.ax.yaxis.label.set_color('white')
        cbar.ax.tick_params(axis='y', colors='white')

        #change background color of figure and axis
        fig.patch.set_facecolor("#191414")
        ax1.set_facecolor("#191414")
        
        #change the background color of the color bar
        cbar.ax.set_facecolor("#191414")

        #returns the figure so we can plot it on tkinter
        return fig


    def fetchPlaylists(self):
        #this method just fetches each playlist and their respective data so that we can display them in a listbox in a results window
        self._cur.execute('''SELECT id, name, totalTracks FROM Playlists''')
        return self._cur.fetchall()
    
if __name__ == "__main__":
    a = SpOauth()
    sp = SpotiBase(a.authHeader)
