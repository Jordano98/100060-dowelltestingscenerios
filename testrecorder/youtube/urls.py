# youtube/urls.py
from django.urls import path
from .views import (logout_view, index, create_broadcast,
                    CreateBroadcastView, TransitionBroadcastView, PlaylistItemsInsertView,
                    FetchPlaylistsView, CreatePlaylistView)
from .views_w import UserChannelsView, DeleteVideoView, LoadVideoView, YouTubeVideoAPIView
from .views_library import FetchlibraryPlaylists, SelectedPlaylistLoadVideo, RateVideoView

urlpatterns = [
    path('', index, name='index'),
    path('createbroadcast/', create_broadcast, name='createbroadcast'),
    path('createbroadcast/api/', CreateBroadcastView.as_view(),
         name='create-broadcast-api'),
    path('transitionbroadcast/api/', TransitionBroadcastView.as_view(),
         name='transition-broadcast-api'),
    path('playlistitemsinsert/api/', PlaylistItemsInsertView.as_view(),
         name='playlist-items-insert-api'),
    path('fetchplaylists/api/', FetchPlaylistsView.as_view(), name='fetch-playlists'),
    path('createplaylist/api/', CreatePlaylistView.as_view(), name='create-playlist'),
    path('logout/', logout_view, name='logout'),
    path('channels/api/', UserChannelsView.as_view(), name='user_channel'),
    path('delete-video/api/', DeleteVideoView.as_view(), name='delete-video'),
    path('videos/api/',  LoadVideoView.as_view(), name='videos'),
    path('video/<str:broadcast_id>/',
         YouTubeVideoAPIView.as_view(), name='youtube_video'),
        # methods call for library page
    path('fetchlibraryplaylists/api/', FetchlibraryPlaylists.as_view(), name='fetchlibrary-playlists'),
    path('videos/api/<str:playlistId>/', SelectedPlaylistLoadVideo.as_view(), name='videos_from_playlistId'),
    path('videos/api/rate/<str:videoId>/', RateVideoView.as_view(), name='rate_video'),
]
