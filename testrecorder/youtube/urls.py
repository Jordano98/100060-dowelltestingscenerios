# youtube/urls.py
from django.urls import path
from .views import (logout_view, index, create_broadcast,
                    CreateBroadcastView, TransitionBroadcastView, PlaylistItemsInsertView,
                    FetchPlaylistsView, CreatePlaylistView)
from .views_w import UserChannelsView, DeleteVideoView, LoadVideoView

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
]
# Testing_new_deploy 2023-06-15T14:19:21.936291