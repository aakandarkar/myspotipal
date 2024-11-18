import requests

def get_top_items(access_token, time_range, item_type):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(f'https://api.spotify.com/v1/me/top/{item_type}?&time_range={time_range}', headers=headers)
    
    if response.status_code != 200:
        print(f"Error fetching top {item_type} for {time_range}:")
        print("Error code:", response.status_code)
        print("Error response:", response.text)
        return None

    items = response.json()['items']
    # Keep only necessary fields
    simplified_items = []
    for item in items:
        simplified_item = {
            'name': item['name'],
            'popularity': item.get('popularity'),
        }
        if item_type == 'artists':
            simplified_item['genres'] = item['genres']
        elif item_type == 'tracks':
            simplified_item['artists'] = [artist['name'] for artist in item['artists']]
            simplified_item['album'] = item['album']['name']
        simplified_items.append(simplified_item)
    return simplified_items

def summarize_data(data, item_type):
    summary = {}
    if item_type == 'artists':
        genres = [genre for item in data for genre in item.get('genres', [])]
        summary['top_genres'] = list(set(genres))
    elif item_type == 'tracks':
        summary['top_artists'] = list(set(artist for item in data for artist in item.get('artists', [])))
    
    summary['average_popularity'] = sum(item.get('popularity', 0) for item in data) / len(data)
    return summary

def get_followed_artists(access_token):
    url = 'https://api.spotify.com/v1/me/following?type=artist&limit=50'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    artists = []
    while url:
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print("Error fetching followed artists:")
            print("Request URL:", url)
            print("Status Code:", response.status_code)
            print("Response Text:", response.text)
            return None

        data = response.json()
        for artist in data['artists']['items']:
            simplified_artist = {
                'name': artist['name'],
            }
            artists.append(simplified_artist)
        
        if 'next' in data['artists'] and data['artists']['next']:
            url = data['artists']['next']
        else:
            break

    return artists

def get_user_playlists(access_token):
    url = 'https://api.spotify.com/v1/me/playlists?limit=50'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    playlists = []
    while url and len(playlists) < 100:
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print("Error fetching user playlists:")
            print("Request URL:", url)
            print("Status Code:", response.status_code)
            print("Response Text:", response.text)
            return None

        data = response.json()
        for playlist in data['items']:
            simplified_playlist = {
                'id': playlist['id'],
                'name': playlist['name'],
                'uri': playlist['uri']
            }
            playlists.append(simplified_playlist)
        
        if len(playlists) >= 100:
            break
        
        url = data['next']

    return playlists[:100]

def get_saved_shows(access_token):
    url = 'https://api.spotify.com/v1/me/shows?limit=50'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    shows = []
    while url:
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print("Error fetching saved shows:")
            print("Request URL:", url)
            print("Status Code:", response.status_code)
            print("Response Text:", response.text)
            return None

        data = response.json()
        for item in data['items']:
            show = item.get('show', {})
            simplified_show = {
                'name': show.get('name', 'Unknown Show'),
                'description': show.get('description', ''),
                'publisher': show.get('publisher', ''),
            }
            shows.append(simplified_show)
        
        url = data.get('next')

    print(f"Fetched {len(shows)} shows")
    return shows

def get_recently_played_tracks(access_token):
    url = 'https://api.spotify.com/v1/me/player/recently-played?limit=50'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    recent_tracks = []
    while url:
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print("Error fetching recent tracks:")
            print("Request URL:", url)
            print("Status Code:", response.status_code)
            print("Response Text:", response.text)
            return None

        data = response.json()
        for track in data['items']:
            simplified_track = {
                'name': track['track']['name'],
                'artists': [{'name': artist['name'], 'id': artist['id']} for artist in track['track']['artists']],
                'album': {'name': track['track']['album']['name'], 'id': track['track']['album']['id']},
            }
            recent_tracks.append(simplified_track)
        
        url = data.get('next')

    return recent_tracks

def gather_spotify_data(access_token, cache):
    # Fetch data using the helper functions
    time_ranges = ['short_term', 'medium_term', 'long_term']
    top_artists_data = {}
    top_tracks_data = {}

    for time_range in time_ranges:
        top_artists_data[time_range] = get_top_items(access_token, time_range, 'artists')
        top_tracks_data[time_range] = get_top_items(access_token, time_range, 'tracks')

    spotify_data = {
        'top_artists': top_artists_data,
        'top_tracks': top_tracks_data
    }

    print("Spotify data to be cached:", spotify_data)  # Debug statement
    cache.set('spotify_data', spotify_data)  # Explicitly cache the data
    return spotify_data

def search_artist(artist_name, access_token):
    url = 'https://api.spotify.com/v1/search'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    params = {
        'q': artist_name,
        'type': 'artist',
        'limit': 1
    }

    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        print("Error searching for artist:")
        print("Request URL:", url)
        print("Status Code:", response.status_code)
        print("Response Text:", response.text)
        return None

    data = response.json()
    if data['artists']['items']:
        artist = data['artists']['items'][0]
        return {
            'id': artist['id'],
            'name': artist['name'],
            'genres': artist['genres'],
            'followers': artist['followers']['total'],
            'popularity': artist['popularity'],
            'url': artist['external_urls']['spotify']
        }
    else:
        return None
    
