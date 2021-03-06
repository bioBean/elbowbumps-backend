from flask import Flask, request, jsonify
from flask.wrappers import Response
from elbowbumps.twitter_scraper import getTweets
from elbowbumps.twitter_id_lookup import twitterID
from flask_cors import CORS, cross_origin
from elbowbumps import create_app, db
from json import loads
from twython import Twython
import json

app = create_app()
cors = CORS(app)
from elbowbumps.models import UserData, UserInterestData, UserMatch, ReportUser, SquaredWeights

from elbowbumps.auth import auth

app.register_blueprint(auth)


# Updates interests for a given user
@app.route('/update_interests', methods=['POST'])
def update_interests():
    param = request.args.get('user_id', None)
    print(param)
    response = {}

    # TODO: check if user exists in database

    if (param):
        response["STATUS_CODE"] = 200
        response["MESSAGE"] = f"User {param} has been updated"
    else:
        response["STATUS_CODE"] = 500
        response["MESSAGE"] = "Please provide a user id"
    return jsonify(response)

# Adds row for interest data


@app.route('/add_interest_score', methods=['POST'])
def add_interest_score():
    param = request.args.get('user_id')
    interest = UserInterestData(1, 'Basketball', 0, 0.5)
    interest2 = UserInterestData(3, 'Basketball', 0, 0.3)
    interest3 = UserInterestData(4, 'Basketball', 0, 0.4)
    db.session.add(interest)
    db.session.add(interest2)
    db.session.add(interest3)
    db.session.commit()
    return jsonify({
        'STATUS_CODE': 200,
        'MESSAGE': 'row added successfully'
    })

@app.route('/match_info', methods=['POST'])
@cross_origin()
def match_info():
    matches = loads(request.form.get('matches'))
    print(matches)
    match_info = []
    for match in matches:
        print(match)
        user = UserData.query.filter_by(ud_id=match['uid_ud_id']).first()
        if user:
            match_info.append(user.serialise())
    return jsonify({
        "STATUS_CODE": 200,
        'match_info': match_info
    })

@app.route('/bump', methods=['POST'])
@cross_origin()
def bump():
    user_id = request.form.get('userId')
    match_id = request.form.get('matchId')
    m1 = UserMatch.query.filter(UserMatch.um_ud_id_1==user_id).filter(UserMatch.um_ud_id_2==match_id).first()
    m2 = UserMatch.query.filter(UserMatch.um_ud_id_2==user_id).filter(UserMatch.um_ud_id_1==match_id).first()
    if m1:
        m1.um_1_matched = True
        db.session.commit()
        return jsonify({"STATUS_CODE": 200})
    else:
        m2.um_2_matched = True
        db.session.commit()
        return jsonify({"STATUS_CODE": 200})

@app.route('/unbump', methods=['POST'])
@cross_origin()
def unbump():
    user_id = request.form.get('userId')
    match_id = request.form.get('matchId')
    m1 = UserMatch.query.filter(UserMatch.um_ud_id_1==user_id).filter(UserMatch.um_ud_id_2==match_id).first()
    m2 = UserMatch.query.filter(UserMatch.um_ud_id_2==user_id).filter(UserMatch.um_ud_id_1==match_id).first()
    if m1:
        m1.um_1_matched = False
        db.session.commit()
        return jsonify({"STATUS_CODE": 200})
    else:
        m2.um_2_matched = False
        db.session.commit()
        return jsonify({"STATUS_CODE": 200})

@app.route('/blockUser', methods=['POST'])
@cross_origin()
def blockUser():
    user_id = request.form.get('userId')
    match_id = request.form.get('matchId')
    print(user_id)
    print(match_id)
    m1 = UserMatch.query.filter(UserMatch.um_ud_id_1==user_id).filter(UserMatch.um_ud_id_2==match_id).first()
    m2 = UserMatch.query.filter(UserMatch.um_ud_id_2==user_id).filter(UserMatch.um_ud_id_1==match_id).first()
    if m1:
        m1.um_blocked = True
        db.session.commit()
        return jsonify({"STATUS_CODE": 200})
    else:
        m2.um_blocked = True
        db.session.commit()
        return jsonify({"STATUS_CODE": 200})

