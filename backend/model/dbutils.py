from . import model

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

import datetime as dt
import re

from ..scraping_wr import utils_wr

# logging stuff
import logging
logger = logging.getLogger(__name__)

# session / connection str
engine = create_engine("postgresql+psycopg2://postgres:postgres@localhost:5432/rowing", echo=True)
Session = sessionmaker(bind=engine)


def get_(data, key, default=None):
    if data == None:
        return default
    
    if not isinstance(data, dict):
        raise ValueError("data Parameter is not dict type")
    
    return data.get(key, default)


def parse_timedelta_(delta_str):
    """returns int in milliseconds
    
    Input format examples:
    '00:01:53.920'
    '00:07:59.75'
    """
    regex = re.compile( r"^(\d+):(\d+):(\d+)\.(\d+)$" )
    result = regex.match(delta_str)

    if result == None:
        raise ValueError("Timedelta string does not match the format 'HH:MM:SS.mmm'")
    
    hours, minutes, seconds, milliseconds = result.group(1,2,3,4)

    SECOND_IN_MILLIS = 1000
    MINUTE_IN_MILLIS = 60 * SECOND_IN_MILLIS
    HOUR_IN_MILLIS   = 60 * MINUTE_IN_MILLIS

    return int(hours)*HOUR_IN_MILLIS + int(minutes)*MINUTE_IN_MILLIS + int(seconds)*SECOND_IN_MILLIS + int(milliseconds)


def create_tables():
    # create all tables (init) if they don't exist
    model.Base.metadata.create_all(engine, checkfirst=True)

    # session = Session()
    # session.commit()


def drop_all_tables():
    model.Base.metadata.drop_all(engine)


def query_by_uuid_(session, Entity_Class, uuid):
    """Helper function.
    If an entity with given uuid exists:
        returns ORM object linked to db
    If not existing:
        returns None
    """
    statement = select(Entity_Class).where(Entity_Class.additional_id_ == uuid.lower())
    result_list = session.execute(statement).first()

    if result_list:
        return result_list[0]
    
    return None


def wr_insert(session, Entity_Class, map_func, data):
    """Proxy function to fetch or create an entity.
    Usage: wr_insert(session, model.Country, wr_map_country, data_dict)"""
    if data == None:
        return None

    uuid = data['id'].lower()
    entity = query_by_uuid_(session, Entity_Class, uuid)
    create_entity = entity == None

    if create_entity:
        entity = Entity_Class()
        entity.additional_id_ = uuid

    map_func(session, entity, data)

    if create_entity:
        session.add(entity)

    return entity


def wr_map_country(session, entity, data):
    entity.country_code = get_(data, 'CountryCode')
    entity.name = get_(data, 'DisplayName')

    entity.is_former_country__ = repr(get_(data, 'IsFormerCountry'))
    entity.is_noc__ = repr(get_(data, 'IsNOC'))


def wr_map_boat_class(session, entity, data):
    entity.abbreviation = get_(data, 'DisplayName')
    # TODO: entity.name // full name not in API data


def wr_map_gender(session, entity, data):
    entity.name = get_(data, 'DisplayName')


def wr_map_athlete(session, entity, data):
    pass

def wr_map_race_boat(session, entity, data):
    entity.country = wr_insert(session, model.Country, wr_map_country, data['country'])
    
    # Athletes # TODO: Fix raceBoatAthlete.get('person', {}) => None
    for raceBoatAthlete in get_(data, 'raceBoatAthletes', []):
        athlete_data = get_(raceBoatAthlete, 'person', {})
        if athlete_data:
            association = model.Association_Race_Boat_Athlete(boat_position=get_(raceBoatAthlete,'boatPosition'))
            association.athlete = wr_insert(session, model.Athlete, wr_map_athlete, athlete_data)
            session.add(association)
            
            entity.athletes.append(association)

    entity.name = get_(data, 'DisplayName') # e.g. "GER2" for the second German boat
    entity.result_time_ms = parse_timedelta_( get_(data, 'ResultTime') ) if get_(data, 'ResultTime') else None
    
    entity.lane = get_(data, 'Lane')
    entity.rank = get_(data, 'Rank')
    entity.final_rank = get_( get_(data, 'boat', {}), 'finalRank' ) #  TODO use chained get_()
    entity.final_rank_index__ = repr( get_ (get_(data, 'boat', {}), 'finalRankIndex' ) ) #  TODO use chained get_()
    
    entity.remark__ = repr( get_(data, 'Remark') )
    entity.world_cup_points__ = get_(data, 'WorldCupPoints')
    entity.club_name__ = get_( get_(data, 'boat', {}), 'clubName' )

    # TODO: Race Data

