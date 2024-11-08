#Author of authRequest.py: Eric Dong
import requests
import urllib.parse
import socket
import webbrowser
import base64
from datetime import datetime


class SpOauth():
    #Important constants in the authorization process: CLIENT_ID and CLIENT_SECRET are the application's identifier, given to us after registering the app on developer.spotify.com/dashboard
    #The REDIRECT_URI is where Spotify's authorization server will send the user once they have successfully authorized and been granted an authorization code or access token.
    #SCOPE are the fields of user data we are requesting to access on the user' behalf, such as their playlists and profile
    CLIENT_ID = "a1515b5290be41d1ae50cd900d17a191" 
    CLIENT_SECRET = "dc1b83ea9e964e0a91664938080d69d3" 
    SCOPE = 'user-read-private user-read-email user-top-read playlist-read-private playlist-modify-public playlist-modify-private'
    REDIRECT_URI = 'http://localhost:5690/callback' 
    AUTH_URL = 'https://accounts.spotify.com/authorize'
    TOKEN_URL = 'https://accounts.spotify.com/api/token'

    def __init__(self):
        #one of the requirements to get an access token was to encode our client_id and client_secret into a base64 byte string and put it in the header
        authString = SpOauth.CLIENT_ID + ":" + SpOauth.CLIENT_SECRET
        auth_bytes = authString.encode("utf-8")
        self._auth64 = str(base64.b64encode(auth_bytes), 'utf-8')

        self._authCode = None
        self._tokenData = None
        self._expiration = None
        self.authenticate()
        #on startup, the constructor will call authenticate which directs the user to Spotify' authorization webpage to login and authorize the app.
        

    def authenticate(self):
        PARAMS = {'client_id': SpOauth.CLIENT_ID,
                'response_type':'code',
                'scope': SpOauth.SCOPE, 
                'redirect_uri': SpOauth.REDIRECT_URI, 
                'show_dialog':False}

        #urllib.parse.urlencode connverts a mapping object such as our dictionary PARAMS, which may contain str or bytes objects, to a percent-encoded ASCII text string
        #according to the documentation, urllib.parse.parse_qs, is basically the opposite method. it would undo this encoding
        authUrl = f'{SpOauth.AUTH_URL}?{urllib.parse.urlencode(PARAMS)}'
        webbrowser.open(authUrl)
        self.authCodeCallback()
        #once the webpage is open, we start up our own socket server to listen for Spotify's authorization server's response/redirect
        

    
    def authCodeCallback(self):
        HOST = 'localhost'
        PORT = 5690
        
        #the server will listen for a response, if the user closes the authorization window without doing anything or sits for too long, the server times out and raises SystemExit
        #if the user declines the authorization then we get an error response that we'll catch and exit off of 
        with socket.socket() as server:
            server.bind((HOST, PORT))
            server.settimeout(60)
            server.listen()
            try:  
                (conn, addr) = server.accept()
                fromSpotify = conn.recv(1024).decode('utf-8')
                
                #once we receive a response from the authorization server, we send back a simple byte string containing an http status code and some html text to appear on the webbrowser to tell the user they can close that window
                status = 'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\nAuthorization complete. You can close this window.'
                conn.sendall(status.encode('utf-8'))

                response = fromSpotify.split('\n')[0]
            
                #auth page response, then we parse it for the code= portion: using urllib.parse.urlparse which parses a URL into six components, returning a 6-item named tuple.
                # GET /callback?code=AQCPfNNDozPGo6fxhuiK1OTNs1Vt58bdbdxwK02b7XyG8uTSN8ar1cMMtF7eWYNUX_y65SVqT70dBiNltYEq79e5P-2UsvhNsAFQRci-tHSdIJ9bZRMzJrtmzWiwM1ySM6OEQCb6pq_Ez2mvCzUKXEWB8gHLrVU0pTsoRiwqZARobPaLp__Q0Uxdfygemx981fvVGZm5iunah4UeVZZB3cGlK32711M5luRZsqHl9SSM397JTJ4Dw0n84GjI93qpiqTqnyCQCiQMBr78HwWdLYSwttur19qk80SpDdel-AaAnWcfwkN03TB5XRN4CqmIhpgfHygHbbgwPgTCqQ HTTP/1.1
                #this code is our authorization code, which we have to parse and send back to Spotify in a post request so we can get an access token to make requests
                codeQuery = urllib.parse.urlparse(response).query
                
                try:
                    #parse_qs turns the code= part into a dictionary with code being the key and the authorization code our value, I assume that they send a valid code and not an error, 
                    #if it is an error we catch the keyerror exception and exit
                    self._authCode = urllib.parse.parse_qs(codeQuery)['code'][0].split(" ")[0]

                    #we have to send a post request containing the code we received and parsed, and the callback endpoint/redirect uri. On the documentation they wouldn't actually redirect anywhere, its just there just in case apparently
                    DATA = {"grant_type":"authorization_code",
                            "code":self._authCode,
                            "redirect_uri":SpOauth.REDIRECT_URI}
                    
                    #then the header containing the base64 encoded client_id:client_secret 
                    HEADERS = {"Authorization": f"Basic {self._auth64}",
                            "Content-Type":"application/x-www-form-urlencoded"}
                    
                    #send the post request, and receive a json containing our access token for API access, the time (ms) the token expires in (1 hour)
                    #and a refresh token that we could exchange for a new access token if it ever expires
                    tokenReq = requests.post(SpOauth.TOKEN_URL, headers=HEADERS, data=DATA)
                    self._tokenData = tokenReq.json()
                    print("\n", self._tokenData, "\n")
                    self._expiration = datetime.now().timestamp() + self._tokenData['expires_in']
                    #mark the time that the token was received, add the time it expires in so we can refresh it accordingly

                except KeyError:
                    raise SystemExit('Authorization Denied')
                    #raise an exception, maybe let gui handle it
            except socket.timeout:
                server.close()
                raise SystemExit("No response: Authorization Denied")
                
            
            '''
            {'access_token': 'BQDPSmqOeD4JICrGgXTsfMpHxFVaqy6GwgcPXRvhttGD6ENQrWA_ZZK77aA_09LCcYjmdjqX4FDE4plkhy29uRCUQ4XmRsvGj4KtHy8ULMcDbGb1sqn9q89kHVKuY7jzDQumJ8sCpgi9BiamQ5om8rwfHgXUlyl2O4Z1QEBa4BODCWPda44a7cyFU4kHp5icjjAO3IHIdQ5xQiFiviwLUyFTVjGi_tP8W07_IAHgq_kTRNXTjCQruJ75d9wJUVkpbaFO9zpYMF4k_1ycm8rQ', 
            'token_type': 'Bearer', 
            'expires_in': 3600, 
            'refresh_token': 'AQC_m_EuRpmHDYz2OK5r7y1tPY5woMQ2LG-uHTW2gDll9Vq3GUMLK68A1dzFh7KUKe2SskrcO5VKUoK7kqmRAWB2eQuXGbkUTHomj5AcTUdC-ZmVEca9hbieHXlf9ar1lv0', 
            'scope': 'playlist-read-private playlist-modify-private playlist-modify-public user-read-email user-read-private user-top-read'}
            '''
    
    def refreshToken(self):
        #check if we even have a refresh token, else go back through the authorization process, 
        #write the body/data containing our refresh token and grant type, the header has the content type and our base64 string from before
        #send another post request with that data to receive a new json containing a new token, refesh token (very similar to the first json)
        if "refresh_token" in self._tokenData:
            BODY = {"grant_type": "refresh_token",
                    "refresh_token":self._tokenData['refresh_token']}
            HEADER = {"Content-Type":"application/x-www-form-urlencoded",
                      "Authorization":"Basic " + self._auth64}
            tokenResponse = requests.post(SpOauth.TOKEN_URL, data=BODY, headers=HEADER)
            self._tokenData = tokenResponse.json()
            self._expiration = datetime.now().timestamp() + self._tokenData['expires_in']
        else:
            self.authenticate()
    
    @property
    def authHeader(self):
        '''Returns header containing the access token, vital for making API requests, we have to put it in the headers field with every API request'''
        #if there is no token data, reauthorize
        if not self._tokenData:
            self.authenticate()
        
        #if the token is expired, refresh the token
        if datetime.now().timestamp() > self._expiration:
            print("Token expired, refreshing")
            self.refreshToken()
        #once everything checks out, then you get your header
        return {"Authorization":'Bearer ' + self._tokenData['access_token']}


    
    