@app.route('/bumped_by', methods=['GET'])
@cross_origin()
def bumped_by():
    user_id = request.args.get('userID')
    usr = UserData.query.filter_by(ud_id=user_id).first()
    if not usr:
        return jsonify({
            'STATUS': 'USER_NOT_EXISTS',
            'STATUS_CODE': 500,
            'DATA': {}
        })
    matches1 = UserMatch.query.filter((UserMatch.um_ud_id_1 == user_id) & (UserMatch.um_1_matched == False) & (UserMatch.um_2_matched == True))
    matches2 = UserMatch.query.filter((UserMatch.um_ud_id_2 == user_id) & (UserMatch.um_1_matched == True) & (UserMatch.um_2_matched == False))
    match_ids = []
    for m in matches1:
        match_ids.append(m.um_ud_id_2)
    for m in matches2:
        match_ids.append(m.um_ud_id_1)
    return jsonify({
        'STATUS': 'OK',
        'STATUS_CODE': 200,
        'DATA': {'users': match_ids}
    })

@app.route('/bumped_with', methods=['GET'])
@cross_origin()
def bumped_with():
    user_id = request.args.get('userID')
    usr = UserData.query.filter_by(ud_id=user_id).first()
    if not usr:
        return jsonify({
            'STATUS': 'USER_NOT_EXISTS',
            'STATUS_CODE': 500,
            'DATA': {}
        })
    matches1 = UserMatch.query.filter((UserMatch.um_ud_id_1 == user_id) & (UserMatch.um_1_matched == True) & (UserMatch.um_2_matched == False))
    matches2 = UserMatch.query.filter((UserMatch.um_ud_id_2 == user_id) & (UserMatch.um_1_matched == False) & (UserMatch.um_2_matched == True))
    match_ids = []
    for m in matches1:
        match_ids.append(m.um_ud_id_2)
    for m in matches2:
        match_ids.append(m.um_ud_id_1)
    return jsonify({
        'STATUS': 'OK',
        'STATUS_CODE': 200,
        'DATA': {'users': match_ids}
    })

@app.route('/get_bumps', methods=['GET'])
@cross_origin()
def get_bumps():
    user_id = int(request.args.get('user_id'))
    matches = UserMatch.query.filter((UserMatch.um_ud_id_1 == user_id) | (UserMatch.um_ud_id_2 == user_id)).filter(UserMatch.um_1_matched == True).filter(UserMatch.um_2_matched == True).all()
    match_ids = []
    for m in matches:
        if (m.um_ud_id_1 == int(user_id)):
            match_ids.append(m.um_ud_id_2)
        else:
            match_ids.append(m.um_ud_id_1)
    print(match_ids)
    return jsonify({
        'matches': match_ids
    })

@app.route('/get_interest_data', methods=['GET'])
@cross_origin()
def get_interest_data():
    user_id = request.args.get('user_id')
    query = f'SELECT uid_interest_type, uid_interest_weight FROM user_interest_data WHERE user_interest_data.uid_ud_id = \'{user_id}\';'
    results = db.engine.execute(query)
    response = []
    for res in results:
        response.append(dict(res))
    print(user_id)
    print(response)
    return jsonify({
        "STATUS_CODE": 200,
        "Message": f"userID {user_id} interest data.",
        "Data": json.dumps(response)
    })

@app.route('/get_interests', methods=['GET'])
@cross_origin()
def get_interests():
    user_id = request.args.get('user_id')
    query = f'SELECT uid_interest_type, uid_interest_weight FROM user_interest_data WHERE user_interest_data.uid_ud_id = \'{user_id}\';'
    results = db.engine.execute(query)
    print("results = ", results)
    results = sorted(results, reverse = True)
    print("sorted results = ", results)
    response = []
    sorted_results = []
    # for res in results:
    #     if res.uid_interest_weight > 1:
    #         response.append(res.uid_interest_type)
        # response.append(dict(res))
    for res in results:
        if res.uid_interest_weight > 1:
            sorted_results.append(res.uid_interest_weight)
    sorted_results = sorted(sorted_results, reverse = True)
    print("sorted results = ", sorted_results)
    for x in range(len(sorted_results)):
        for res in results:
            if sorted_results[x] == res.uid_interest_weight and res.uid_interest_type not in response:
                response.append(res.uid_interest_type)
    print(user_id)
    print(response)
    return jsonify({
        "STATUS_CODE": 200,
        "Message": f"userID {user_id} interest data.",
        "Data": response
    })

