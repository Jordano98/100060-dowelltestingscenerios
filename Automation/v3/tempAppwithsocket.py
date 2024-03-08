import json
import os
from datetime import datetime, timedelta

from flask import (
    Flask,
    make_response, jsonify, redirect, 
    render_template,
    request, session
)
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from google.oauth2 import credentials
from google_auth_oauthlib.flow import Flow
import googleapiclient.discovery

# The above code is importing the `VideoStreamer` class from the `LiveStreamclass` module.
from LiveStreamclass import VideoStreamer


# `app = Flask(__name__)` creates a Flask application object. This object represents the Flask web
# application and is used to handle incoming requests and route them to the appropriate functions.
app = Flask(__name__)
CORS(app, origins='*')
# `app.config['SESSION_COOKIE_NAME'] = 'google-login-session'` is setting the name of the session
# cookie to 'google-login-session'. This allows the Flask application to identify and manage the
# session cookie for the user's login session.
app.config['SESSION_COOKIE_NAME'] = 'google-login-session'

# `app.config.update(SECRET_KEY=os.urandom(24))` is setting the secret key for the Flask application.
# The secret key is used to encrypt session cookies and other sensitive data. `os.urandom(24)`
# generates a random string of 24 bytes, which is then used as the secret key.
app.config.update(SECRET_KEY=os.urandom(24))

# `CLIENT_SECRETS_FILE = "client_secrets.json"` is setting the value of the variable
# `CLIENT_SECRETS_FILE` to the string "client_secrets.json". This variable is used to specify the file
# path of the client secrets JSON file, which contains the client ID and client secret for the OAuth
# 2.0 authentication process with the Google API.
CLIENT_SECRETS_FILE = "client_secrets.json"

# The above code is defining a list called `SCOPES` which contains three strings. These strings
# represent the different scopes or permissions that are required to access certain features of the
# YouTube API. 
# The first scope `https://www.googleapis.com/auth/youtube.readonly` allows read-only
# access to the user's YouTube account. The second scope
# `https://www.googleapis.com/auth/youtube.upload` allows the user to upload videos to their YouTube
# account. The third scope `https://www.googleapis.com/auth/youtube.force-ssl` enforces the use of SSL
# (Secure Sockets Layer) for all API
SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
    "https://www.googleapis.com/auth/youtube.upload",
    'https://www.googleapis.com/auth/youtube.force-ssl'
]

# The above code is defining two variables, `API_SERVICE_NAME` and `API_VERSION`, with the values
# "youtube" and "v3" respectively. These variables are likely used to specify the API service name and
# version when making API requests.
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

# The above code is setting the value of the 'OAUTHLIB_INSECURE_TRANSPORT' environment variable to
# '1'. This is typically done to allow insecure transport for OAuth authentication, which is useful
# for testing or development purposes.
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# The above code is creating a SocketIO object and initializing it with the Flask app. This allows the
# Flask app to handle real-time communication with clients using websockets.
socketio = SocketIO(app)
# CORS(app, origins='*')

# The above code is creating a flow object using the `Flow.from_client_secrets_file()` method. This
# method takes in the path to a client secrets file, the desired scopes for the flow, and a redirect
# URI. The client secrets file contains information required to authenticate the application with the
# Google API. The scopes define the level of access the application will have to the user's Google
# account. The redirect URI is the URL where the user will be redirected after completing the
# authentication process.
flow = Flow.from_client_secrets_file(
    CLIENT_SECRETS_FILE,
    scopes=SCOPES,
    redirect_uri='http://localhost:8000/callback/'
)

@app.route('/')
def index():
    """
    The index function checks if the user is logged in and redirects them to the
    authorization URL if not, otherwise it renders the index.html template.
    Return: If the 'credentials' key is not present in the session, the code will
        redirect the user to the authorization URL. If the 'credentials' key is present
        in the session, the code will render the 'index.html' template.
    """
    if 'credentials' not in session:
        authorization_url, _ = flow.authorization_url(prompt='consent')
        return redirect(authorization_url)
    else:
        return render_template('index.html')


@app.route('/callback/')
def callback():
    """
    This function handles the callback URL and retrieves the access token
    from the authorization response.
    Return: a redirect to the root URL ("/").
    """
    flow.fetch_token(authorization_response=request.url)
    if not flow.credentials:
        return 'Failed to retrieve access token.'
    if session.get('user') != None:
        print(session['user'])
    session['credentials'] = credentials_to_dict(flow.credentials)
    return redirect('/')


