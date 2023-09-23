"""
Second views file for the YouTube app.
"""
import json
import logging
import requests
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import YoutubeUserCredential, ChannelsRecord
from rest_framework.renderers import JSONRenderer
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


# def create_user_youtube_object(request):
#     """
#     Create a YouTube object using the v3 version of the API and
#     the authenticated user's credentials.
#     """
#     print('Creating youtube object...')
#     try:
#         # Retrieve the YoutubeUserCredential object associated with the authenticated user
#         print('user=request.user 27', request.user)
#         youtube_user = YoutubeUserCredential.objects.get(user=request.user)
#         print('youtube_user 28:', youtube_user)
#
#         # Retrieve the user's credentials associated with the YoutubeUserCredential object
#         credentials_data = youtube_user.credential
#         print('credentials_data 33:', credentials_data)
#         try:
#             # Convert the JSON string to a dictionary
#             credentials_data_dict = json.loads(credentials_data)
#             print('credentials_data_dict 37:', credentials_data_dict)
#             # Create credentials from the dictionary
#             credentials = Credentials.from_authorized_user_info(info=credentials_data_dict)
#             print('credentials 40:', credentials)
#             # print('Credentials: xxxxxxxxxxx')
#         except Exception as e:
#             credentials = Credentials.from_authorized_user_info(info=credentials_data)
#             # print('Credentials: xxxxxxxxxxx')
#         try:
#             # print(f'Checking if access token has expired...{credentials.expired}')
#             # Check if the access token has expired
#             if credentials.expired:
#                 print('Access token has expired!')
#
#                 print('Refreshing access token...')
#                 import google.auth.transport.requests
#
#                 # Create a request object using the credentials
#                 google_request = google.auth.transport.requests.Request()
#
#                 # Refresh the access token using the refresh token
#                 credentials.refresh(google_request)
#
#                 # Update the stored credential data with the refreshed token
#                 youtube_user.credential = credentials.to_json()
#                 youtube_user.save()
#                 print('Access token refreshed!')
#         except Exception as e:
#             # Handle any error that occurred while refreshing the access token
#             print(f'An error occurred: {e}')
#             return None
#
#         # Create a YouTube object using the v3 version of the API and the retrieved credentials
#         youtube = build('youtube', 'v3', credentials=credentials, cache_discovery=False)
#
#         return youtube, credentials
#     except YoutubeUserCredential.DoesNotExist:
#         # If the user doesn't have a YoutubeUserCredential object,
#         # return an error response with 401 Unauthorized status code
#         return None
def create_user_youtube_object(request):
    """
    Create a YouTube object using the v3 version of the API and
    the authenticated user's credentials.
    """
    print('Creating youtube object...')
    try:
        # Retrieve the YoutubeUserCredential object associated with the authenticated user
        print('user=request.user 27', request.user)
        youtube_user = YoutubeUserCredential.objects.get(user=request.user)
        print('youtube_user 28:', youtube_user)

        # Retrieve the user's credentials associated with the YoutubeUserCredential object
        credentials_data = youtube_user.credential
        print('credentials_data 33:', credentials_data)
        try:
            # Convert the JSON string to a dictionary
            credentials_data_dict = json.loads(credentials_data)
            print('credentials_data_dict 37:', credentials_data_dict)
            # Create credentials from the dictionary
            credentials = Credentials.from_authorized_user_info(info=credentials_data_dict)
            print('credentials 40:', credentials)
        except Exception as e:
            credentials = Credentials.from_authorized_user_info(info=credentials_data)

        try:
            # Check if the access token has expired
            if credentials.expired:
                print('Access token has expired!')

                print('Refreshing access token...')
                import google.auth.transport.requests

                # Create a request object using the credentials
                google_request = google.auth.transport.requests.Request()

                # Refresh the access token using the refresh token
                credentials.refresh(google_request)

                # Update the stored credential data with the refreshed token
                youtube_user.credential = credentials.to_json()
                youtube_user.save()
                print('Access token refreshed!')
        except Exception as e:
            # Handle any error that occurred while refreshing the access token
            print(f'An error occurred: {e}')
            return None

        # Create a YouTube object using the v3 version of the API and the retrieved credentials
        youtube = build('youtube', 'v3', credentials=credentials, cache_discovery=False)

        # return youtube, credentials
        return youtube
    except YoutubeUserCredential.DoesNotExist:
        # If the user doesn't have a YoutubeUserCredential object,
        # return an error response with 401 Unauthorized status code
        return None


