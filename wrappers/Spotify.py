import os
# Spotify library.
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
# URL conversions.
import urllib.request
import urllib.parse
import re

APIs = {
    "spotify": {
        "client_id": os.environ.get("spotify_client_id"),
        "client_secret": os.environ.get("spotify_client_secret")
    },
    "youtube": {
        "api_key": os.environ.get("youtube_api_key"),
        "client_id": os.environ.get("youtube_client_id"),
        "client_secret": os.environ.get("youtube_api_secret")
    }
}


def getTracks(playlistURL):
    # Creating and authenticating our Spotify app.
    client_credentials_manager = SpotifyClientCredentials(
        APIs["spotify"]["client_id"], APIs["spotify"]["client_secret"])
    spotify = spotipy.Spotify(
        client_credentials_manager=client_credentials_manager)

    # Getting a playlist.
    results = spotify.user_playlist_tracks(user="", playlist_id=playlistURL)
    items = results["items"]
    while results["next"] is not None:
        results = spotify.next(results)
        items += results["items"]

    trackList = []
    # For each track in the playlist.
    for i in items:
        # In case there's only one artist.
        if (i["track"]["artists"].__len__() == 1):
            # We add trackName - artist.
            trackList.append(i["track"]["name"] + " - " +
                             i["track"]["artists"][0]["name"])
        # In case there's more than one artist.
        else:
            nameString = ""
            # For each artist in the track.
            for index, b in enumerate(i["track"]["artists"]):
                nameString += (b["name"])
                # If it isn't the last artist.
                if (i["track"]["artists"].__len__() - 1 != index):
                    nameString += ", "
            # Adding the track to the list.
            trackList.append(i["track"]["name"] + " - " + nameString)

    return trackList


def searchYoutubeAlternative(songName):
    # YouTube will block you if you query too many songs using this search.
    textToSearch = songName
    query = urllib.parse.quote(textToSearch)
    url = "https://www.youtube.com/results?search_query=" + query
    response = urllib.request.urlopen(url)
    html = response.read()
    soup = bs4(html, 'html.parser')
    for vid in soup.findAll(attrs={'class': 'yt-uix-tile-link'}):
        print('https://www.youtube.com' + vid['href'])


def searchYoutube(songName):
    html = urllib.request.urlopen(
        f"https://www.youtube.com/results?search_query={songName}")

    video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
    if(len(video_ids) == 0):
        return
    else:
        return f"https://www.youtube.com/watch?v={video_ids[0]}"


def getYoutubeLinksFromPlaylist(playlist):
    tracks = getTracks(playlist)
    songs = []
    for i in tracks:
        songs.append((searchYoutube(urllib.parse.quote_plus(i)), i))
    return songs
