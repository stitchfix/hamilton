from typing import List, Dict, Any

import click

from hamilton import driver, graph
import helloworld
import playlist

"""
Implementing the metaflow examples. Some observations:
1. Configuring is a little tricky -- let's let examples determine what input is a config and what is a parameter
    - Currently sticking it in computed, but that's just ugly
    - Should it be in config? Maybe? I don't know.
2. We could use things to process Tuple[..., ...], similar to extract_columns
3. Handling side-effects -- where should that live? IMO the framework should handle it
4. The @does operator should be able to run on non-kwarg inputs -- E.G. just *args
5. We should really be able to handle typing generics -- as it stands its a bit of a mess...
6. How to handle external dataloaders? Some ideas:
    - @input_data on functions with adapters you pass in
    - Convention to have a data loader module, this could be passed in and validated in a driver.
    - ???
"""


class MetaflowDriver:
    def __init__(self, *modules, config=None):
        self.function_graph = graph.FunctionGraph(*modules, config=config if config is not None else {})

    def execute(self, nodes: List[str]):
        nodes_to_execute = [self.function_graph.nodes[node_name] for node_name in nodes]
        return self.function_graph.execute()


@click.group()
def main():
    pass


@main.command()
def run_helloworld():
    dr = MetaflowDriver(helloworld)
    dr.execute(['end'])


@main.command()
@click.option('--genre', type=str, help="Genre of movies to select from", default='Sci-fi')
@click.option('--recommendations', type=int, help="Number of reommendations to select", default=5)
@click.option('--movie-file-location', type=str, default="data/movies.csv")
def run_playlist(**parameters):
    def print_recommendations(
            genre: str,
            movie_recommendations: list,
            bonus_movie: str,
            bonus_movie_genre: str):
        """Prints out recommendations. TOOD -- add this to a results builder,
        or decide the best way to handle side-effects"""
        print("Playlist for movies in genre '%s'" % genre)
        for pick, movie in enumerate(movie_recommendations, start=1):
            print("Pick %d: '%s'" % (pick, movie))
        print("Bonus Pick: '%s' from '%s'" % (bonus_movie, bonus_movie_genre))

    print(parameters)

    df = MetaflowDriver(playlist, config=parameters)  # Construct it with the config
    data = df.execute(['movie_recommendations', 'bonus_movie', 'bonus_movie_genre', 'genre'])
    return print_recommendations(
        genre=data['genre'],
        movie_recommendations=data['movie_recommendations'],
        bonus_movie=data['bonus_movie'],
        bonus_movie_genre=data['bonus_movie_genre']
    )



if __name__ == '__main__':
    main()
