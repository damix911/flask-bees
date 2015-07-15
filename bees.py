from flask import jsonify, request, Response

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

_sessions = {}

def _bind(func):
    def f():
        try:
            data = request.get_data()
            if data:
                i = request.get_json()
            else:
                i = {}

            if not i:
                i = {}

            i["method"] = request.method

            o = func(i)

            if not o:
                o = {}

            o["error"] = False

            return jsonify(o)
        except Exception as e:
            import traceback
            print(traceback.format_exc())

            msg = str(e)
            code = ''.join(e for e in msg.lower() if e.isalnum() or e.isspace())
            code = code.replace(" ", "_")
            return jsonify({"error": True, "errorMessage": msg, "errorCode": code})
    return f

class Bees(object):
    def __init__(self, app, base):
        self.app = app
        self.base = base
        self.names = []

        @app.route(self.base + "api.js")
        def js():
            up = urlparse(request.url)
            application = "%s://%s" % (up.scheme, up.netloc)
            return Response(self.js_client(application), mimetype="text/plain")

        @app.route(self.base + "api.py")
        def py():
            up = urlparse(request.url)
            application = "%s://%s" % (up.scheme, up.netloc)
            return Response(self.py_client(application), mimetype="text/plain")

        @app.route(self.base + "api_corona.lua")
        def corona_lua():
            up = urlparse(request.url)
            application = "%s://%s" % (up.scheme, up.netloc)
            return Response(self.corona_lua_client(application), mimetype="text/plain")

        @self.publish("meta_clients")
        def meta_clients(i):
            o = {}

            o["platforms"] = {}

            o["platforms"]["javascript"] = self.base + "api.js"
            o["platforms"]["python"] = self.base + "api.py"
            o["platforms"]["corona_lua"] = self.base + "api_corona.lua"

            return o

    def publish(self, ep):
        def deco(func):
            @self.app.route(self.base + ep + ":docs", methods = ["GET"], endpoint = ep + ":docs")
            def f():
                if func.__doc__:
                    return "<h1>%s</h1><div class=\"docs\">%s</div>" % (ep, func.__doc__)
                else:
                    return "<h1>%s</h1><div class=\"docs\">%s</div>" % (ep, "No documentation attached.")

            @self.app.route(self.base + ep + ":examples.javascript", methods = ["GET"], endpoint = ep + ":examples.javascript")
            def f():
                return "var x = 10;"

            @self.app.route(self.base + ep + ":examples.python", methods = ["GET"], endpoint = ep + ":examples.python")
            def f():
                return "x = 10"

            @self.app.route(self.base + ep + ":examples.corona_lua", methods = ["GET"], endpoint = ep + ":examples.corona_lua")
            def f():
                return "local x = 10"

            self.names.append(ep)
            tmp = _bind(func)
            r = self.app.route(self.base + ep, methods = ["GET", "POST", "PUT", "DELETE"], endpoint = ep)
            return r(tmp)
        return deco

    def js_client(self, app_url):
        src = ""
        src += "var __application = \"%s\";\n" % app_url
        src += "var __base = \"%s\";\n" % self.base
        src += """
function __ajax(method, url, data, onHttpSuccess, onHttpFail) {
  var xhr = new XMLHttpRequest();
  xhr.open(method, url);
  xhr.onreadystatechange = function () {
    if (xhr.readyState == 4) {
      if (xhr.status == 200) {
        onHttpSuccess(JSON.parse(xhr.responseText));
      }
      else {
        onHttpFail(xhr.status);
      }
    }
  };
  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.send(JSON.stringify(data));
}

function __bees(method, relUrl, data, onSuccess, onFail) {
  __ajax(method, __application + __base + relUrl, data, function (d) {
    if (!d.error)
      onSuccess(d);
    else
      onFail(d.errorCode, d.errorMessage);
  },
  function (status) {
    onFail("http_" + status, "An HTTP error has occurred.");
  });
}

function __Promise() {
  this.success = function (s) {
    this._onSuccess = s;
    return this;
  };

  this.fail = function (f) {
    this._onFail = f;
    return this;
  };
}
"""

        src += "var api = {};\n"
        src += "api.session = '';\n"
        src += "api.onsessionchanged = null;\n"

        for name in self.names:
            jsName = name
            pyName = name
            src += """
api.%s = function (i) {
  var promise = new __Promise();

  if (!i) {
    i = {};
  }

  if (api.session != '') {
    i.session = api.session;
  }

  __bees("POST", "%s", i, function (data) {
    if ('session' in data) {
      api.session = data.session;
      if (api.onsessionchanged)
        api.onsessionchanged(api.session);
    }

    if (promise._onSuccess)
      promise._onSuccess(data, i);
  },
  function (errorCode, errorMessage) {
    if (promise._onFail)
      promise._onFail(errorCode, errorMessage, i);
  });

  return promise;
};
""" % (jsName, pyName)

        return src

    def py_client(self, app_url):
        src = ""
        src += """
import requests
import json
"""
        src += "\n"
        src += "application = \"%s\"\n" % app_url
        src += "base = \"%s\"\n" % self.base
        src += "session = ''\n"
        src += "onsessionchanged = None\n"

        for name in self.names:
            pyName = name
            epName = name
            src += """
def %s(i = None):
    global application
    global base
    global session
    global onsessionchanged

    if not i:
        i = {}

    if session != "":
        i["session"] = session

    o = requests.post(application + base + \"%s\", data=json.dumps(i), headers={"Content-Type": "application/json"}).json()

    if "session" in o:
        session = o["session"]
        if onsessionchanged:
            onsessionchanged(session)

    return o
""" % (pyName, epName)

        return src

    def corona_lua_client(self, app_url):
        src = ""
        src += "local api = {}\n"
        src += "api.application = \"%s\"\n" % app_url
        src += "api.base = \"%s\"\n" % self.base
        src += "api.session = ''\n"
        src += "api.onsessionchanged = None\n"

        for name in self.names:
            luaName = name
            epName = name
            src += """
function api.%s(i)
    if not i then
        i = {}
    end

    if api.session != "" then
        i["session"] = api.session
    end

    --[[ !!!TODO!!!
    o = requests.post(application + base + \"%s\", data=json.dumps(i), headers={"Content-Type": "application/json"}).json()

    if "session" in o:
        session = o["session"]
        if onsessionchanged:
            onsessionchanged(session)

    return o
    ]]--
end
""" % (luaName, epName)


        src += "return api\n"

        return src

def new_session(permissions):
    import random, string
    s = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))
    _sessions[s] = {}
    _sessions[s]["permissions"] = permissions[:]
    return s

def del_session(i):
    if i and "session" in i:
        if i["session"] != "":
            session = i["session"]
            del _sessions[session]

def get_session(i):
    session = None
    if i and "session" in i:
        s = i["session"]
        if s in _sessions:
            session = _sessions[s]
    return session

def get_active_sessions():
    return _sessions

def has_one_of(i, permissions):
    if len(permissions) == 0:
        raise Exception("At least one permission should be specified.")
    session = get_session(i)
    if not session:
        return False
    for needed in permissions:
        for actual in session["permissions"]:
            if needed == actual:
                return True

def needs_one_of(i, permissions):
    if not has_one_of(i, permissions):
        raise Exception("Unauthorized.")
