Final Project for CIS41B Spring 2024
Authors: Alyssa Goldgeisser and Eric Dong

Description:
------------
Our project has three files, main_gui.py, authRequest.py, and SpotiBase.py, and one database user.db. 
The authRequest and SpotiBase are the “backend” part of our project. authRequest is primarily focused on 
getting an authorization token from the Spotify API in order to access all of the functions of the API. 
The SpotiBase file is the file that makes all the requests to Spotify and stores the data received into 
appropriate containers such as a database or a dictionary. The database user.db stores the user's playlists 
and tracks in each playlist. The main_gui file is the front end of our program. It has four main functions, 
which are :

0. Spotify Authorization
   0.1 Login with a Spotify account and do the following!
1. creating new playlists
   1.1 Upon creation, you can search and add songs to said playlist
   
2. getting recommendations based on songs in playlist
   2.1 Pick a playlist in your library, get recommendations, browse, and add them to your playlist
   
3. Visualize the "vibes" or the composition of genres in any of your playlist
   3.1 "Vibes" = Danceability, Energy, and Valence/Mood on a bar chart with a complimentary color bar/vibe meter
   3.2 View the distribution of genres across your playlist on a pie chart
   
4. Search for songs (independent of creating a playlist) and add them to any playlist.
   
Bonus Feature: 
Viewing songs, you can listen to a 30-second preview snippet of a track 
No redirections, No webpages. It plays it in the app!

   
Modules used in each file:
--------------------------
authRequest.py : requests(Web Access), sockets(Network)
SpotiBase.py : requests(Web Access), threading(Threads), database(Data Storage), numpy/matplotlib (Data Analysis and Visualization)
main_gui.py : requests(Web Access), database(Data Storage), tkiner(GUI)



FOR CLARE:
-----------------------------------------------------
Dummy Account Login Info

EMAIL: testingdummy41b@yahoo.com  Yahoo Password: spotifinal123$
Spotify Password: spotifinal123


How to use the app:
Open and run main_gui.py. 
It will open a web browser page for you to log into the Spotify account. 
Our server listening for an authorization response times out after a minute. 

BACKUP IN CASE YOU CAN'T MAKE REQUESTS:
If, for whatever reason, the login doesn't work and says that you're not authorized/registered, I've preregistered a new app at https://developer.spotify.com/dashboard on the given account
If not already, go to the dashboard at developer.spotify.com, select the app, at the top right are the settings, click that and the first thing you'll see is the client id. You can also unhide the client secret right below it.
In our module authRequest.py, our CLIENT_ID and CLIENT_SECRET are attributes of the SpOauth class. Replace our client id and secret with the one from the app in your dashboard.
I set the callback/redirect-URI in the app's registration to be the same as the one we're using (the one already in the authRequest.py). 
If the socket server isn't receiving anything after you log in, there's a slim chance you may also have to add a new redirect-uri. In the app's settings, you can go down, press edit, and change the redirect-URI. 
The most you'll have to change is the Port number. If you do have to change the redirect-uri in the dashboard, change the REDIRECT_URI class attribute, and the PORT in the authCodeCallback method. 

You should be set.
