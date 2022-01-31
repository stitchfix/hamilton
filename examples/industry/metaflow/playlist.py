import copy
import random
from typing import Any, Dict, List, Tuple


### Configuration to choose from
### These will get erased as they'll get passed in as overrides/config

def movie_data(movie_file_location: str) -> dict:
    """Loads movie data from a CSV"""
    columns = ["movie_title", "genres"]
    dataframe = dict((column, list()) for column in columns)

    # Parse the CSV header.
    movie_data_raw = open(movie_file_location).read()
    lines = movie_data_raw.split("\n")
    header = lines[0].split(",")
    idx = {column: header.index(column) for column in columns}

    # Populate our dataframe from the lines of the CSV file.
    for line in lines[1:]:
        if not line:
            continue

        fields = line.rsplit(",", 4)
        for column in columns:
            dataframe[column].append(fields[idx[column]])
    return dataframe


def bonus_movie_and_genre(movie_data: dict, genre: str) -> tuple:
    movies = [
        (movie, genres)
        for movie, genres in zip(
            movie_data["movie_title"], movie_data["genres"]
        )
        if genre.lower() not in genres.lower()
    ]
    return random.choice(movies)


def bonus_movie(bonus_movie_and_genre: tuple) -> str:
    return bonus_movie_and_genre[0]


def bonus_movie_genre(bonus_movie_and_genre: tuple) -> str:
    return bonus_movie_and_genre[1]


def genre_movies(movie_data: dict, genre: str) -> list:
    return [
        movie
        for movie, genres in zip(
            movie_data["movie_title"], movie_data["genres"]
        )
        if genre.lower() in genres.lower()
    ]


def movie_recommendations(genre_movies: list, recommendations: int) -> list:
    shuffled = copy.copy(genre_movies)
    import random
    random.shuffle(shuffled)
    return shuffled[0:recommendations]