def wr_map_race(session, entity, data):
    entity.name = get_(data, 'DisplayName')
    entity.date = dt.datetime.fromisoformat(data['Date'])
    entity.phase_type = get_( get_(data, 'racePhase', {}), 'DisplayName','' ).lower() #  TODO use chained get_()
    entity.phase = get_(data, 'FB') # !!! TODO: Extract from RSC Code !!!
    entity.progression = get_(data, 'Progression')
    entity.rsc_code = get_(data, 'RscCode')

    # TODO: PDF URLs from pdf parser output?
    entity.pdf_url_results = "https://dummy.url/race_results.pdf"
    entity.pdf_url_race_data = "https://dummy.url/race_data.pdf"

    entity.race_nr__ = repr( get_(data, 'RaceNr') )
    entity.rescheduled__ = repr( get_(data, 'Rescheduled') )
    entity.rescheduled_from__ = repr( get_(data, 'RescheduledFrom') )
    entity.race_status__ = repr( get_( get_(data, 'raceStatus', {} ), 'DisplayName' ) )

    # Race Boats
    race_boats = map(
        lambda d : wr_insert(session, model.Race_Boat, wr_map_race_boat, d),
        get_(data, 'raceBoats', [])
    )
    entity.race_boats.extend(race_boats)


def wr_map_event(session, entity, data):
    entity.name = get_(data, 'DisplayName')
    entity.boat_class = wr_insert(session, model.Boat_Class, wr_map_boat_class, data['boatClass'])
    entity.gender = wr_insert(session, model.Gender, wr_map_gender, data['gender'])
    entity.rsc_code__ = get_(data, 'RscCode')

    # Races
    races = map(
        lambda d : wr_insert(session, model.Race, wr_map_race, d),
        get_(data, 'races', [])
    )
    entity.races.extend(races)


def wr_map_competition_category(session, entity, data):
    entity.name = get_(data, 'DisplayName')


def wr_map_venue(session, entity, data):
    entity.country = wr_insert(session, model.Country, wr_map_country, data['country'])
    entity.city = get_(data, 'RegionCity')
    entity.site = get_(data, 'Site')
    entity.is_world_rowing_venue = get_(data, 'IsWorldRowingVenue')


def wr_map_competition(session, entity, data):
    # Competition_Category
    competition_category = wr_insert(
        session,
        model.Competition_Category,
        wr_map_competition_category,
        data['competitionType']['competitionCategory']
    )

    # Venue
    venue = wr_insert(session, model.Venue, wr_map_venue, data['venue'])

    entity.competition_category = competition_category
    entity.venue = venue
    entity.name = get_(data, 'DisplayName')
    entity.start_date = dt.datetime.fromisoformat(data['StartDate'])
    entity.end_date = dt.datetime.fromisoformat(data['EndDate'])

    entity.competition_code__ = get_(data, 'CompetitionCode')
    entity.is_fisa__ = get_(data, 'IsFisa')

    # Events
    # Insert 1:m https://stackoverflow.com/q/16433338
    events = map(
        lambda d : wr_insert(session, model.Event, wr_map_event, d),
        get_(competition_data, 'events', [])
    )
    entity.events.extend(events)


def wr_insert_competition(competition_data):
    session = Session()

    wr_insert(session, model.Competition, wr_map_competition, competition_data)

    session.commit()
    pass



if __name__ == '__main__':
    import argparse
    from sys import exit as sysexit
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--create", help="Create tables if not yet existing", action="store_true")
    parser.add_argument("-d", "--drop", help="Drop all tables described by the schema defined in model.py", action="store_true")
    parser.add_argument("-i", "--insert", help="Import JSON data for a rowing competition")
    args = parser.parse_args()
    print(args)

    if args.insert:
        print("Load JSON file:", args.insert)
        with open(args.insert, mode="r", encoding="utf-8") as fp:
            competition_data = json.load(fp)

        wr_insert_competition(competition_data)
        sysexit()

    if args.drop:
        print("----- Drop All Tables -----")
        drop_all_tables()

    if args.create:
        print("----- Create Tables -----")
        create_tables()