import requests
import json
from bs4 import BeautifulSoup
import sqlite3
from tqdm import tqdm
import webbrowser
import plotly.graph_objects as go

CACHE_FILENAME = 'movies.json'
DBNAME = 'movie_imdb.db'
CACHE_DICT = {}


def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}

    return cache_dict

def save_cache(cache_dict):
    ''' Saves the current state of the cache to disk
    
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    
    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close() 

def make_url_request_using_cache(url, cache):
    if url in cache.keys():
        # print("Using cache")
        return cache[url]
    else:
        # print('Fetching')
        response = requests.get(url)
        cache[url] = response.text
        save_cache(cache)
        return cache[url]

def build_movie_dict():
    ''' Make a dictionary that maps movie list to movie page url from url
    Parameters
    ----------
    None
    Returns
    -------
    dict
        key is a movie name and value is the movie info 
    '''

    response = make_url_request_using_cache(url, CACHE_DICT)
    soup = BeautifulSoup(response, 'html.parser')
    movie_list = soup.find_all(class_ = 'posterColumn')

    for movie in tqdm(movie_list):
    
        full_link = 'https://www.imdb.com' + movie.find('a')['href']
        movie_name = movie.find('img').get('alt', '')
        index = movie.find("span").attrs['data-value']
        top_movies[movie_name] = {}
        top_movies[movie_name]['index'] = index
        top_movies[movie_name]['full_link'] = full_link
        top_movies[movie_name]['movie_name'] = movie_name

    for movie in tqdm(top_movies):
        
        movie_content = make_url_request_using_cache(top_movies[movie]['full_link'],CACHE_DICT)
        details = BeautifulSoup(movie_content, 'html.parser')
        Json = json.loads("".join(details.find("script",{"type":"application/ld+json"}).contents))

        try:
            top_movies[movie]['director'] = Json['director']['name']
        except:
            top_movies[movie]['director'] = ', '.join([item['name'] for item in Json['director']]) 

        top_movies[movie]['stars'] = ', '.join([n['name'] for n in Json['actor']]) 

        if type(Json['genre']) == str:
            top_movies[movie]['genre'] = Json['genre']
        else:
            top_movies[movie]['genre'] = ', '.join(Json['genre'])

        top_movies[movie]['date_published'] = Json['datePublished']
        top_movies[movie]['ratingCount'] = Json['aggregateRating']['ratingCount']
        top_movies[movie]['ratingValue'] = Json['aggregateRating']['ratingValue']
        
        try:
            top_movies[movie]['content_rating'] = Json['contentRating']
        except:
            top_movies[movie]['content_rating'] = 'NA'

    return top_movies

def init_db():
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    statement = '''
        DROP TABLE IF EXISTS 'movies';
    '''
    cur.execute(statement)

    statement = '''
        DROP TABLE IF EXISTS 'directors';
    '''
    cur.execute(statement)

    statement = '''
        DROP TABLE IF EXISTS 'stars';
    '''
    cur.execute(statement)

    statement = '''
        CREATE TABLE 'movies' (
                'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
                'IMDB_Rank' INTEGER,
                'Name' TEXT NOT NULL,
                'Link' TEXT NOT NULL,
                'Genre' TEXT NOT NULL,
                'RatingValue' REAL,
                'RatingCount' REAL,
                'ContentRating' TEXT NOT NULL,
                'Date_published' TEXT NOT NULL
        );
    '''
    cur.execute(statement)

    statement = '''
        CREATE TABLE 'directors' (
                'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
                'MovieName' TEXT NOT NULL,
                'DirectorName' TEXT NOT NULL
        );
    '''
    cur.execute(statement)

    statement = '''
        CREATE TABLE 'stars' (
                'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
                'MovieName' TEXT NOT NULL,
                'StarName' TEXT NOT NULL
        );
    '''
    cur.execute(statement)

    conn.commit()
    conn.close()


def insert_movies():
    conn = sqlite3.connect(DBNAME)
    conn.text_factory = str
    cur = conn.cursor()

    for movie in top_movies:

        insertion = (None, top_movies[movie]['index'], top_movies[movie]['movie_name'], 
                    top_movies[movie]['full_link'], top_movies[movie]['genre'], top_movies[movie]['ratingValue'], 
                    top_movies[movie]['ratingCount'],top_movies[movie]['content_rating'],top_movies[movie]['date_published'])
        statement = 'INSERT INTO "movies" '
        statement += 'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'
        cur.execute(statement, insertion)
    conn.commit()
    conn.close()

def insert_directors():
    conn = sqlite3.connect(DBNAME)
    conn.text_factory = str
    cur = conn.cursor()

    for movie in top_movies:

        insertion = (None, top_movies[movie]['movie_name'], top_movies[movie]['director'])
        statement = 'INSERT INTO "directors" '
        statement += 'VALUES (?, ?, ?)'
        cur.execute(statement, insertion)

    conn.commit()
    conn.close()

def insert_stars():
    conn = sqlite3.connect(DBNAME)
    conn.text_factory = str
    cur = conn.cursor()

    for movie in top_movies:

        insertion = (None, top_movies[movie]['movie_name'], top_movies[movie]['stars'])
        statement = 'INSERT INTO "stars" '
        statement += 'VALUES (?, ?, ?)'
        cur.execute(statement, insertion)

    conn.commit()
    conn.close()

def plot_rating_count():
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    statement = '''
        SELECT ContentRating As Rated, COUNT(*) As Num
        FROM movies
        GROUP BY ContentRating 
        ORDER BY COUNT(*) DESC
        ;
    '''
    output = cur.execute(statement)
    output = list(cur.fetchall())

    conn.commit()
    conn.close()

    rated = []
    num = []
    for i in output:
        rated.append(i[0])
        num.append(i[1])
    fig = go.Figure([go.Bar(x=rated, y=num, text=num, textposition='auto')])
    fig.show()

def plot_year_count():
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    statement = '''
        SELECT SUBSTR(Date_published, 1, 4) AS Year, count(*) AS Num
        FROM movies
        GROUP BY SUBSTR(Date_published, 1, 4) 
        
        ;
    '''
    output = cur.execute(statement)
    output = list(cur.fetchall())

    conn.commit()
    conn.close()

    year = []
    num = []
    for i in output:
        year.append(i[0])
        num.append(i[1])
    fig = go.Figure([go.Bar(x=year, y=num, text=num, textposition='auto')])
    fig.show()

def plot_director_count():
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    statement = '''
        WITH split(word, str) AS (
            SELECT '', DirectorName||',' FROM directors
            UNION ALL SELECT
            substr(str, 0, instr(str, ',')),
            substr(str, instr(str, ',')+1)
            FROM split WHERE str!=''
            ) SELECT ltrim(word,'  ') AS Genre,count(*) AS Num FROM split 
            WHERE word!=''
            GROUP BY ltrim(word,'  ') 
            HAVING COUNT(*) >  2
            ORDER BY COUNT(*) DESC
        ;
    '''
    output = cur.execute(statement)
    output = list(cur.fetchall())

    conn.commit()
    conn.close()

    name = []
    num = []
    for i in output:
        name.append(i[0])
        num.append(i[1])
    fig = go.Figure([go.Bar(x=name, y=num, text=num, textposition='auto')])
    fig.show()

def plot_celebrity_count():
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    statement = '''
        WITH split(word, str) AS (
            SELECT '', StarName||',' FROM stars
            UNION ALL SELECT
            substr(str, 0, instr(str, ',')),
            substr(str, instr(str, ',')+1)
            FROM split WHERE str!=''
            ) SELECT ltrim(word,'  ') AS Genre,count(*) AS Num FROM split 
            WHERE word!=''
            GROUP BY ltrim(word,'  ') 
            HAVING COUNT(*) >  2
            ORDER BY COUNT(*) DESC
    '''
    output = cur.execute(statement)
    output = list(cur.fetchall())

    conn.commit()
    conn.close()

    name = []
    num = []
    for i in output:
        name.append(i[0])
        num.append(i[1])
    fig = go.Figure([go.Bar(x=name, y=num, text=num, textposition='auto')])
    fig.show()

def plot_genre_count():
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    statement = '''
        WITH split(word, str) AS (
            SELECT '', Genre||',' FROM movies
            UNION ALL SELECT
            substr(str, 0, instr(str, ',')),
            substr(str, instr(str, ',')+1)
            FROM split WHERE str!=''
            ) SELECT ltrim(word,'  ') AS Genre,count(*) AS Num FROM split 
            WHERE word!=''
            GROUP BY ltrim(word,'  ') 
            ORDER BY COUNT(*) DESC
    '''
    output = cur.execute(statement)
    output = list(cur.fetchall())

    conn.commit()
    conn.close()

    name = []
    num = []
    for i in output:
        name.append(i[0])
        num.append(i[1])
    fig = go.Figure([go.Bar(x=name, y=num, text=num, textposition='auto')])
    fig.show()

def load_help_text():
    with open('help.txt') as f:
        return f.read()

def interactive_prompt():
    
    help_text = load_help_text()
    response = ''
    print("Find out more about top 250 movies of all time! Enter 'help' to see the options")

    while response != 'exit':
        response = input('Enter a command: ')

        if response == 'help':
            print(help_text)
            continue

        if response in top_movies:
            webbrowser.open(top_movies[response]['full_link'])

        elif response.lower() == 'director':
            print('Generating...')
            plot_director_count()

        elif response.lower() == 'genre':
            print('Generating...')
            plot_genre_count()

        elif response.lower() == 'actor':
            print('Generating...')
            plot_celebrity_count()

        elif response.lower() == 'rated':
            print('Generating...')
            plot_rating_count()

        elif response.lower() == 'year':
            print('Generating...')
            plot_year_count()

        elif response == 'exit':
            print('Bye...')
            break
        
        else:
            print('Command not recognized...')



    
url = 'https://www.imdb.com/chart/top?ref_=nv_mv_250'
CACHE_DICT = open_cache()
top_movies = {}
build_movie_dict()
init_db()
insert_movies()
insert_directors()
insert_stars()
interactive_prompt()
    
    
    
    
    

    
    

