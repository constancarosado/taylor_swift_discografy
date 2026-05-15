import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
from flask import render_template, Flask, abort
import logging
import db

APP = Flask(__name__)

@APP.before_request
def before_request():
    db.connect()

@APP.teardown_request
def teardown_request(exception):
    db.close()


# Start page
@APP.route('/')
def index():
    stats = {}
    stats = db.execute('''
    SELECT * FROM
      (SELECT COUNT(*) n_albums FROM ALBUMS)
    JOIN
      (SELECT COUNT(*) n_musics FROM MUSICS)
    JOIN
      (SELECT COUNT(*) n_people FROM PEOPLE)
    JOIN
      (SELECT COUNT(*) n_tags FROM TAGS)
    ''').fetchone()
    logging.info(stats)
    return render_template('index.html', stats=stats)

# --- ÁLBUNS ---

@APP.route('/albums/')
def list_albums():
    albums = db.execute(
      '''
      SELECT album_id, title, category, url
      FROM ALBUMS
      ORDER BY title
      ''').fetchall()
    return render_template('album-list.html', albums=albums)

# Detalhes do Álbum
@APP.route('/albums/<int:id>/')
def get_album(id):
    album = db.execute(
        '''
        SELECT album_id, title, category, url
        FROM ALBUMS
        WHERE album_id = ?
        ''', [id]).fetchone()
    
    if album is None: 
        abort(404, 'Album id {} does not exist.'.format(id)) 

    songs = db.execute(
        '''
        SELECT M.music_id, M.title, M.page_views, I.track_number
        FROM MUSICS M
        JOIN INCLUDES I ON M.music_id = I.music_id
        WHERE I.album_id = ?
        ORDER BY I.track_number
        ''', [id]).fetchall()
    
    return render_template('album.html',
                           album=album, songs=songs)

# --- MÚSICAS ---

# Lista de Músicas
@APP.route('/musics/')
def list_musics():
    musics = db.execute(
        '''
        SELECT music_id, title, release_date, page_views
        FROM MUSICS
        ORDER BY page_views DESC
        ''').fetchall()
    return render_template('music-list.html', musics=musics)

# Detalhes da Música
@APP.route('/musics/<int:id>/')
def get_music(id):
    music = db.execute(
        '''
        SELECT music_id, title, release_date, page_views, lyrics, url
        FROM MUSICS
        WHERE music_id = ?
        ''', [id]).fetchone()

    if music is None:
        abort(404, 'Music id {} does not exist.'.format(id))

    artists = db.execute(
        '''
        SELECT P.person_id, P.name
        FROM PEOPLE P
        JOIN PERFORMANCE PR ON P.person_id = PR.person_id
        WHERE PR.music_id = ?
        ORDER BY P.name
        ''', [id]).fetchall()

    writers = db.execute(
        '''
        SELECT P.person_id, P.name
        FROM PEOPLE P
        JOIN WRITERS W ON P.person_id = W.person_id
        WHERE W.music_id = ?
        ORDER BY P.name
        ''', [id]).fetchall()

    producers = db.execute(
        '''
        SELECT P.person_id, P.name
        FROM PEOPLE P
        JOIN PRODUCERS PD ON P.person_id = PD.person_id
        WHERE PD.music_id = ?
        ORDER BY P.name
        ''', [id]).fetchall()

    tags = db.execute(
        '''
        SELECT T.tag_id, T.tag
        FROM TAGS T
        JOIN TAG_WITH TW ON T.tag_id = TW.tag_id
        WHERE TW.music_id = ?
        ORDER BY T.tag
        ''', [id]).fetchall()

    return render_template('music.html',
                           music=music, artists=artists, writers=writers, producers=producers, tags=tags)


# --- PESSOAS (Artistas, Escritores, Produtores) ---

# Lista de Pessoas 
@APP.route('/people/')
def list_people():
    people = db.execute('''
      SELECT person_id, name
      FROM PEOPLE
      ORDER BY name
    ''').fetchall()
    return render_template('person-list.html', people=people)


