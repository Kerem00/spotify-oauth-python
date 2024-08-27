#   Spotify OAuth Python - Spotify OAuth example with Python using Flask.
#   Copyright (C) 2024  Kerem Biçen

#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.

#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.

#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

from flask import Flask, request, render_template, redirect, url_for
from urllib.parse import urlencode
import requests
import base64

app = Flask(__name__)

CLIENT_ID = "client-id"
CLIENT_SECRET = "client-secret"
scope = "user-top-read"
redirect_uri = "redirect-uri"

limit = 5

headers_basic = {
    "Authorization": "Basic " + base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode(),
    "Content-Type": "application/x-www-form-urlencoded"
}

def get_list(type, token):
    headers = {
        "Authorization": f"Bearer {token['access_token']}",
        "Content-Type": "application/json"
    }
        
    params = {
        "limit": limit
    }

    r = requests.get(f"https://api.spotify.com/v1/me/top/{type}", headers=headers, params=params)

    if r.status_code == 401:
        return None
    
    return r.json()["items"]

def token_refresh(token):
    params = {
        "grant_type": "refresh_token",
        "refresh_token": token["refresh_token"]
    }

    r = requests.post("https://accounts.spotify.com/api/token", headers=headers_basic, params=params).json()

    token["access_token"] = r["access_token"]

@app.route("/")
def index():
    if request.cookies.get("access_token") is not None and request.cookies.get("refresh_token") is not None:
        spotify_token = {
            "access_token": request.cookies.get("access_token"),
            "refresh_token": request.cookies.get("refresh_token")
        }

        artists = get_list("artists", spotify_token)
        
        if not artists:
            token_refresh(spotify_token)

            response = redirect(url_for("index"))
            response.set_cookie("access_token", spotify_token["access_token"], max_age=86400)

            return response

        context = {
            "artists": artists,
            "tracks": get_list("tracks", spotify_token)
        }

        return render_template("index.html", **context)
    else:
        params = {
            "response_type": "code",
            "client_id": CLIENT_ID,
            "scope": scope,
            "redirect_uri": redirect_uri
        }

        return redirect(f"https://accounts.spotify.com/authorize?{urlencode(params)}")

@app.route("/callback")
def callback():
    params = {
        "grant_type": "authorization_code",
        "code": request.args.get("code"),
        "redirect_uri": redirect_uri
    }

    r = requests.post("https://accounts.spotify.com/api/token", headers=headers_basic, params=params).json()

    response = redirect(url_for("index"))
    response.set_cookie("access_token", r["access_token"], max_age=86400)
    response.set_cookie("refresh_token", r["refresh_token"], max_age=86400)

    return response