@app.route('/get_all_interests', methods=['GET'])
@cross_origin()
def get_all_interests():
    user_id = request.args.get('user_id')
    query = f'SELECT uid_interest_type as cat, uid_interest_weight * 50 as weight FROM user_interest_data WHERE user_interest_data.uid_ud_id = \'{user_id}\';'
    results = db.engine.execute(query)
    response = []
    for res in results:
        response.append(dict(res))
    query2 = f'SELECT uid_interest_type as cat, uid_twitter_score * 50 as weight FROM user_interest_data WHERE user_interest_data.uid_ud_id = \'{user_id}\';'
    results2 = db.engine.execute(query2)
    twitter_results = []
    for res in results2:
        twitter_results.append(dict(res))
    query3 = f'SELECT uid_interest_type as cat, uid_twitter_score * 50 as twitter, uid_questionnaire_score * 50 as questionnaire, uid_interest_weight * 50 as weight FROM user_interest_data WHERE user_interest_data.uid_ud_id = {user_id}'
    results3 = db.engine.execute(query3)
    overall_results = []
    for res in results3:
        overall_results.append(dict(res))
    print(overall_results)
    return jsonify({
        "STATUS_CODE": 200,
        "Message": f"userID {user_id} interest data.",
        "Data": {'overall': response, 'twitter': twitter_results, 'all': overall_results}
    })

@app.route('/questionnaire', methods=['POST'])
@cross_origin()
def add_questionnaire_scores():
    user_id = int(request.form.get('user_id'))
    scores = request.form

    for cat in scores:

        if cat == 'user_id':
            continue

        # will end up being a list, probably, when we have multiple scores instrad of one
        score = scores[cat]
        normalisedScore = float(score) * 2
        user_interests = UserInterestData.query.filter_by(uid_ud_id=user_id, uid_interest_type=cat).first()
        if user_interests:
            user_interests.uid_questionnaire_score = normalisedScore
            user_interests.updateScores()
            db.session.commit()
        else:
            data = UserInterestData(user_id, cat, 0, normalisedScore)
            db.session.add(data)
            db.session.commit()
            user_interests = UserInterestData.query.filter_by(uid_ud_id=user_id, uid_interest_type=cat).first()
            user_interests.updateScores()

    return jsonify({
        "STATUS_CODE": 200,
        "Message": f"Updated userID {user_id} interest data."
    })

@app.route('/twitter_oauth_url', methods=['POST'])
def oauth_twitter():
    # need these in the server environment variables
    APP_KEY = '2pHz1BZBRluCVPALHah1rF92o'
    APP_SECRET = 'xY7W7TfQpnovvYcL4g71hzYGj27sT3BgogKXGIWAn1OHntDjBL'
    twitter = Twython(APP_KEY, APP_SECRET)
    try:
        auth = twitter.get_authentication_tokens(callback_url='oob')
        OAUTH_TOKEN = auth['oauth_token']
        OAUTH_TOKEN_SECRET = auth['oauth_token_secret']
        return jsonify({
                "STATUS_CODE": 200,
                "oauthURL": auth['auth_url'],
                "oauthToken": OAUTH_TOKEN,
                "oauthTokenSecret": OAUTH_TOKEN_SECRET
            })
    except:
        return jsonify({
                "STATUS_CODE": 500,
                "Message": "Couldn't generate the Twitter URL"
            })

