# SI507_Final_Project

This is my final project for SI 507. Here you can find all the information about top 250 movies and top 250 TV series of all time. \
The movie information is from https://www.imdb.com/chart/top?ref_=nv_mv_250.\
The drama information is from https://imdb.to/33V5QdO.

## Instructions

Main.py will ask you to input 'Movie' or 'Drama'. If 'movie' is entered, movie.py will be executed, while if  'drama' is entered, drama.py will be executed. Both movie.py and drama.py will scrape the top 250 movies or drama information from IMDB and store them in the database: movie.db and drama.db. Caching is also used to store the JSON file. 

The system will allow users to input the movie names and direct them directly to the IMDB page. It will also allow users to see multiple graphs using plotly based on different information gathered, such as genre, directors, actors and etc. More command keywords can be found by entering 'help'. The system will exit when the user enters 'exit'. 