def get_artist_info(self, artist_id, access_token):
    url = f'https://api.spotify.com/v1/artists/{artist_id}'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print("Error fetching artist info:")
        print("Request URL:", url)
        print("Status Code:", response.status_code)
        print("Response Text:", response.text)
        return None

    artist = response.json()
    return {
        'name': artist['name'],
        'genres': artist['genres'],
        'followers': artist['followers']['total'],
        'popularity': artist['popularity'],
        'url': artist['external_urls']['spotify']
    }

def search_item(query, search_type, access_token):
    """
    Search for a specific item type on Spotify (e.g., album, artist).
    """
    url = 'https://api.spotify.com/v1/search'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    params = {
        'q': query,
        'type': search_type,
        'limit': 1
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print(f"Error searching for {search_type}: {response.status_code}")
        return None

    data = response.json()

    if search_type == 'artist' and data['artists']['items']:
        return _process_item(data['artists']['items'][0], search_type)
    
    elif search_type == 'track' and data['tracks']['items']:
        return _process_item(data['tracks']['items'][0], search_type)
    
    elif search_type == 'album' and data['albums']['items']:
        return _process_item(data['albums']['items'][0], search_type)
    
    elif search_type == 'playlist' and data['playlists']['items']:
        return _process_item(data['playlists']['items'][0], search_type)
    
    elif search_type == 'show' and data['shows']['items']:
        return _process_item(data['shows']['items'][0], search_type)
    
    elif search_type == 'episode' and data['episodes']['items']:
        return _process_item(data['episodes']['items'][0], search_type)
    
    elif search_type == 'audiobook' and data['audiobooks']['items']:
        return _process_item(data['audiobooks']['items'][0], search_type)
    
    else:
        return None
    
def _process_item(item, item_type):
    """Process different types of Spotify items"""
    if item_type == 'artist':
        return {
            'id': item['id'],
            'name': item['name'],
            'genres': item.get('genres', []),
            'followers': item.get('followers', {}).get('total'),
            'popularity': item.get('popularity'),
            'images': item.get('images', []),
            'uri': item['uri']
        }
    
    elif item_type == 'track':
        return {
            'id': item['id'],
            'name': item['name'],
            'artists': [{'id': a['id'], 'name': a['name']} for a in item['artists']],
            'album': {
                'id': item['album']['id'],
                'name': item['album']['name'],
                'release_date': item['album'].get('release_date')
            },
            'duration_ms': item.get('duration_ms'),
            'popularity': item.get('popularity'),
            'preview_url': item.get('preview_url'),
            'uri': item['uri']
        }
    
    elif item_type == 'album':
        return {
            'id': item['id'],
            'name': item['name'],
            'artists': [{'id': a['id'], 'name': a['name']} for a in item['artists']],
            'release_date': item.get('release_date'),
            'total_tracks': item.get('total_tracks'),
            'images': item.get('images', []),
            'uri': item['uri']
        }
    
    elif item_type == 'playlist':
        return {
            'id': item['id'],
            'name': item['name'],
            'owner': {
                'id': item['owner']['id'],
                'name': item['owner'].get('display_name', 'Unknown')
            },
            'total_tracks': item['tracks']['total'],
            'description': item.get('description'),
            'images': item.get('images', []),
            'uri': item['uri']
        }
    
    elif item_type == 'show':
        return {
            'id': item['id'],
            'name': item['name'],
            'description': item.get('description'),
            'publisher': item.get('publisher'),
            'media_type': item.get('media_type'),
            'total_episodes': item.get('total_episodes'),
            'languages': item.get('languages', []),
            'images': item.get('images', []),
            'explicit': item.get('explicit', False),
            'uri': item['uri']
        }
    
    elif item_type == 'episode':
        return {
            'id': item['id'],
            'name': item['name'],
            'description': item.get('description'),
            'duration_ms': item.get('duration_ms'),
            'languages': item.get('languages', []),
            'release_date': item.get('release_date'),
            'explicit': item.get('explicit', False),
            'show': {
                'id': item['show'].get('id'),
                'name': item['show'].get('name'),
                'publisher': item['show'].get('publisher')
            } if 'show' in item else None,
            'images': item.get('images', []),
            'uri': item['uri']
        }
    
    elif item_type == 'audiobook':
        return {
            'id': item['id'],
            'name': item['name'],
            'authors': [author['name'] for author in item.get('authors', [])],
            'narrators': [narrator['name'] for narrator in item.get('narrators', [])],
            'description': item.get('description'),
            'publisher': item.get('publisher'),
            'languages': item.get('languages', []),
            'total_chapters': item.get('total_chapters'),
            'duration_ms': item.get('duration_ms'),
            'explicit': item.get('explicit', False),
            'images': item.get('images', []),
            'uri': item['uri']
        }
    
    # Default case for unknown types
    return {
        'id': item['id'],
        'name': item['name'],
        'uri': item['uri']
    }
    
def get_artist_id(spotify_client, artist_name):
    """
    Function to search for an artist by name and return the Spotify artist ID.
    """
    # Use search_item function to search for the artist by name
    search_results = spotify_client.search_item(query=artist_name, search_type="artist")
    
    # Extract the artist ID from the search results
    if search_results and search_results['artists']['items']:
        artist_id = search_results['artists']['items'][0]['id']  # Get the first artist's ID
        return artist_id
    else:
        print(f"Artist '{artist_name}' not found.")
        return None