@app.route('/social_media_info', methods=['POST'])
def callback_twitter():
    APP_KEY = '2pHz1BZBRluCVPALHah1rF92o'
    APP_SECRET = 'xY7W7TfQpnovvYcL4g71hzYGj27sT3BgogKXGIWAn1OHntDjBL'
    oauth_verifier = request.form.get('pin')
    id = request.form.get('id')
    OAUTH_TOKEN = request.form.get('OAUTH_TOKEN')
    OAUTH_TOKEN_SECRET = request.form.get('OAUTH_TOKEN_SECRET')
    try:
        twitter = Twython(APP_KEY, APP_SECRET,
                        OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
        response = twitter.get_authorized_tokens(oauth_verifier)
    except:
        return jsonify({
            "STATUS_CODE": "500",
            "Message": "That wasn't the correct pin"
        })

    return add_twitter_db(id, response['user_id'], response['screen_name'])

@app.route('/refresh_twitter_score', methods=['POST'])
def refresh_twitter_score():
    id = request.form.get('id')
    return get_tweets(id)

def add_twitter_db(id, twitter_id, twitter_name):
    user = UserData.query.filter_by(ud_id = id).first()
    if not user:
        return jsonify({
            "STATUS_CODE": "500",
            "Message": "Please ensure the user exists!"
        })
    else:
        query = f'SELECT * FROM user_data WHERE ud_twitter = \'{twitter_name}\';'
        results = db.engine.execute(query)
        if results.rowcount == 0:
            user.ud_twitter = twitter_name
            user.ud_id_twitter = twitter_id
            db.session.commit()
            response = get_tweets(user.ud_id)
            return response
        else:
            for res in results:
                print(res)
                if res[0] == int(id):
                    return get_tweets(id)
            return jsonify ({
            "STATUS_CODE": "500",
            "Message": "Please provide a unique twitter username"
            })

def get_tweets(user_id):
    user = UserData.query.filter_by(ud_id=user_id).first()

    if not user:
        return jsonify({
            "STATUS_CODE": "500",
            "Message": "Please ensure the user exists!"
            })
    elif user.ud_twitter == "":
        return jsonify({
            "STATUS_CODE": "500",
            "Message": "Please ensure the user has a social media account registered"
            })
    else:
        scores = getTweets(user.ud_id_twitter)
        for name, score in scores.items():
            score = score + 1
            user_interests = UserInterestData.query.filter_by(uid_ud_id=user_id, uid_interest_type=name).first()
            if user_interests:
                user_interests.uid_twitter_score = score
                user_interests.updateScores()
                db.session.commit()
            else:
                data = UserInterestData(user_id, name, score, 0)
                db.session.add(data)
                db.session.commit()

        return jsonify({
            'STATUS_CODE': '200',
            "Message": f"Updated scores for "
        })
    return jsonify({
        'STATUS_CODE': '500',
        "Message": f"Hmm error"
            })
    

@app.route('/pending_bumps', methods=['GET'])
def pending_bumps():
    userID_1 = request.args.get('userID_1')
    userID_2 = request.args.get('userID_2')

    matches_1 = UserMatch.query.filter((UserMatch.um_ud_id_1 == userID_1) & (UserMatch.um_ud_id_2 == userID_2)).filter(UserMatch.um_1_matched == True).filter(UserMatch.um_2_matched == False).all()
    matches_2 = UserMatch.query.filter((UserMatch.um_ud_id_1 == userID_2) & (UserMatch.um_ud_id_2 == userID_1)).filter(UserMatch.um_2_matched == True).filter(UserMatch.um_1_matched == False).all()

    pending = False
    print(matches_1)
    if len(matches_1) == 1:
        pending = True
    elif len(matches_2) == 1:
        pending = True

    return jsonify({
        'STATUS_CODE': '200',
        'result': pending
    })

@app.route('/full_bumps', methods=['GET'])
def full_bumps():
    userID_1 = request.args.get('userID_1')
    userID_2 = request.args.get('userID_2')

    matches_1 = UserMatch.query.filter((UserMatch.um_ud_id_1 == userID_1) & (UserMatch.um_ud_id_2 == userID_2)).filter(UserMatch.um_1_matched == True).filter(UserMatch.um_2_matched == True).all()
    matches_2 = UserMatch.query.filter((UserMatch.um_ud_id_1 == userID_2) & (UserMatch.um_ud_id_2 == userID_1)).filter(UserMatch.um_2_matched == True).filter(UserMatch.um_1_matched == True).all()

    accepted = False
    print(matches_1)
    if len(matches_1) == 1:
        accepted = True
    elif len(matches_2) == 1:
        accepted = True

    print(accepted)
    return jsonify({
        'STATUS_CODE': '200',
        'result': accepted
    })

# finds furthest neighbours for a given user
@app.route('/find_furthest_matches', methods=['GET'])
@cross_origin()
def find_furthest_matches():
    param = request.args.get('user_id')
    limit = int(request.args.get('limit'))
    interest_cat = request.args.get('interestCat')
    if interest_cat != None and interest_cat != "All interests":
        query = f'select uid1.uid_ud_id, uid2.uid_ud_id, sqrt(sw1.sum + sw2.sum - sum(2*uid1.uid_interest_weight*uid2.uid_interest_weight)) as distance from squared_weights sw1 , squared_weights sw2 , user_interest_data uid1 , user_interest_data uid2 where sw1.uid_ud_id = uid1.uid_ud_id and sw2.uid_ud_id = uid2.uid_ud_id and uid1.uid_interest_type = uid2.uid_interest_type and uid1.uid_interest_type = \'{interest_cat}\' and uid1.uid_id <> uid2.uid_id and uid1.uid_ud_id = {param} and uid1.uid_ud_id <> uid2.uid_ud_id group by uid2.uid_ud_id, uid1.uid_ud_id, uid1.uid_squared_weight,uid2.uid_squared_weight,uid1.uid_interest_weight,uid2.uid_interest_weight,sw1.sum,sw2.sum order by distance desc limit 50;'
    else:
        print("True")
        query = f'select uid1.uid_ud_id, uid2.uid_ud_id, sqrt(sw1.sum + sw2.sum - sum(2*uid1.uid_interest_weight*uid2.uid_interest_weight)) as distance from squared_weights sw1 , squared_weights sw2 , user_interest_data uid1 , user_interest_data uid2 where sw1.uid_ud_id = uid1.uid_ud_id and sw2.uid_ud_id = uid2.uid_ud_id and uid1.uid_interest_type = uid2.uid_interest_type and uid1.uid_id <> uid2.uid_id and uid1.uid_ud_id = {param} and uid1.uid_ud_id <> uid2.uid_ud_id group by uid2.uid_ud_id, uid1.uid_ud_id, uid1.uid_squared_weight,uid2.uid_squared_weight,uid1.uid_interest_weight,uid2.uid_interest_weight,sw1.sum,sw2.sum order by distance desc limit 50;'
    results = db.engine.execute(query)
    response = []
    index = 0
    for res in results:
        print(res)
        m1 = UserMatch.query.filter_by(um_ud_id_1=param,um_ud_id_2=res.uid_ud_id).first()
        m2 = UserMatch.query.filter_by(um_ud_id_2=param,um_ud_id_1=res.uid_ud_id).first()
        if not m1 and not m2:
            newMatch = UserMatch(param, res.uid_ud_id)
            db.session.add(newMatch)
            response.append(dict(res))
            index = index + 1
            db.session.commit()
        else:
            accepted_check_1 = UserMatch.query.filter((UserMatch.um_ud_id_1 == param) & (UserMatch.um_ud_id_2 == res.uid_ud_id)).filter(UserMatch.um_1_matched == True).filter(UserMatch.um_2_matched == True).all()
            accepted_check_2 = UserMatch.query.filter((UserMatch.um_ud_id_1 == res.uid_ud_id) & (UserMatch.um_ud_id_2 == param)).filter(UserMatch.um_2_matched == True).filter(UserMatch.um_1_matched == True).all()
            if not accepted_check_1 and not accepted_check_2:
                blocked_check_1 = UserMatch.query.filter((UserMatch.um_ud_id_1 == param) & (UserMatch.um_ud_id_2 == res.uid_ud_id)).filter(UserMatch.um_blocked == True).all()
                blocked_check_2 = UserMatch.query.filter((UserMatch.um_ud_id_1 == res.uid_ud_id) & (UserMatch.um_ud_id_2 == param)).filter(UserMatch.um_blocked == True).all()
                if not blocked_check_1 and not blocked_check_2:
                    for item in response:
                        if item['uid_ud_id'] == res.uid_ud_id:
                            break
                    else:
                        response.append(dict(res))
                        index = index + 1
        if index >= limit:
            break
    print(response)

    return jsonify({
        'STATUS_CODE': '200',
        'result': response
    })

# finds nearest neighbours for a given user
@app.route('/find_matches', methods=['GET'])
@cross_origin()
def find_matches():
    param = request.args.get('user_id')
    limit = int(request.args.get('limit'))
    interest_cat = request.args.get('interestCat')
    if interest_cat != None and interest_cat != "All interests":
        query = f'select uid1.uid_ud_id, uid2.uid_ud_id, sqrt(sw1.sum + sw2.sum - sum(2*uid1.uid_interest_weight*uid2.uid_interest_weight)) as distance from squared_weights sw1 , squared_weights sw2 , user_interest_data uid1 , user_interest_data uid2 where sw1.uid_ud_id = uid1.uid_ud_id and sw2.uid_ud_id = uid2.uid_ud_id and uid1.uid_interest_type = uid2.uid_interest_type and uid1.uid_interest_type = \'{interest_cat}\' and uid1.uid_id <> uid2.uid_id and uid1.uid_ud_id = {param} and uid1.uid_ud_id <> uid2.uid_ud_id group by uid2.uid_ud_id, uid1.uid_ud_id, uid1.uid_squared_weight,uid2.uid_squared_weight,uid1.uid_interest_weight,uid2.uid_interest_weight,sw1.sum,sw2.sum order by distance limit 50;'
    else:
        query = f'select uid1.uid_ud_id, uid2.uid_ud_id, sqrt(sw1.sum + sw2.sum - sum(2*uid1.uid_interest_weight*uid2.uid_interest_weight)) as distance from squared_weights sw1 , squared_weights sw2 , user_interest_data uid1 , user_interest_data uid2 where sw1.uid_ud_id = uid1.uid_ud_id and sw2.uid_ud_id = uid2.uid_ud_id and uid1.uid_interest_type = uid2.uid_interest_type and uid1.uid_id <> uid2.uid_id and uid1.uid_ud_id = {param} and uid1.uid_ud_id <> uid2.uid_ud_id group by uid2.uid_ud_id, uid1.uid_ud_id, uid1.uid_squared_weight,uid2.uid_squared_weight,uid1.uid_interest_weight,uid2.uid_interest_weight,sw1.sum,sw2.sum order by distance limit 50;'
    results = db.engine.execute(query)
    response = []
    index = 0
    for res in results:
        print(res)
        m1 = UserMatch.query.filter_by(um_ud_id_1=param,um_ud_id_2=res.uid_ud_id).first()
        m2 = UserMatch.query.filter_by(um_ud_id_2=param,um_ud_id_1=res.uid_ud_id).first()
        if not m1 and not m2:
            newMatch = UserMatch(param, res.uid_ud_id)
            db.session.add(newMatch)
            response.append(dict(res))
            index = index + 1
            db.session.commit()
        else:
            accepted_check_1 = UserMatch.query.filter((UserMatch.um_ud_id_1 == param) & (UserMatch.um_ud_id_2 == res.uid_ud_id)).filter(UserMatch.um_1_matched == True).filter(UserMatch.um_2_matched == True).all()
            accepted_check_2 = UserMatch.query.filter((UserMatch.um_ud_id_1 == res.uid_ud_id) & (UserMatch.um_ud_id_2 == param)).filter(UserMatch.um_2_matched == True).filter(UserMatch.um_1_matched == True).all()
            if not accepted_check_1 and not accepted_check_2:
                blocked_check_1 = UserMatch.query.filter((UserMatch.um_ud_id_1 == param) & (UserMatch.um_ud_id_2 == res.uid_ud_id)).filter(UserMatch.um_blocked == True).all()
                blocked_check_2 = UserMatch.query.filter((UserMatch.um_ud_id_1 == res.uid_ud_id) & (UserMatch.um_ud_id_2 == param)).filter(UserMatch.um_blocked == True).all()
                if not blocked_check_1 and not blocked_check_2:
                    for item in response:
                        if item['uid_ud_id'] == res.uid_ud_id:
                            break
                    else:
                        response.append(dict(res))
                        index = index + 1
        if index >= limit:
            break
    print(response)

    return jsonify({
        'STATUS_CODE': '200',
        'result': response
    })

# Gets distances, ids and names of users for network graph
@app.route('/get_names', methods=['GET'])
@cross_origin()
def get_names():
    user_id = request.args.get('user_id')
    query = f'select uid2.uid_ud_id as id, sqrt(sw1.sum + sw2.sum - sum(2*uid1.uid_interest_weight*uid2.uid_interest_weight)) as distance from squared_weights sw1 , squared_weights sw2 , user_interest_data uid1 , user_interest_data uid2 where sw1.uid_ud_id = uid1.uid_ud_id and sw2.uid_ud_id = uid2.uid_ud_id and uid1.uid_interest_type = uid2.uid_interest_type and uid1.uid_id <> uid2.uid_id and uid1.uid_ud_id = {user_id} and uid1.uid_ud_id <> uid2.uid_ud_id  group by uid2.uid_ud_id, uid1.uid_ud_id, uid1.uid_squared_weight,uid2.uid_squared_weight,uid1.uid_interest_weight,uid2.uid_interest_weight,sw1.sum,sw2.sum order by distance limit 5;'
    results = db.engine.execute(query)
    data = []
    for res in results:
        name = UserData.query.filter_by(ud_id=res['id']).first().ud_forename
        data.append({'id' : res['id'], 'name': name, 'distance': res['distance']})
    print(data)
    return jsonify({
        'result': data
    })

# Gets recommendations for a given user


@app.route('/get_recs_for', methods=['GET'])
def get_recs_for():
    param = request.args.get('user_id')
    test_user = "345"
    fake_users = ["556", "223"]
    if (param == test_user):
        return jsonify({
            "recommendations": fake_users,
            "STATUS_CODE": "200"
        })
    elif (param == None):
        return jsonify({
            "STATUS_CODE": "500",
            "Message": "Please provide a user id"
        })
    else:
        return jsonify({
            "STATUS_CODE": "500",
            "Message": "Please ensure user exists in database"
        })

# Adds User Report to database
@app.route('/report', methods=['POST'])
def report():
    id_1 = request.form.get('id_1')
    id_2 = request.form.get('id_2')
    report = request.form.get('report')
    details = request.form.get('details')
    new_report = ReportUser(id_1, id_2, report, details)
    db.session.add(new_report)
    db.session.commit()
    return jsonify({
        'STATUS_CODE': '200',
        "Message": 'Report added'
    })


# Test endpoint - an example of how to make a transaction

@app.route('/test_user', methods=['POST'])
def create_test_user():
    from random import randint
    user = UserData('Faridz', 'Ibrahim', 19, f'{randint(0, 6000)}',
                    f'{randint(0, 6000)}', f'{randint(0, 6000)}', 'M', f'{randint(0, 6000)}')
    db.session.add(user)
    db.session.commit()
    return jsonify({
        'STATUS_CODE': '200',
        "Message": 'User added'
    })

@app.route('/dummy_data', methods=['POST'])
def dummy_data():
    db.session.query(UserData).delete()
    db.session.query(UserInterestData).delete()
    db.session.query(SquaredWeights).delete()
    db.session.query(UserMatch).delete()
    from random import randint, uniform
    no_users = request.form.get('no_users')
    no_cats = request.form.get('no_cats')
    for i in range(int(no_users)):
        print(i)
        user = UserData('Faridz', 'Ibrahim', 19, "fake"+str(i)+"@manchester.ac.uk",
                        i, str(i), 'M', f'{randint(0, 6000)}')
        db.session.add(user)
        db.session.commit()
        for j in range(int(no_cats)):
            notSuccessful = True
            cat = 0
            while notSuccessful:
                cat = str(randint(0, int(no_cats)*50)) 
                # change 50 to decrease the number of categories available to pick from for each user's interests 
                print("this is" + str(cat))
                user_interests = UserInterestData.query.filter_by(uid_ud_id=i, uid_interest_type=cat).first()
                if not user_interests:
                    notSuccessful = False
            cat = "category"+str(cat)
            interest = UserInterestData(i,  cat, uniform(0,2), uniform(0,2))
            db.session.add(interest)
            db.session.commit()
            user_interests = UserInterestData.query.filter_by(uid_ud_id=i, uid_interest_type=cat).first()
            user_interests.updateScores()

    return jsonify({
        'STATUS_CODE': '200',
        "Message": 'Users added'
    })

@app.route('/')
def index():
    return "<h1>Welcome to our server !!</h1>"


if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)