# Detalhes da Pessoa
@APP.route('/people/<int:id>/')
def get_person(id):
    person = db.execute(
        '''
        SELECT person_id, name
        FROM PEOPLE
        WHERE person_id = ?
        ''', [id]).fetchone()

    if person is None:
        abort(404, 'Person id {} does not exist.'.format(id))

    artist_in = db.execute(
        '''
        SELECT M.music_id, M.title
        FROM MUSICS M JOIN PERFORMANCE PR ON M.music_id = PR.music_id
        WHERE PR.person_id = ?
        ORDER BY M.title
        ''', [id]).fetchall()

    writer_in = db.execute(
        '''
        SELECT M.music_id, M.title
        FROM MUSICS M JOIN WRITERS W ON M.music_id = W.music_id
        WHERE W.person_id = ?
        ORDER BY M.title
        ''', [id]).fetchall()
    
    producer_in = db.execute(
        '''
        SELECT M.music_id, M.title
        FROM MUSICS M JOIN PRODUCERS PD ON M.music_id = PD.music_id
        WHERE PD.person_id = ?
        ORDER BY M.title
        ''', [id]).fetchall()

    return render_template('person.html',
                           person=person, artist_in=artist_in, writer_in=writer_in, producer_in=producer_in)

# --- Tags ---

# Lista de Tags 
@APP.route('/tags/')
def list_tags():
    tags = db.execute('''
      SELECT tag_id, tag
      FROM TAGS
      ORDER BY tag
    ''').fetchall()
    return render_template('tag-list.html', tags=tags)


# --- Interrogações ---
# Interrogação 1: Nome e número de visualizações das músicas (decrescente)

@APP.route('/query1/')
def query1():
    results = db.execute('''
    SELECT title, page_views FROM MUSICS ORDER BY page_views DESC;
    ''').fetchall()
    
    query_title = '1.Qual é nome e número de visualizações das músicas? Ordena por ordem decrescente o número de visualizações.'
    return render_template('query-result.html', results=results, query_title=query_title)

# Interrogação 2: Álbuns cujo total de visualizações esteja entre 100000 e 275000

@APP.route('/query2/')
def query2():
    results = db.execute('''
    SELECT DISTINCT
        A.title,
        A.album_id
    FROM
        ALBUMS A
    JOIN
        INCLUDES I ON A.album_id = I.album_id
    JOIN
        MUSICS M ON I.music_id = M.music_id
    WHERE 
        m.page_views BETWEEN 100000 AND 275000
    ORDER BY 
        a.title;
    ''').fetchall()
    
    query_title = '2.Quais os nome e id dos álbuns cujo número de visualizações esteja entra 100000 e 275000'
    return render_template('query-result.html', results=results, query_title=query_title)

# Interrogação 3: URLs das músicas que contenham a expressão ‘smile’

@APP.route('/query3/')
def query3():
    results = db.execute('''
    SELECT url FROM MUSICS WHERE lyrics LIKE '%smile%' ORDER BY url;
    ''').fetchall()
    
    query_title = '3.Quais são os url das músicas que contenham a expressão ‘smile’? Ordene por url.'
    return render_template('query-result.html', results=results, query_title=query_title)

# Interrogação 4: Título de cada música com número de artistas >= 2

@APP.route('/query4/')
def query4():
    results = db.execute('''
    SELECT
        M.title
    FROM
        MUSICS M
    JOIN
        PERFORMANCE P ON M.music_id = P.music_id
    GROUP BY
        M.music_id, M.title
    HAVING
        COUNT(P.person_id) >= 2
    ORDER BY
        M.title;
    ''').fetchall()
    
    query_title = '4.Selecione o título de cada música cujo número de artistas, que participam na música, seja maior ou igual a 2'
    return render_template('query-result.html', results=results, query_title=query_title)

# Interrogação 5: Para cada escritor, quantas músicas escreveu (QUANT)

@APP.route('/query5/')
def query5():
    results = db.execute('''
    SELECT
        P.name,
        COUNT(W.music_id) AS QUANT
    FROM
        PEOPLE P
    JOIN
        WRITERS W ON P.person_id = W.person_id
    GROUP BY
        P.person_id, P.name
    ORDER BY
        QUANT DESC;
    ''').fetchall()
    
    query_title = '5.Para cada escritor, quantas músicas escreveu? Indique o nome e o número de músicas (coluna chamada QUANT) e ordene de forma decrescente pelo número de músicas.'
    return render_template('query-result.html', results=results, query_title=query_title)

# Interrogação 6: URL do álbum que tem mais músicas (MAX)

