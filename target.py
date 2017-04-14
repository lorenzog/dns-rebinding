#!/usr/bin/env python3
# Run this script on a different host to see what happens
from __future__ import print_function
import argparse
from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    return "This is the target main page"


@app.after_request
def return_cors(response):
    # response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers['Cache-Control'] = 'no-cache'
    return response


def secret_content():
    # TODO set a httpOnly cookie?
    return "This is the secret content"


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("port", type=int, help="Target port")
    parser.add_argument("target_path", help="Where the secret content is")
    parser.add_argument("-d", "--debug", action="store_true")
    args = parser.parse_args()

    print("[+] Loading target...")
    if args.debug:
        app.debug = True
    # dynamically add the URL for the secret content
    app.add_url_rule(
        "/{}".format(args.target_path), 'secret_content', secret_content)

    app.run(host="0.0.0.0", port=args.port)
