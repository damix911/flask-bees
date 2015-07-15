from flask import Flask
from bees import Bees

app = Flask(__name__)
bees = Bees(app, "/api/v1/")

@app.route("/")
def index():
    s = "<h1>Our API</h1>"
    s += "<ul>"
    for name in bees.names:
        s += "<li><a href='/api/v1/%s:docs'>%s</a></li>" % (name, name)
    s += "</ul>"
    s += """
    <script src="/api/v1/api.js"></script>
    <script>
        window.onload = function () {
            api.meta_clients()
            .success(function (data) {
                var clients = document.getElementById("clients");

                for (var platform in data.platforms) {
                    var li = document.createElement("LI");
                    var a = document.createElement("A");
                    a.setAttribute("href", data.platforms[platform]);
                    a.appendChild(document.createTextNode(platform));
                    li.appendChild(a);
                    clients.appendChild(li);
                }
            });
        }
    </script>
    <h2>Available Clients</h2>
    <ul id="clients">
    </ul>
    """
    return s

@bees.publish("foo")
def f(i):
    return {"foo": "bar"}

@bees.publish("add")
def f(i):
    """
    Addiziona due numeri.

    <h2>Example</h2>
    <pre>{"x": 3, "y": 7} ==> {"r": 10}</pre>

    <h2>Try</h2>
    <script src="/api/v1/api.js"></script>
    <script>
        function btnClick() {
            api.add({'x': 3, 'y': 7})
            .success(function (data) {
                alert(JSON.stringify(data));
            });
        }
    </script>
    <button onclick="btnClick()">3 + 7</button>
    """
    return {"r": i["x"] + i ["y"]}

if __name__ == "__main__":
    app.run()
