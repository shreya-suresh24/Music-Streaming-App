from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from contextlib import contextmanager
from sqlalchemy import or_, func, distinct

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///musicapp.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'  # Change this to a secret key

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

class Song(db.Model):
    song_id = db.Column(db.Integer, primary_key=True)
    song_name = db.Column(db.String(100), nullable=False)
    artist_name = db.Column(db.String(50), nullable=False)
    lyrics = db.Column(db.Text)
    duration = db.Column(db.String(10))
    release_date = db.Column(db.String(20))
    song_link = db.Column(db.String(255))
    album_name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)

class Album(db.Model):
    album_id = db.Column(db.Integer, primary_key=True)
    album_name = db.Column(db.String(100), nullable=False)

class Playlist(db.Model):
    playlist_id = db.Column(db.Integer, primary_key=True)
    playlist_name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)

class PlaylistSong(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    playlist_id = db.Column(db.Integer, nullable=False)
    song_id = db.Column(db.Integer, nullable=False)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

# Routes
@app.route('/welcome')
def welcome():
    return render_template('openopenpage.html')

@app.route('/')
def home():
    username = session.get('username')
    if username:
        user = User.query.filter_by(username=username).first()
        if user:
            # Retrieve the latest 5 songs from the database
            latest_songs = Song.query.order_by(Song.song_id.desc()).limit(5).all()
            return render_template('main_pagemod.html', username=user.username, latest_songs=latest_songs)
    return redirect(url_for('login'))

@app.route('/main')
def main():
    username = session.get('username')
    print("Value of username in session:", username)
    if username:
        user = User.query.filter_by(username=username).first()
        if user:
            return render_template('main_pagemod.html', username=user.username)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    print(request.method)
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        print(username)
        print(password)
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['username'] = username
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('openpage.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        username = request.form.get('username')
        password = request.form.get('password')

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        new_user = User(name=name, email=email, phone=phone, username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully. You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/creator', methods=['GET', 'POST'])
def creator():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Get the current user
    username = session['username']
    user = User.query.filter_by(username=username).first()

    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Handle song deletion
        song_id_to_delete = request.form.get('delete_song')

        if song_id_to_delete:
            # Get the song to delete
            song_to_delete = Song.query.get(song_id_to_delete)

            # Get the album of the song
            album_of_song = Album.query.filter_by(album_name=song_to_delete.album_name).first()

            # Delete the song
            db.session.delete(song_to_delete)
            db.session.commit()

            # Check if there are any remaining songs from the same album
            remaining_songs_in_album = Song.query.filter_by(album_name=album_of_song.album_name).count()

            # If no remaining songs, delete the album
            if remaining_songs_in_album == 0:
                db.session.delete(album_of_song)
                db.session.commit()

    # Query songs added by the current user
    user_songs = Song.query.filter_by(user_id=user.id).all()

    return render_template('creator.html', user_songs=user_songs)

@app.route('/addsong', methods=['GET', 'POST'])
def addsong():
    if request.method == 'POST':
        song_name = request.form.get('song_name')
        artist_name = request.form.get('artist_name')
        lyrics = request.form.get('lyrics')
        duration = request.form.get('duration')
        release_date = request.form.get('release_date')
        song_link = request.form.get('song_link')
        album_option = request.form.get('album')

        user = User.query.filter_by(username=session.get('username')).first()

        if album_option == 'existing_album':
            existing_album_name = request.form.get('existing_album')
            album = Album.query.filter_by(album_name=existing_album_name).first()
        else:
            new_album_name = request.form.get('new_album_name')
            album = Album(album_name=new_album_name)
            db.session.add(album)
            db.session.commit()

        new_song = Song(
            song_name=song_name,
            artist_name=artist_name,
            lyrics=lyrics,
            duration=duration,
            release_date=release_date,
            song_link=song_link,
            album_name=album.album_name,
            user_id=user.id
        )

        db.session.add(new_song)
        db.session.commit()

        flash('Song added successfully!', 'success')
        return redirect(url_for('creator'))

    # For GET requests, provide a list of existing albums to the template
    albums = Album.query.all()
    return render_template('addsong_mod.html', albums=albums)

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        # Get the search query from the form
        search_query = request.form.get('search_query')

        # Query songs that match the search query
        search_results = Song.query.filter(or_(Song.song_name.ilike(f"%{search_query}%"), Song.artist_name.ilike(f"%{search_query}%"))).all()

        return render_template('search.html', search_results=search_results, search_query=search_query)

    return render_template('search.html')

@app.route('/playlists', methods=['GET', 'POST'])
def playlists():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    user = User.query.filter_by(username=username).first()

    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Handle playlist deletion
        playlist_id_to_delete = request.form.get('delete_playlist')

        if playlist_id_to_delete:
            # Get the playlist to delete
            playlist_to_delete = Playlist.query.get(playlist_id_to_delete)

            # Check if the playlist exists
            if playlist_to_delete:
                # Delete playlist from Playlist table
                db.session.delete(playlist_to_delete)
                db.session.commit()

                # Delete associated songs from PlaylistSong table
                PlaylistSong.query.filter_by(playlist_id=playlist_id_to_delete).delete()
                db.session.commit()

                flash(f'Playlist "{playlist_to_delete.playlist_name}" and associated songs deleted successfully!', 'success')
                return redirect(url_for('playlists'))
            else:
                flash('Playlist not found', 'danger')

    # Retrieve playlists for the current user
    user_playlists = Playlist.query.filter_by(user_id=user.id).all()

    return render_template('display_playlists.html', user_playlists=user_playlists)


@app.route('/playlist/<int:playlist_id>', methods=['GET'])
def playlist(playlist_id):
    # Get the playlist
    playlist = Playlist.query.get(playlist_id)

    # Check if the playlist exists
    if not playlist:
        flash('Playlist not found', 'danger')
        return redirect(url_for('playlists'))

    # Get the songs in the playlist
    playlist_songs = (
    db.session.query(Song)
    .join(PlaylistSong, Song.song_id == PlaylistSong.song_id)
    .filter(PlaylistSong.playlist_id == playlist_id)
    .all()
)

    return render_template('playlist_display.html', playlist=playlist, playlist_songs=playlist_songs)

@app.route('/create_playlist', methods=['GET', 'POST'])
def create_playlist():
    # Get the current user
    username = session.get('username')
    user = User.query.filter_by(username=username).first()

    if request.method == 'POST' and user:
        playlist_name = request.form.get('playlistName')

        # Check if the playlist with the same name already exists for the user
        existing_playlist = Playlist.query.filter_by(playlist_name=playlist_name, user_id=user.id).first()
        print(existing_playlist)

        if not existing_playlist:
            # Create a new playlist and add it to the database
            new_playlist = Playlist(playlist_name=playlist_name, user_id=user.id)
            db.session.add(new_playlist)
            db.session.commit()
            flash(f'Playlist "{playlist_name}" created successfully!', 'success')
        else:
            flash(f'Playlist "{playlist_name}" already exists!', 'danger')

        return redirect(url_for('playlists'))
    
    all_songs = Song.query.all()

    # Retrieve all playlists for the dropdown
    all_playlists = Playlist.query.filter_by(user_id=user.id).all()

    return render_template('create_playlist.html',all_songs=all_songs, all_playlists=all_playlists)
@app.route('/add_songs_to_playlist', methods=['POST'])
def add_songs_to_playlist():
    playlist_id = request.form.get('playlistSelect')
    selected_song_ids = request.form.getlist('songSelect')

    # Get the playlist
    playlist = Playlist.query.get(playlist_id)

    if playlist:
        # Add the selected songs to the playlist
        for song_id in selected_song_ids:
            playlist_song = PlaylistSong(playlist_id=playlist.playlist_id, song_id=song_id)
            db.session.add(playlist_song)

        db.session.commit()
        flash(f'Songs added to playlist "{playlist.playlist_name}" successfully!', 'success')
        return redirect(url_for('playlists'))

    return redirect(url_for('create_playlist'))

@app.route('/adminlogin', methods=['GET', 'POST'])
def adminlogin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Admin.query.filter_by(username=username).first()

        if admin and check_password_hash(admin.password,password):
            session['admin_username'] = admin.username
            return redirect(url_for('admindashboard'))
        else:
            flash('Invalid admin username or password', 'danger')

    return render_template('adminlogin.html')

@app.route('/admindashboard')
def admindashboard():
    # Check if the user is logged in as an admin
    admin_username = session.get('admin_username')
    if not admin_username:
        return redirect(url_for('adminlogin'))

    # Query the database for statistics
    total_users = User.query.count()
    total_songs = Song.query.count()
    total_creators = db.session.query(func.count(distinct(Song.user_id))).scalar()
    total_albums = Album.query.count()

    # Render the admin dashboard template with the obtained statistics
    return render_template('dashboard.html',
                           admin_username=admin_username,
                           total_users=total_users,
                           total_songs=total_songs,
                           total_creators=total_creators,
                           total_albums=total_albums)

@app.route('/songs', methods=['GET', 'POST'])
def songs():
    if request.method == 'POST':
        # Handle song deletion
        song_id_to_delete = request.form.get('delete_song')

        if song_id_to_delete:
            # Get the song to delete
            song_to_delete = Song.query.get(song_id_to_delete)

            # Get the album of the song
            album_of_song = Album.query.filter_by(album_name=song_to_delete.album_name).first()

            # Delete the song
            db.session.delete(song_to_delete)
            db.session.commit()

            # Check if there are any remaining songs from the same album
            remaining_songs_in_album = Song.query.filter_by(album_name=album_of_song.album_name).count()

            # If no remaining songs, delete the album
            if remaining_songs_in_album == 0:
                db.session.delete(album_of_song)
                db.session.commit()

    all_songs = Song.query.all()
    return render_template('songs.html', all_songs=all_songs)


@app.route('/editsong', methods=['GET', 'POST'])
def editsong():
    if request.method == 'POST':
        song_id = request.form.get('song_id')
        field_to_change = request.form.get('field_to_change')
        new_value = request.form.get('new_value')

        song = Song.query.get(song_id)

        if song:
            # Update the chosen field with the new value
            if field_to_change == 'song_name':
                song.song_name = new_value
            elif field_to_change == 'artist_name':
                song.artist_name = new_value
            elif field_to_change == 'lyrics':
                song.lyrics = new_value
            elif field_to_change == 'duration':
                song.duration = new_value
            elif field_to_change == 'release_date':
                song.release_date = new_value
            elif field_to_change == 'song_link':
                song.song_link = new_value
            # Add other conditions as needed

            db.session.commit()

    # Fetch all songs to display in the dropdown
    all_songs = Song.query.all()

    return render_template('editsong_mod.html', all_songs=all_songs)

@app.route('/creators')
def creators():
    # Query the database to get creators (users associated with songs)
    creators = (
        db.session.query(User)
        .join(Song, User.id == Song.user_id)
        .distinct(User.id)
        .all()
    )

    return render_template('creators.html', all_creators=creators)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables before running the app
    app.run(debug=True)
