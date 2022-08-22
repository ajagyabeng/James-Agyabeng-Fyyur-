#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import sys
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import config
from models import db, Venue, Artist, Show
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ---------------------------------------------------------------


@app.route('/venues')
def venues():

    all_location = Venue.query.with_entities(
        Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
    result = []

    for location in all_location:
        venues_in_location = Venue.query.filter_by(
            state=location.state).filter_by(city=location.city).all()
        venue_data = []
        for venue in venues_in_location:
            venue_data.append({
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": len(Show.query.filter(Show.venue_id == 1).filter(Show.start_time > datetime.now()).all())
            })
        result.append(({
            "city": location.city,
            "state": location.state,
            "venues": venue_data
        }))
    # db_city_and_states = db.session.query(
    #     Venue.city, Venue.state).distinct().all()
    # db_venues = db.session.query(
    #     Venue.id, Venue.city, Venue.state, Venue.name).all()

    # result = []

    # for city, state in db_city_and_states:
    #     data = {
    #         "city": city,
    #         "state": state,
    #         "venues": []
    #     }

    #     for name, id, cty, st in db_venues:
    #         if cty == city and st == state:
    #             data["venues"].append({
    #                 "name": name,
    #                 "id": id,
    #                 "num_upcoming_shows": db.session.query(Show).join(Venue).filter(Show.venue_id == id, Show.start_time > datetime.now()).count()
    #             })
    # result.append(data)
    return render_template('pages/venues.html', areas=result)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    keyword = request.form.get('search_term')
    keyword_search_results = Venue.query.filter(
        Venue.name.ilike(f"%{keyword}%"))
    data = []
    for item in keyword_search_results:
        data.append({
            "id": item.id,
            "name": item.name,
            "num_upcoming_shows": len(Show.query.filter(Show.venue_id == item.id).filter(Show.start_time > datetime.now()).all())
        })

    response = {
        "count": len(keyword_search_results),
        "data": data
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue_to_show = Venue.query.get(venue_id)

    if not venue_to_show:
        return render_template("errors/404.html")

    upcoming_shows = db.session.query(Show).join(Venue).filter(
        Show.start_time > datetime.now(), venue_id == Show.venue_id).all()
    upcoming_shows_list = []

    for show in upcoming_shows:
        upcoming_shows_list.append({
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "venue_image_link": show.venue.image_link,
            "start_time": str(show.start_time)
        })

    past_shows = db.session.query(Show).join(Venue).filter(
        Show.start_time < datetime.now(), venue_id == Show.venue_id).all()
    past_shows_list = []

    for show in past_shows:
        past_shows_list.append({
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "venue_image_link": show.venue.image_link,
            "start_time": str(show.start_time)
        })

    data = {
        "id": venue_to_show.id,
        "name": venue_to_show.name,
        "genres": venue_to_show.genres,
        "city": venue_to_show.city,
        "state": venue_to_show.state,
        "address": venue_to_show.address,
        "phone": venue_to_show.phone,
        "website": venue_to_show.website_link,
        "facebook_link": venue_to_show.facebook_link,
        "seeking_talent": venue_to_show.seeking_talent,
        "seeking_description": venue_to_show.seeking_talent,
        "image_link": venue_to_show.image_link,
        "upcoming_shows_count": len(upcoming_shows),
        "past_shows_count": len(past_shows),
        "upcoming_shows": upcoming_shows_list,
        "past_shows": past_shows_list,
    }
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    venue_form = VenueForm(request.form)
    if venue_form.validate():
        try:
            new_venue = Venue(
                name=venue_form.name.data,
                city=venue_form.city.data,
                state=venue_form.state.data,
                address=venue_form.address.data,
                phone=venue_form.phone.data,
                image_link=venue_form.image_link.data,
                facebook_link=venue_form.facebook_link.data,
                genres=venue_form.genres.data,
                website_link=venue_form.website_link.data,
                seeking_talent=venue_form.seeking_talent.data,
                seeking_description=venue_form.seeking_description.data
            )
            # print(new_venue.seeking_talent)
            db.session.add(new_venue)
            db.session.commit()
            flash(f"Venue {request.form['name']} was successfully listed!")
        except:
            db.session.rollback()
            flash(
                f"An error occurred. Venue {request.form['name']} could not be listed.")
            return render_template("forms/new_venue.html", form=venue_form)
        finally:
            db.session.close()
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    venue_to_delete = Venue.query.get(venue_id)
    if venue_to_delete is None:
        return render_template("pages/404.html")

    try:
        flash(f"Venue {venue_to_delete.name} was deleted successfully!")
        db.session.delete(venue_to_delete)
        db.session.commit()
    except:
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    return jsonify({"success": True})

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    data = Artist.query.order_by('id').all()
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    keyword = request.form.get('search_term')
    keyword_search_results = Artist.query.filter(
        Artist.name.ilike(f"%{keyword}%"))
    data = []
    for item in keyword_search_results:
        data.append({
            "id": item.id,
            "name": item.name,
            "num_upcoming_shows": len(Show.query.filter(Show.artist_id == item.id).filter(Show.start_time > datetime.now()).all())
        })

    response = {
        "count": len(keyword_search_results),
        "data": data
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    artist_to_show = Artist.query.get(artist_id)
    if not artist_to_show:
        return render_template("errors/404.html")

    past_shows = Show.query.join(Artist).filter(
        Show.artist_id == artist_id).filter(Show.start_time > datetime.now()).all()
    past_shows_list = []

    for show in past_shows:
        past_shows_list.append({
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": str(show.start_time)
        })

    upcoming_shows = Show.query.join(Artist).filter(
        Show.artist_id == artist_id).filter(Show.start_time > datetime.now()).all()
    upcoming_shows_list = []

    for show in upcoming_shows:
        upcoming_shows_list.append({
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": str(show.start_time)
        })

    data = {
        "id": artist_to_show.id,
        "name": artist_to_show.name,
        "genres": artist_to_show.genres,
        "city": artist_to_show.city,
        "state": artist_to_show.state,
        "phone": artist_to_show.phone,
        "website": artist_to_show.website_link,
        "facebook_link": artist_to_show.facebook_link,
        "seeking_venue": artist_to_show.seeking_venue,
        "seeking_description": artist_to_show.seeking_description,
        "image_link": artist_to_show.image_link,
        "upcoming_shows_count": len(upcoming_shows),
        "past_shows_count": len(past_shows),
        "upcoming_shows": upcoming_shows_list,
        "past_shows": past_shows_list,
    }

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id)

    if artist is None:
        return render_template("errors/404.html")

    form = ArtistForm(
        name=artist.name,
        city=artist.city,
        state=artist.state,
        phone=artist.phone,
        image_link=artist.image_link,
        facebook_link=artist.facebook_link,
        website_link=artist.website_link,
        seeking_venue=artist.seeking_venue,
        seeking_description=artist.seeking_description,
        genres=artist.genres
    )

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    artist_edit_form = ArtistForm(request.form)
    artist = Artist.query.get(artist_id)
    if not artist:
        return render_template("errors/404.html")

    try:
        artist.name = artist_edit_form.name.data
        artist.genres = artist_edit_form.genres.data
        artist.phone = artist_edit_form.phone.data
        artist.facebook_link = artist_edit_form.facebook_link.data
        artist.image_link = artist_edit_form.image_link.data
        artist.city = artist_edit_form.city.data
        artist.state = artist_edit_form.state.data
        artist.website_link = artist_edit_form.website_link.data
        artist.seeking_venue = artist_edit_form.seeking_venue.data
        artist.seeking_description = artist_edit_form.seeking_description.data

        db.session.commit()
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash("Artist info update unsuccessful")
    finally:
        db.session.close()

    flash(f"Successfully updated Artist '{artist_edit_form.name.data}'")
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.get(venue_id)

    form = VenueForm(
        name=venue.name,
        genres=venue.genres,
        city=venue.city,
        state=venue.state,
        phone=venue.phone,
        website_link=venue.website_link,
        facebook_link=venue.facebook_link,
        seeking_talent=venue.seeking_talent,
        address=venue.address
    )
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    venue_edit_form = VenueForm(request.form)
    venue = Venue.query.get(venue_id)
    if not venue:
        return render_template("errors/404.html")

    try:
        venue.name = venue_edit_form.name.data
        venue.genres = venue_edit_form.genres.data
        venue.phone = venue_edit_form.phone.data
        venue.facebook_link = venue_edit_form.facebook_link.data
        venue.image_link = venue_edit_form.image_link.data
        venue.city = venue_edit_form.city.data
        venue.state = venue_edit_form.state.data
        venue.website_link = venue_edit_form.website_link.data
        venue.seeking_talent = venue_edit_form.seeking_talent.data
        venue.seeking_description = venue_edit_form.seeking_description.data

        db.session.commit()
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash("Venue info update unsuccessful")
    finally:
        db.session.close()

    flash(f"Successfully updated Venue '{venue_edit_form.name.data}'")
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    artists_form = ArtistForm(request.form)
    if artists_form.validate():
        try:
            new_artist = Artist(
                name=artists_form.name.data,
                city=artists_form.city.data,
                state=artists_form.state.data,
                phone=artists_form.phone.data,
                image_link=artists_form.image_link.data,
                facebook_link=artists_form.facebook_link.data,
                genres=artists_form.genres.data,
                website_link=artists_form.website_link.data,
                seeking_venue=artists_form.seeking_venue.data,
                seeking_description=artists_form.seeking_description.data
            )
            print(new_artist.name)
            db.session.add(new_artist)
            db.session.commit()
            flash(f"Artist {request.form['name']} was successfully listed!")
        except:
            db.session.rollback()
            print(sys.exc_info())
            flash(
                f"An error occurred. Artist {request.form['name']} could not be listed.")
            return render_template("forms/new_artist.html", form=artists_form)
        finally:
            db.session.close()
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    response = Show.query.all()
    if not response:
        return render_template("errors/404.html")
    data = []

    for show in response:
        data.append({
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.imgae_link,
            "artist_id": show.artist_id,
            "venue_name": show.venue.name,
            "vaenue_id": show.venue_id
        })

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    new_show = Show(request.form)
    if new_show.validate():
        artist_id = new_show.artist_id.data,
        venue_id = new_show.venue_id.data,
        show_start_time = new_show.start_time.data

        try:
            new_show = Show(
                artist=Artist.query.get(artist_id),
                venue=Venue.query.get(venue_id),
                start_time=show_start_time
            )

            db.session.add(new_show)
            db.session.commit()
        except:
            db.session.rollback()
            flash("Wrong Venue/Artist ID")
            print(sys.exc_info())
        finally:
            db.session.close()
    flash('Show was successfully listed!')
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
