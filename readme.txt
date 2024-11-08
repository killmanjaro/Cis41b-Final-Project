Final Project for CIS41B Spring 2024
Authors: Alyssa Goldgeisser and Eric Dong

Description:
------------
Our project has three files, main_gui.py, authRequest.py, and SpotiBase.py and one database user.db. 
The authRequest and SpotiBase are the “backend” part of our project. authRequest is primarily focused on 
Spotify's authorization code flow (Oauth2.0). Since, we are working with user data via Spotify's API, we 
are required to set up an authorization code flow, which essentially has a user sign into their Spotify
account and gives our app permission to fetch/access data on their behalf. Additionally through this authorization process
we are granted an access token which we can use to actually make API requests. 
The SpotiBase file manages the flow and storage of data via API requests and Sqlite3 database. 
The database user.db stores the users playlists and tracks in each playlist. 
The main_gui file is the front end for our program. It has four main functions, 
which are :

1. creating new playlists 
2. getting recommendations based on your playlists 
3. visualizing your playlist either by genre or using metadata from spotify
4. searching for songs, and adding to the playlist. 

Modules used in each file:
--------------------------
authRequest.py : requests(Web Access), sockets(Network)
SpotiBase.py : requests(Web Access), threading(Threads), database/pickle(Data Storage), numpy/matplotlib (Data Analysis and Visualization)
main_gui.py : requests(Web Access), database(Data Storage), tkiner(GUI)

Added Imports:
--------------
pygame : Pygame is an open source module for making games, through we only use it to play audio.
We use it in only this simple function :
    def play_audio(self, audio_data):
        ''' plays audio '''
        pygame.mixer.init()
        pygame.mixer.music.load(audio_data)
        pygame.mixer.music.play()
And we use it to create a button that plays music from spotify right in our GUI!
To import, simply just type into your terminal: pip install pygame

Gotham-Medium font: We think that the app has much more of a spotify feel if you install this
font, but the GUI still functions if you do not, just defaults to Arial.

Flow:
-----
					Main Page:

				
1: Create a new Playlist (MainWindow)					2. Get reccomendations	(MainWin)			3.Visualize Playlists
|										|						  (Main Window)
|										|							|
v										v							v
Add name and description to new Playlist (NewPlaylist)			Listbox of your playlists (searchWIN)			Listbox of your playlists		
|										|						also choice between																	
|										|						plotting genre or features
v										v						(Search Win)	
Add songs? -> Yes							10 reccomended song Listbox (SearchWin)				|
|		|								|							|
|		|								v							v					
v		v 4. Search for a Song (MainWindow)			Listbox Selection					   Pie Chart	
No	  Enter a song name							|
destroy	   (SearchSong Win)							|
window		|								v
		|							10 Songs Listbox
	10 Songs Listbox						  (Result Win)					
	    (ResultWin)								|						 
		|								|
		|								v								
		v							Select one of the Songs								
	 Listbox Selection							|
		|								|
		|								v
		v							 song info (songWin)
	    Song info								|
	    (SongWin)								|
		|								v
		|							Save to Playlist?
		V							 (Search Win)
	Save to Playlist?							|
	  (Search Win)								|	
		|								v
		|							Playlist selected,
		v							song added
	Playlist selected,					
	song added.
	

		