class UserChannelsView(APIView):
    """
    This class is a DRF APIView that retrieves the authenticated user's YouTube channels.

    Methods:
      get(self, request, *args, **kwargs): Handles GET requests to this view and retrieves the
        channels associated with the currently
        authenticated user's YouTube account.
        Parameters:
        request: DRF Request object
        *args: tuple of positional arguments
        **kwargs: dictionary of keyword arguments

        Functionality:
            The get method retrieves the authenticated user's YouTube channels by first retrieving
            the YoutubeUserCredential object associated with the authenticated user. It then retrieves the user's
            credentials associated with the YoutubeUserCredential object and uses them to create a YouTube object using
            the v3 version of the API. It then retrieves the channels associated with the user's account and processes
            them into a list of dictionaries containing the channel id and title. It saves the first channel's details
            to a ChannelsRecord object and returns the channels in the response body with a 200 OK status code.
            If an exception is raised during any of the above steps, it returns an error response with a 404
            Not Found status code.

        Returns:
            If successful, returns a DRF Response object with a JSON array of dictionaries containing the channel id and
               title with a 200 OK status code.
            If the user doesn't have a YoutubeUserCredential object, returns a DRF Response object with an error message
                and a 401 Unauthorized status code.
            If unable to fetch the YouTube channels, returns a DRF Response object with an error message and
                a 404 Not Found status code.

    Attributes:
        permission_classes: a list containing the IsAuthenticated permission class to ensure only authenticated users
        can access this view.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Retrieve the authenticated user's YouTube channels.
        Returns a JSON array of dictionaries containing the channel id and title
        with a 200 OK status code. If the user doesn't have a YoutubeUserCredential
        object, returns a 401 Unauthorized status code. If unable to fetch the
        YouTube channels, returns a 404 Not Found status code.
        """
        try:
            youtube, credential = create_user_youtube_object(request)
            if youtube is None:
                print('youtube object creation failed!!')
                return Response({'Error': 'Account is not a Google account'}, status=status.HTTP_401_UNAUTHORIZED)

            print('Getting user youtube channel...')
            # Retrieve the channels associated with the user's account
            channels_response = youtube.channels().list(part='snippet', mine=True).execute()
            if 'items' not in channels_response:
                return Response({'Error': 'There is no youtube channel associated with this account!'},
                                status=status.HTTP_404_NOT_FOUND)

            # Process the channels into a list of dictionaries containing the channel id and title
            channels = [
                {
                    'channel_id': channel['id'],
                    'channel_title': channel['snippet']['title']
                }
                for channel in channels_response['items']
            ]

            try:
                # Check if the first channel already exists in the database
                first_channel = channels[0]

                channel_record, created = ChannelsRecord.objects.get_or_create(
                    channel_id=first_channel.get('channel_id'),
                    defaults={
                        'channel_title': first_channel.get('channel_title'),
                        'channel_credentials': credential
                    }
                )
                # If the channel already exists, update the credential
                if not created and channel_record.channel_credentials != credential:
                    channel_record.channel_credentials = credential
                    print("Channel credential updated!!!")
                    channel_record.save()

            except Exception as e:
                logger.error(
                    f'Error while saving user channel credential locally!: {e} occurred')

            return Response(channels, status=status.HTTP_200_OK)

        except Exception as e:
            error_message = str(e)
            return Response(
                {'Error': error_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def is_available_in_db(self, email) -> bool:
        """
        Checks if record already exist in the database'

        Return:
            True: If record exist in the database.
            False: If record is not in the database.
        """
        url = "http://100002.pythonanywhere.com/"

        payload = json.dumps({
            "cluster": "ux_live",
            "database": "ux_live",
            "collection": "credentials",
            "document": "credentials",
            "team_member_ID": "1200001",
            "function_ID": "ABCDE",
            "command": "find",
            "field": {
                'user_email': email
            },
            "update_field": {
                "order_nos": 21
            },
            "platform": "bangalore"
        })
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request(
            "POST", url, headers=headers, data=payload).json()

        if response.get('data') is None:
            return False

        print("xxx DB Response xx=> ", response)
        return True

    def fetch_user_credential_from_dowell_connection_db(self, email):
        """
        Inserts a new user youtube info record into the company's database

        Return:
            Json response from the database.
        """

        url = "http://100002.pythonanywhere.com/"

        payload = json.dumps({
            "cluster": "ux_live",
            "database": "ux_live",
            "collection": "credentials",
            "document": "credentials",
            "team_member_ID": "1200001",
            "function_ID": "ABCDE",
            "command": "find",
            "field": {
                'user_email': email,
            },
            "update_field": {
                "order_nos": 21
            },
            "platform": "bangalore"
        })
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request(
            "POST", url, headers=headers, data=payload).json()

        return response


class DeleteVideoView(APIView):
    """
    API view class for deleting a video on YouTube.

    Methods:
        post(request): Delete a video based on the provided video ID.

    Attributes:
        permission_classes: a list containing the IsAuthenticated permission class to ensure only authenticated users
        can access this view.
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request):
        """
        POST request to delete a YouTube video.

        Parameters:
        - request: The HTTP request object.

        Returns:
        - Response: HTTP response indicating the result of the video deletion.

        Raises:
        - Http404: If the YoutubeUserCredential object is not found for the authenticated user.
        - Exception: If an error occurs while deleting the video.

        Authorization:
        - The user must be authenticated.

        Example:
        ```
        POST /api/delete-video/ --- (Link yet to implemented)
        {
            "video_id": "your_video_id"
        }
        ```
        """
        try:
            youtube, credential = create_user_youtube_object(request)
            if youtube is None:
                print('youtube object creation failed!!')
                return Response({'Error': 'Account is not a Google account'}, status=status.HTTP_401_UNAUTHORIZED)

            video_id = request.data.get('video_id')

            # Delete the video using the video ID
            # If successful, this method returns an HTTP 204 response code (No Content).
            response = youtube.videos().delete(id=video_id).execute()
            return Response({'message': "Video deleted successfully", 'response': response},
                            status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'Error': str(e)})


class LoadVideoView(APIView):
    """
    API view class for loading all videos from YouTube.

    Methods:
        get(request): Load all videos

     Attributes:
        permission_classes: a list containing the IsAuthenticated permission class to ensure only authenticated users
        can access this view.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Load all videos from YouTube.

        Parameters:
            request (HttpRequest): The HTTP request object.

        Returns:
            Response: A response containing the loaded videos.

        Raises:
            YoutubeUserCredential.DoesNotExist: If the authenticated user does not have a YoutubeUserCredential object.
            Exception: If an error occurs during the loading process.
        """
        try:
            youtube, credential = create_user_youtube_object(request)
            if youtube is None:
                print('youtube object creation failed!!')
                return Response({'Error': 'Account is not a Google account'}, status=status.HTTP_401_UNAUTHORIZED)

            # Perform the YouTube Channels API call
            channels_response = youtube.channels().list(
                part='contentDetails',
                mine=True
            ).execute()

            channels = channels_response.get('items', [])
            if channels:
                channel_id = channels[0]['id']

                # Retrieve videos from each playlist
                playlists_response = youtube.playlists().list(
                    part='snippet,contentDetails',
                    channelId=channel_id,
                    maxResults=50
                ).execute()

                playlists = playlists_response.get('items', [])
                videos = []

                for playlist in playlists:
                    temp_playlist = {}
                    video = {}

                    temp_playlist['playlistTitle'] = playlist['snippet']['title']
                    temp_playlist['playlistId'] = playlist['id']

                    playlist_id = playlist['id']
                    playlist_items_response = youtube.playlistItems().list(
                        part='snippet',
                        playlistId=playlist_id,
                        maxResults=50
                    ).execute()

                    playlist_videos = playlist_items_response.get('items', [])

                    video = [
                        {
                            'videoId': videoItem['snippet']['resourceId']['videoId'],
                            'videoTitle': videoItem['snippet']['title'],
                            'videoThumbnail': videoItem['snippet']['thumbnails'].get('default', {}).get('url',
                                                                                                        'No Thumbnail Available'),
                            'videoDescription': videoItem['snippet']['description'],
                        } for videoItem in playlist_videos
                        if videoItem['snippet']['title'] != 'Deleted video'

                    ]

                    temp_playlist['videos'] = video  # playlist_videos

                    videos.append(temp_playlist)
            else:
                # Handle case when no channels are found
                videos = []

            return Response(videos, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'Error': str(e)}, status=status.HTTP_404_NOT_FOUND)


class YouTubeVideoAPIView(APIView):
    def get(self, request, broadcast_id):
        # Retrieve the video from the YouTube API
        video_data = self.get_video_data(request, broadcast_id)

        if video_data:
            return Response(video_data)
        else:
            return Response({'error': 'Video not found'}, status=404)

    def get_video_data(self, request, broadcast_id):
        # Set up the YouTube API client
        youtube, credential = create_user_youtube_object(request)
        if youtube is None:
            print('youtube object creation failed!!')
            return Response({'Error': 'Account is not a Google account'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            # Make a request to the YouTube API to retrieve video details
            response = youtube.videos().list(
                part='snippet',
                id=broadcast_id
            ).execute()

            if 'items' in response and len(response['items']) > 0:
                video_data = response['items'][0]['snippet']
                return video_data
            else:
                return None

        except Exception as e:
            # Handle any error that occurred during the API request
            print(f'An error occurred: {e}')
            return None


class FetchlibraryPlaylists(APIView):
    renderer_classes = [JSONRenderer]

    def get(self, request, *args, **kwargs):
        print('started Get Method from FetchlibraryPlaylists Function ')
        try:

            youtube = create_user_youtube_object(request)
            print('youtube 439:', youtube)
            if youtube is None:
                raise AttributeError('youtube object creation failed!!')

            # Fetch all playlists with pagination
            fetch_playlists = True
            playlists = []
            page_token = ""
            while fetch_playlists:
                request = youtube.playlists().list(
                    part='id, snippet,status,contentDetails',
                    maxResults=50,
                    mine=True,
                    pageToken=page_token
                )
                response = request.execute()
                print('response 455:', response)
                # Get next page token
                if "nextPageToken" in response.keys():
                    page_token = response['nextPageToken']
                else:
                    fetch_playlists = False

                # Add current page's playlists
                playlists.extend(response['items'])

                print('===== playlist count ===> ', len(playlists))

            # Check if the playlist is empty
            if len(playlists) == 0:
                print("The playlist is empty.")
                return Response({'Error': 'The playlist is empty.'}, status=status.HTTP_204_NO_CONTENT)
            else:
                playlist_details_list = []

                # Iterating through the json list
                for playlist in playlists:
                    playlist_id = playlist.get('id', '')
                    title = playlist.get('snippet', {}).get('title', '')
                    playlist_status = playlist.get('status', {}).get('privacyStatus', '')
                    total_videos = playlist.get('contentDetails', {}).get('itemCount', '')
                    thumbnail = playlist.get('snippet', {}).get('thumbnails', {}).get('medium', {}).get('url', '')

                    playlist_details_list.append({
                        'playlist_id': playlist_id,
                        'playlist_title': title,
                        'privacy_status': playlist_status,
                        'total_videos': total_videos,
                        'thumbnail_url': thumbnail
                    })

            # Current channel title (assuming the first playlist belongs to the same channel)
            channel_title = playlists[0]["snippet"]["channelTitle"]

            # Dictionary with all necessary data
            youtube_details = {
                'channel_title': channel_title,
                'playlists': playlist_details_list
            }

            return Response(youtube_details, status=status.HTTP_200_OK)

        except Exception as err:
            print("Error while fetching playlists: " + str(err))
            return Response({'Error': str(err)}, status=status.HTTP_400_BAD_REQUEST)


class SelectedPlaylistLoadVideo(APIView):
    """
    API view class for loading all videos from YouTube.

    Methods:
        get(request): Load all videos

     Attributes:
        permission_classes: a list containing the IsAuthenticated permission class to ensure only authenticated users
        can access this view.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, playlistId):
        print('request video against this video id : 490:', playlistId)
        """
        Load all videos from YouTube for the specified playlistId.

        Parameters:
            request (HttpRequest): The HTTP request object.
            playlistId (str): The ID of the playlist to load videos from.

        Returns:
            Response: A response containing the loaded videos.

        Raises:
            YoutubeUserCredential.DoesNotExist: If the authenticated user does not have a YoutubeUserCredential object.
            Exception: If an error occurs during the loading process.
        """
        try:
            youtube = create_user_youtube_object(request)
            if youtube is None:
                raise AttributeError('youtube object creation failed!!')

            # Perform the YouTube API call to retrieve videos for the specified playlistId
            playlist_items_response = youtube.playlistItems().list(
                part='snippet',
                playlistId=playlistId,
                maxResults=50
            ).execute()
            # print('selected playlist detail from views  515:', playlist_items_response)
            playlist_videos = playlist_items_response.get('items', [])

            videos = []

            for videoItem in playlist_videos:
                if 'snippet' not in videoItem or 'title' not in videoItem['snippet'] or 'resourceId' not in videoItem[
                    'snippet']:
                    continue

                # video_title = videoItem['snippet']['title']
                video_title = videoItem.get('snippet', {}).get('title', '')  # Error handling include
                # resource_id = videoItem['snippet']['resourceId']
                resource_id = videoItem.get('snippet', {}).get('resourceId', {})
                if 'videoId' not in resource_id:
                    continue

                videoId = resource_id.get('videoId', '')
                videoTitle = video_title
                videoThumbnail = videoItem.get('snippet', {}).get('thumbnails', {}).get('medium', {}).get('url',
                                                                                                          'No Thumbnail Available')
                videoDescription = videoItem.get('snippet', {}).get('description', '')

                try:
                    video_response = youtube.videos().list(
                        # part='snippet,contentDetails,status',
                        part='contentDetails, status',
                        id=videoId
                    ).execute()
                    # print('selected video_response detail from views  543:', video_response)

                    video_info = video_response.get('items', [])[0]
                    privacyStatus = video_info.get('status', {}).get('privacyStatus', 'Unknown')
                    duration = video_info.get('contentDetails', {}).get('duration', '00:00')
                except HttpError as e:
                    # Handle HttpError (e.g., video not found)
                    privacyStatus = 'Unknown'
                    duration = '00:00'

                video_info = {
                    'videoId': videoId,
                    'videoTitle': videoTitle,
                    'videoThumbnail': videoThumbnail,
                    'videoDescription': videoDescription,
                    'privacyStatus': privacyStatus,
                    'duration': duration,
                }
                print('currently process video info 562: ', video_info)
                videos.append(video_info)

                playlist_details = {
                    'playlist_videos': videos
                }

            return Response(playlist_details, status=status.HTTP_200_OK)
        except Exception as e:
            # Return an error message
            print('videos error  >> ', e)
            return Response({'Error': str(e)}, status=status.HTTP_404_NOT_FOUND)


class RateVideoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, videoId):
        try:
            rating = request.data.get('rating')
            if rating not in ['like', 'dislike']:
                raise ValueError('Invalid rating value')

            youtube = create_user_youtube_object(request)
            if youtube is None:
                raise AttributeError('youtube object creation failed!!')

            # Perform the YouTube API call to rate the video
            youtube.videos().rate(id=videoId, rating=rating).execute()

            return Response({'message': f'Video {rating}d successfully.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'Error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
