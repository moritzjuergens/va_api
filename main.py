import os
from uuid import uuid4
from flask import Flask, Response, request
import requests
import json
from supabase import create_client, Client
from flask_cors import CORS


app = Flask(__name__, static_folder='../client/dist/',    static_url_path='/')


CORS(app, resources={r'/*': {'origins': '*'}})

supabase_url = "https://hqatoyyncrwdojrhwygi.supabase.co"
supabase_key = os.getenv("SUPABASE_KEY")
if supabase_key is None or len(supabase_key) == 0:
    raise Exception(
        "please make sure to provide the SUPABASE_KEY environment variable")

client: Client = create_client(
    supabase_url=supabase_url, supabase_key=supabase_key)


@app.route("/highscores", methods=["GET"])
def highscores():
    try:
        res = client.postgrest.from_table("highscores").select("*").execute()
        return Response(json.dumps(res.data), mimetype='application/json')
    except Exception as err:
        print(err)
        return Response(status=500)


@app.route("/questions", methods=["GET"])
def questions():
    try:
        res = client.postgrest.from_table("questions").select("*").execute()
        return Response(json.dumps(res.data), mimetype='application/json')
    except Exception as err:
        print(err)
        return Response(status=500)


@app.route("/start/<name>/<question_cnt>", methods=["GET"])
def start(name, question_cnt):

    try:
        res = client.postgrest.from_("questions").select("*").execute()
    except Exception as err:
        print(err)

    questions = []
    print(questions)
    #questions['answer_given'] = 0
    for question in res.data:
        temp = {
            "id": question['id'],
            "question": question['question'],
            "answers": question["answers"],
            "corr_idx": question["corr_idx"],
            "answer_given": 0,
        }
        questions.append(temp)
    print(questions)
    game_id = str(uuid4())
    game_info = json.dumps({
        "name": name,
        "questions": questions
    })

    try:
        client.postgrest.from_("games").insert({
            "game_id": game_id,
            "game_info": game_info
        }).execute()
    except Exception as err:
        print(err)
        return Response(status=600)

    return Response(json.dumps({"game_id": game_id, "game_info": game_info}), status=200, mimetype='application/json')


@app.route("/answer", methods=["POST"])
def check_answer():
    payload = request.json

    try:
        game = client.postgrest.from_table("games").select(
            "*").query("WHERE game_id=" + payload.game_id).execute()
    except Exception as err:
        print(err)
        return Response(status=500)

    for question in game.questions:
        if(question.id != payload.question_id):
            continue
        question.answer_given = payload.answer

        return Response(json.dumps({answer: "correct"}))
    return Response(json.dumps({answer: "incorrect"}))


@app.route("/results", methods=["POST"])
def store_results():
    payload = request.json

    try:
        client.postgrest.from_table("highscores").upsert({
            "name": payload["player"],
            "score": payload["score"]
        }).execute()
        return Response(status=200)
    except Exception as err:
        print(err)
        return Response(status=500)


@app.route("/questions", methods=["POST"])
def post_questions():
    payload = request.json

    try:
        client.postgrest.from_table("questions").upsert({
            "question": payload["question"],
            "answers": payload["answers"],
            "corr_idx": payload["corr_idx"]
        }).execute()
        return Response(status=200)
    except Exception as err:
        print(err)
        return Response(status=500)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7777))
    app.run(host='0.0.0.0', port=port)
