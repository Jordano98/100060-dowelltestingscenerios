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


def create_user_youtube_object(request):
    """
    Create a YouTube object using the v3 version of the API and
    the authenticated user's credentials.
    """
    print('Creating youtube object...')
    try:
        # Retrieve the YoutubeUserCredential object associated with the authenticated user
        youtube_user = YoutubeUserCredential.objects.get(user=request.user)

        # Retrieve the user's credentials associated with the YoutubeUserCredential object
        credentials_data = youtube_user.credential

        try:
            # Convert the JSON string to a dictionary
            credentials_data_dict = json.loads(credentials_data)
            # Create credentials from the dictionary
            credentials = Credentials.from_authorized_user_info(info=credentials_data_dict)
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


class FetchlibraryPlaylists(APIView):

    renderer_classes = [JSONRenderer]

    def get(self, request, *args, **kwargs):
        try:
            youtube = create_user_youtube_object(request)
            print('youtube 439:', youtube)
            if youtube is None:
                raise AttributeError('youtube object creation failed!!')

            # Fetch channel information and subscribers count
            try:
                channel_request = youtube.channels().list(
                    part='snippet,statistics',
                    mine=True
                )
                channel_response = channel_request.execute()

                if 'items' not in channel_response:
                    raise AttributeError('Failed to fetch channel information.')

                if 'items' in channel_response and len(channel_response['items']) > 0:
                    channel = channel_response.get('items', {})[0]
                    channel_title = channel.get('snippet', {}).get('title', '')
                    subscribers_count = channel.get('statistics', {}).get('subscriberCount', '')
                else:
                    channel_title = ''
                    subscribers_count = 0

            except Exception as channel_error:
                print("Error while fetching channel information: " + str(channel_error))
                channel_title = ''
                subscribers_count = 0  # Set default values or handle the error case

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
                'subscribers_count': subscribers_count,
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
        print('request videos against this Playlist Id :', playlistId)
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
                # part="snippet,statistics.viewCount",
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

                video_title = videoItem.get('snippet', {}).get('title', '')  # Error handling include
                resource_id = videoItem.get('snippet', {}).get('resourceId', {})
                if 'videoId' not in resource_id:
                    continue

                videoId = resource_id.get('videoId', '')
                videoTitle = video_title
                videoThumbnail = videoItem.get('snippet', {}).get('thumbnails', {}).get('medium', {}).get('url',
                                                                                                          'No Thumbnail Available')
                videoDescription = videoItem.get('snippet', {}).get('description', '')
                playlistItem_id = videoItem.get('id', '') # use for Remove video from playlist

                try:
                    video_response = youtube.videos().list(
                        # part='contentDetails, status',
                        part='contentDetails, status, statistics',
                        id=videoId
                    ).execute()
                    print('Video Information:', video_response)

                    video_info = video_response.get('items', [])[0]
                    privacyStatus = video_info.get('status', {}).get('privacyStatus', 'Unknown')
                    duration = video_info.get('contentDetails', {}).get('duration', '00:00')
                    video_viewCount = video_info.get('statistics', {}).get('viewCount', '')
                    video_likeCount = video_info.get('statistics', {}).get('likeCount', '')
                    video_commentCount = video_info.get('statistics', {}).get('commentCount', '')
                except HttpError as e:
                    # Handle HttpError (e.g., video not found)
                    privacyStatus = 'Unknown'
                    duration = '00:00'

                video_info = {
                    'videoId': videoId,
                    'videoTitle': videoTitle,
                    'videoThumbnail': videoThumbnail,
                    'videoDescription': videoDescription,
                    'playlistItem_id': playlistItem_id,
                    'privacyStatus': privacyStatus,
                    'duration': duration,
                    'video_viewCount': video_viewCount,
                    'video_likeCount': video_likeCount,
                    'video_commentCount': video_commentCount,
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

class Delete_video(APIView):
    """
    API view class for Remove videos from YouTube Playlist.

    Methods:
        Delete(request): Remoe selected video from list

     Attributes:
        permission_classes: a list containing the IsAuthenticated permission class to ensure only authenticated users
        can access this view.
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, playlistitem_id):
        try:
            youtube = create_user_youtube_object(request)
            if youtube is None:
                raise AttributeError('YouTube object creation failed!!')

            # Perform the YouTube API call to delete the video
            print(f'Now Remove video id is: {playlistitem_id} from the playlist')
            response = youtube.playlistItems().delete(
                id=playlistitem_id
            ).execute()

            print(response)

            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            print(f"An error occurred: {e}")
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)