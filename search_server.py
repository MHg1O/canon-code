#!/usr/bin/env python3

import flask

from model import ModelInfo
from manage import model_image_func

app = flask.Flask("search server")

mi = ModelInfo("/Users/benzlock/Desktop/mhg1o/canon/model-info.json")
model_image = model_image_func(3)

@app.route("/api/search")
def search():
    query = flask.request.args["query"]

    if query == "":
        return flask.jsonify({})

    response = []
    for model, score in mi.extensive_name_search(query)[:4]:
        response += [
                {
                    "name": model.display_name,
                    "model_id": model.model_id,
                    "image": model_image(model.model_id)
                    }
                ]

    print(response)
    return flask.jsonify(response)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