@app.route('/channel')
def channel():
    """
    The function retrieves the information of the authenticated user's YouTube
    channel and returns the channel's snippet information.
    return: The channel information is being returned as a JSON object.
    """
    if 'credentials' not in session:
        return redirect('/')

    cred = credentials.Credentials.from_authorized_user_info(session['credentials'])
    youtube = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=cred)
    try:
        # Fetch YouTube channel information
        channels_response = youtube.channels().list(
            mine=True,
            part='snippet'
        ).execute()

        # Extract channel information
        channel_info = channels_response['items']
        channel_dict = {}
        if len(channel_info) > 0:
            channel_dict = {
                "id": channel_info[0]['id'],
                "title": channel_info[0]['snippet']['title'],
            }

        return make_response(jsonify(channel_dict), 200)
    except Exception as e:
        return make_response(jsonify({'Error': 'Failed to fetch user playlists'}), 500)


@app.route('/playlists')
def playlists():
    """
    The `playlists` function in this Python code fetches the user's playlists from the
    YouTube API.
    return: The code is returning the playlists and their titles in JSON format
            with a status code of 200 if the request is successful. If an
            error occurs, it returns an error message with a status code of 500.
    """
    if 'credentials' not in session:
        return redirect('/')

    cred = credentials.Credentials.from_authorized_user_info(session['credentials'])
    youtube = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=cred)

    try:
        # Fetch user's playlists
        playlists_response = youtube.playlists().list(
            part='snippet',
            mine=True
        ).execute()

        # Extract playlist information
        playlists = playlists_response['items']
        playlists_dict = []
        if len(playlists) > 0:
            playlists_dict = [
                {
                    "id": playlist['id'],
                    "title": playlist['snippet']['title']
                } 
                for playlist in playlists
            ]

        return make_response(jsonify(playlists_dict), 200)
    except Exception as e:
        return make_response(jsonify({'Error': 'Failed to fetch playlists'}), 500)




# send data in form not in json 
@app.route('/createPlaylist', methods=['POST'])
def create_playlist():
    """
    This function creates a new playlist on YouTube using the provided 
    title and description.
    return: The code is returning a JSON response containing the details
            of the newly created playlist.
    """
    if 'credentials' not in session:
        return redirect('/')

    cred = credentials.Credentials.from_authorized_user_info(session['credentials'])
    youtube = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=cred)

    try:
        # Extract playlist details from the request
        playlist_title = request.form.get('title')
        playlist_description = request.form.get('description')

        # Create a new playlist
        new_playlist = youtube.playlists().insert(
            part='snippet',
            body={
                'snippet': {
                    'title': playlist_title,
                    'description': playlist_description
                }
            }
        ).execute()

        return jsonify(new_playlist),200
    except Exception as e:
        return make_response({'Error': 'Failed to create playlist'}, 500)


#needed for startlive function
def insert_broadcast(youtube):
    """
        Creates a liveBroadcast resource and set its title, scheduled start time,
        scheduled end time, and privacy status.
    """
    # create broadcast time
    time_delt1 = timedelta(days=0, hours=0, minutes=1)  # ToDo use milliseconds
    time_now = datetime.utcnow()
    future_date1 = time_now + time_delt1
    future_date_iso = future_date1.isoformat()
    videoPrivacyStatus = "private"  # ToDo get this from request
    videoTitle = "Recored on" + " " + future_date_iso
    
    request = youtube.liveBroadcasts().insert(
        part="snippet,contentDetails,statistics,status",
        body={
            "status": {
                "privacyStatus": videoPrivacyStatus,
                "selfDeclaredMadeForKids": False
            },
            "snippet": {
                "scheduledStartTime": future_date_iso,
                "title": videoTitle
            },
            "contentDetails": {
                "enableAutoStart": True,
                "enableAutoStop": True
            }
        }
    )

    insert_broadcast_response = request.execute()

    snippet = insert_broadcast_response["snippet"]

    return insert_broadcast_response["id"]

#needed for startlive function
def insert_stream(youtube):
    """
        Creates a liveStream resource and set its title, format, and ingestion type.
        This resource describes the content that you are transmitting to YouTube.
    """
    request = youtube.liveStreams().insert(
        part="snippet,cdn,contentDetails,status",
        body={
            "cdn": {
                "frameRate": "variable",
                "ingestionType": "rtmp",
                "resolution": "variable"
            },
            "contentDetails": {
                "isReusable": False
            },
            "snippet": {
                "title": "A non reusable stream",
                "description": "A stream to be used once."
            }
        }
    )
    insert_stream_response = request.execute()
    print(insert_stream_response)

    snippet = insert_stream_response["snippet"]
    cdn = insert_stream_response["cdn"]
    ingestionInfo = cdn["ingestionInfo"]

    print("Stream '%s' with title '%s' was inserted." % (
        insert_stream_response["id"], snippet["title"]))

    newStreamId = insert_stream_response["id"]
    newStreamName = ingestionInfo["streamName"]
    newStreamIngestionAddress = ingestionInfo["rtmpsIngestionAddress"]
    print("New stream id: ", newStreamId)
    print("New stream name: ", newStreamName)
    print("New stream ingestion address: ", newStreamIngestionAddress)
    newRtmpUrl = newStreamIngestionAddress + "/" + newStreamName
    print("New stream RTMP url: ", newRtmpUrl)

    stream_dict = {"newStreamId": newStreamId,
                   "newStreamName": newStreamName,
                   "newStreamIngestionAddress": newStreamIngestionAddress,
                   "newRtmpUrl": newRtmpUrl
                   }
    return stream_dict