@APP.route('/query6/')
def query6():
    result = db.execute('''
    SELECT
        A.url,
        COUNT(I.music_id) AS MAX
    FROM
        ALBUMS A
    JOIN
        INCLUDES I ON A.album_id = I.album_id
    GROUP BY
        A.album_id, A.url
    ORDER BY
        MAX DESC
    LIMIT 1;
    ''').fetchone() # Usar fetchone() porque é apenas um resultado

    results = [result] if result else [] 
    
    query_title = '6.Qual o url do álbum que tem mais músicas? Indique o url e o número de músicas (coluna MAX)'
    return render_template('query-result.html', results=results, query_title=query_title)


# Interrogação 7: Nomes das pessoas que apenas desempenham o papel de artistas

@APP.route('/query7/')
def query7():
    results = db.execute('''
    SELECT
        P.person_id,
        P.name
    FROM
        PEOPLE P
    JOIN
        PERFORMANCE PR ON P.person_id = PR.person_id
    WHERE
        P.person_id NOT IN (SELECT person_id FROM WRITERS)
        AND P.person_id NOT IN (SELECT person_id FROM PRODUCERS)
    GROUP BY
        P.person_id, P.name
    ORDER BY
        P.name;
    ''').fetchall()
    
    query_title = '7.Quais são os nomes das pessoas que apenas desempenham o papel de artistas. Indique o nome, id e ordene por ordem alfabética.'
    return render_template('query-result.html', results=results, query_title=query_title)

# Interrogação 8: Pares pessoa-função (artista, escritor e/ou produtor)

@APP.route('/query8/')
def query8():
    results = db.execute('''
    SELECT
        P.name,
        'Artista' AS Funcao
    FROM
        PEOPLE P
    JOIN
        PERFORMANCE PR ON P.person_id = PR.person_id
    
    UNION 
    
    SELECT
        P.name,
        'Escritor' AS Funcao
    FROM
        PEOPLE P
    JOIN
        WRITERS W ON P.person_id = W.person_id
    
    UNION 
    
    SELECT
        P.name,
        'Produtor' AS Funcao
    FROM
        PEOPLE P
    JOIN
        PRODUCERS PD ON P.person_id = PD.person_id
    
    ORDER BY
        name, Funcao;
    ''').fetchall()
    
    query_title = '8.Quais são os pares pessoa-função (artista, escritor e/ou produtor). Apresente o nome da pessoa e função, ordenando pelo nome, função.'
    return render_template('query-result.html', results=results, query_title=query_title)

# Interrogação 9: Títulos dos álbuns em que todas as músicas incluídas são usadas para a tag 'Pop'

@APP.route('/query9/')
def query9():
    results = db.execute('''
    SELECT
        A.title
    FROM
        ALBUMS A
    WHERE
        A.album_id NOT IN (
            SELECT
                I.album_id
            FROM
                INCLUDES I
            WHERE
                I.music_id NOT IN (
                    SELECT
                        TW.music_id
                    FROM
                        TAG_WITH TW
                    JOIN
                        TAGS T ON TW.tag_id = T.tag_id
                    WHERE
                        T.tag = 'Pop'
                )
        )
    ORDER BY
        A.title;
    ''').fetchall()
    
    query_title = '9.Quais são os títulos dos álbuns em que todas as músicas incluídas são usadas para a tag com a descrição Pop. Ordene os resultados pelo título do álbum'
    return render_template('query-result.html', results=results, query_title=query_title)

# Interrogação 10: Músicas com visualizações superiores à média das outras músicas com a mesma tag

@APP.route('/query10/')
def query10():
    results = db.execute('''
    SELECT DISTINCT
        M.title,
        M.page_views
    FROM
        MUSICS M
    JOIN
        TAG_WITH TW_OUTER ON M.music_id = TW_OUTER.music_id
    WHERE
        M.page_views > (
            SELECT
                AVG(M_INNER.page_views)
            FROM
                MUSICS M_INNER
            JOIN
                TAG_WITH TW_INNER ON M_INNER.music_id = TW_INNER.music_id
            WHERE
                TW_INNER.tag_id = TW_OUTER.tag_id
                AND M_INNER.music_id != M.music_id
        )
    ORDER BY
        M.title;
    ''').fetchall()
    
    query_title = '10.Qual o título e o número de visualizações de página de todas as músicas que possuem uma tag e cujo número de visualizações é superior à média de visualizações de todas as outras músicas que possuem essa mesma tag. Os resultados devem ser ordenados pelo título da música'
    return render_template('query-result.html', results=results, query_title=query_title)

if __name__ == '__main__':
    APP.run(host='0.0.0.0', port=9000, debug=True)