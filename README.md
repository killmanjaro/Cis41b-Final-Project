Final Project for CIS41B Spring 2024 Authors: Alyssa Goldgeisser and Eric Dong
Description:

Our project has three files, main_gui.py, authRequest.py, and SpotiBase.py, and one database user.db. The authRequest and SpotiBase are the “backend” part of our project. authRequest is primarily focused on getting an authorization token from the Spotify API in order to access all of the functions of the API. The SpotiBase file is the file that makes all the requests to Spotify and stores the data received into appropriate containers such as a database or a dictionary. The database user.db stores the user's playlists and tracks in each playlist. The main_gui file is the front end of our program. It has four main functions, which are :

    Spotify Authorization 0.1 Login with a Spotify account and do the following!

    creating new playlists 1.1 Upon creation, you can search and add songs to said playlist

    getting recommendations based on songs in playlist 2.1 Pick a playlist in your library, get recommendations, browse, and add them to your playlist

    Visualize the "vibes" or the composition of genres in any of your playlist 3.1 "Vibes" = Danceability, Energy, and Valence/Mood on a bar chart with a complimentary color bar/vibe meter 3.2 View the distribution of genres across your playlist on a pie chart

    Search for songs (independent of creating a playlist) and add them to any playlist.

Bonus Feature: Viewing songs, you can listen to a 30-second preview snippet of a track No redirections, No webpages. It plays it in the app!
Modules used in each file:
authRequest.py : requests(Web Access), sockets(Network) SpotiBase.py : requests(Web Access), threading(Threads), database(Data Storage), numpy/matplotlib (Data Analysis and Visualization) main_gui.py : requests(Web Access), database(Data Storage), tkiner(GUI)