#needed for startlive function
def bind_broadcast(youtube, broadcast_id, stream_id):
    """
        Binds the broadcast to the video stream. By doing so, you link the video that
        you will transmit to YouTube to the broadcast that the video is for.
    """
    request = youtube.liveBroadcasts().bind(
        part="id,contentDetails",
        id=broadcast_id,
        streamId=stream_id
    )
    bind_broadcast_response = request.execute()


@app.route('/startLiveStream', methods=['POST'])
def create_broadcast():
    """
        Creates a broadcast, it is view based.
    """
    if 'credentials' not in session:
        return redirect('/')

    cred = credentials.Credentials.from_authorized_user_info(session['credentials'])
    youtube = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=cred)

    if youtube is None:
        return "some error happend, try after some time",500
    
    try:
        # Create broadcast
        new_broadcast_id = insert_broadcast(youtube)
        # Create stream
        stream_dict = insert_stream(youtube)

        # Bind livestream and broadcast
        stream_dict['new_broadcast_id'] = new_broadcast_id
        stream_id = stream_dict['newStreamId']
        bind_broadcast(youtube, new_broadcast_id, stream_id)

        # Serializing json
        json_stream_dict = json.dumps(stream_dict)
        print(json_stream_dict)

        response=json_stream_dict
        return response
        
    except Exception as e:
        return 'An error occurred: Please try again after some time',500


@socketio.on('connect')
def handle_connect():
    """
    The function `handle_connect` is triggered when a client connects to
    the socket, and if the session does not already have a 'video_streamer'
    key, it creates a new instance of the `VideoStreamer` class
    and assigns it to the session.
    """
    print('Client connected')
    if 'video_streamer' not in session:
        session['video_streamer'] = VideoStreamer()


@socketio.on('disconnect')
def handle_disconnect():
    """
    The function "handle_disconnect" is triggered when a client disconnects
    from the socket.
    """
    print('Client disconnected')


@socketio.on('start_stream')
def handle_start_stream(stream_key):
    """
    The function `handle_start_stream` starts a video stream and sends 
    the stream ID back to the client.
    param 
        stream_key: The stream_key is a unique identifier for the stream.
            It is used to start the streaming process and associate the stream
            with a specific key
    """
    emit('stream_started')
    video_streamer = session['video_streamer']
    stream_id = video_streamer.start_streaming(stream_key)
    socketio.emit('stream_id', {'stream_id': stream_id})


@socketio.on('stop_stream')
def handle_stop_stream(data):
    """
    The function `handle_stop_stream` stops a video stream identified by
    `stream_id` using the `video_streamer` object stored in the session.
    param 
        data: The `data` parameter is a dictionary that contains the
            information sent from the client-side. It is expected to
            have a key-value pair where the key is `'stream_id'` and
            the value is the ID of the stream that needs to be stopped
    """
    stream_id = data.get('stream_id', None)
    if stream_id:
        video_streamer = session['video_streamer']
        video_streamer.stop_streaming(stream_id)


@socketio.on('stream_data')
def handle_stream_data(data):
    """
    The function handles streaming data by writing the
    stream to the corresponding ffmpeg process.
    param 
        data: 
            The `data` parameter is a dictionary that contains the information
            about the stream data. It may have the following keys:
    """
    stream_id = data.get('stream_id', None)
    video_streamer = session['video_streamer']
    ffmpeg_process = video_streamer.streams.get(stream_id)
    if ffmpeg_process and data:
        stream = data.get('stream', None)
        ffmpeg_process.stdin.write(stream)
        ffmpeg_process.stdin.flush()



def credentials_to_dict(credentials):
    """
    The function `credentials_to_dict` converts a `credentials` object into a 
    dictionary.
    param: 
        credentials: 
            The "credentials" parameter is an object that contains various
            properties related to authentication and authorization.
    Return: a dictionary with the following keys and values:
    """
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }


if __name__ == "__main__":
    # Run the app using the Flask development server and socketio server
    socketio.run(app, port=8000, debug=True)
