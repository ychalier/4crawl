import os
import re
import sys
import json
import time
import networkx
import urllib.error
import urllib.request


class Color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'


BOARDS = ["a", "b", "c", "d", "e", "f", "g", "gif", "h", "hr", "k", "m", "o",
          "p", "r", "s", "t", "u", "v", "vg", "vr", "w", "wg", "i", "ic", "r9k",
          "s4s", "vip", "cm", "hm", "lgbt", "y", "3", "aco", "adv", "an", "asp",
          "biz", "cgl", "ck", "co", "diy", "fa", "fit", "gd", "hc", "his",
          "int", "jp", "lit", "mlp", "mu", "n", "news", "out", "po", "pol",
          "qst", "sci", "soc", "sp", "tg", "toy", "trv", "tv", "vp", "wsg",
          "wsr", "x"]


KEYWORDS = ["sauce", "bump", "more", "moar", "plz", "name", "please",
    "thank you", "thanks", "thank u", "thx", "finally", "this."]


URL_CATALOG = "http://a.4cdn.org/{0}/catalog.json"
URL_POSTS = "http://a.4cdn.org/{0}/thread/{1}.json"
URL_FILE = "http://i.4cdn.org/{0}/{1}"


def compute_argv(argv):
    # default arguments
    args = {
        "boards": [],
        "max-threads": 0,
        "max-posts": -1,
        "extensions": [],
        "omit-sticky": False,
        "match-thread": "",
        "match-post": "",
        "ignore-thread": "",
        "width": [],
        "height": [],
        "one-folder": False,
        "list-threads": False
    }

    operators = ["<", ">", "=", "<=", ">=", "gte", "lte", "lt", "gt", "eq"]

    a = 1  # argument index
    while a < len(argv):

        if argv[a] in ["--boards", "-b"]:
            while a + 1 < len(argv) and argv[a + 1][:1] != "-":
                if argv[a + 1] in BOARDS:
                    args["boards"].append(argv[a + 1])
                else:
                    print(argv[a + 1] + " is not a valid board.")
                    exit(0)
                a += 1
            if len(args["boards"]) == 0:
                print("At least one board must be specified.")
                exit(0)

        elif argv[a] in ["--extensions", "-e"]:
            while a + 1 < len(argv) and argv[a + 1][:1] != "-":
                if argv[a + 1][:1] == ".":
                    args["extensions"].append(argv[a + 1])
                else:
                    args["extensions"].append("." + argv[a + 1])
                a += 1
            if len(args["extensions"]) == 0:
                print("At least one extension must be specified.")
                exit(0)

        elif argv[a] in ["--max-threads", "-t"]:
            if a + 1 < len(argv):
                temp_int = int(argv[a + 1])
                if temp_int >= 0:
                    args["max-threads"] = temp_int
                else:
                    print("Number of threads must be positive.")
                    exit(0)
            else:
                print("A number of threads must be specified.")
                exit(0)
            a += 1

        elif argv[a] in ["--max-posts", "-p"]:
            if a + 1 < len(argv):
                temp_int = int(argv[a + 1])
                if temp_int >= 0:
                    args["max-posts"] = temp_int
                else:
                    print("Number of posts must be positive.")
                    exit(0)
            else:
                print("A number of posts must be specified.")
                exit(0)
            a += 1

        elif argv[a] in ["--match-thread", "-mt"]:
            if a + 1 < len(argv):
                args["match-thread"] = str(argv[a + 1])
            else:
                print("A string must be specified.")
                exit(0)

        elif argv[a] in ["--ignore-thread", "-it"]:
            if a + 1 < len(argv):
                args["ignore-thread"] = str(argv[a + 1])
            else:
                print("A string must be specified.")
                exit(0)

        elif argv[a] in ["--match-post", "-mp"]:
            if a + 1 < len(argv):
                args["match-post"] = str(argv[a + 1])
            else:
                print("A string must be specified.")
                exit(0)

        elif argv[a] in ["--omit-sticky", "-os"]:
            args["omit-sticky"] = True

        elif argv[a] in ["--width", "-w"]:
            while a + 2 < len(argv) and argv[a+1][:1] != "-":
                if argv[a+1] in operators:
                    args["width"].append((argv[a+1], int(argv[a+2])))
                else:
                    print("Wrong operator in width selecting: " + argv[a+1])
                    exit(0)
                a += 2
            if len(args["width"]) == 0:
                print("Width: an expression must be specified.")

        elif argv[a] in ["--height", "-h"]:
            while a + 2 < len(argv) and argv[a+1][:1] != "-":
                if argv[a+1] in operators:
                    args["height"].append((argv[a+1], int(argv[a+2])))
                else:
                    print("Wrong operator in height selecting: " + argv[a+1])
                    exit(0)
                a += 2
            if len(args["height"]) == 0:
                print("Height: an expression must be specified.")

        elif argv[a] in ["--one-folder", "-f"]:
            args["one-folder"] = True

        elif argv[a] in ["--list-threads", "-lt"]:
            args["list-threads"] = True

        a += 1

    if len(args["boards"]) == 0:
        print("\nUSAGE:\n"
              "    4crawl [parameters]\n\n"
              "    parameters\n"
              "      --boards       |  -b \n"
              "      --list-threads | -lt \n"
              "      --max-threads  |  -t \n"
              "      --max-posts    |  -p \n"
              "      --extension    |  -e \n"
              "      --match-thread | -mt \n"
              "      --match-post   | -mp \n"
              "      --omit-sticky  | -os \n"
              "      --width        |  -w \n"
              "      --height       |  -h \n"
              "      --one-folder   |  -f \n\n"
              "See the GitHub readme for more info.")
    else:
        compute_boards(args)


last_request = 0
def json_request(url):
    global last_request
    data = None
    if time.time() - last_request <= 1:
        time.sleep(last_request - time.time() + 1.0)
    req = urllib.request.Request(url, headers={"User-Agent": "Magic Browser"})
    try:
        res = urllib.request.urlopen(req)
        data = json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(Color.RED + str(e) + Color.END)
    last_request = time.time()
    return data


def compute_thread(board, thread, args, index, total):
    def print_aux(prefix, string, end=""):
        print("\r" + prefix + string, end=end)
        sys.stdout.flush()
        return prefix + string

    def post_is_valid(args, post):
        def evaluate_expressions(value, expressions):
            for expression in expressions:
                operator, reference = expression
                if operator in [">", "gt"] and value <= reference:
                    return False
                elif operator in ["<", "lt"] and value >= reference:
                    return False
                elif operator in ["=", "eq"] and value != reference:
                    return False
                elif operator in ["<=", "lte"] and value > reference:
                    return False
                elif operator in [">=", "gte"] and value < reference:
                    return False
            return True
        return ("filename" in post
            and (len(args["extensions"]) == 0
            or post["ext"] in args["extensions"])
            and ("com" in post and args["match-post"] in post["com"].lower()
            or len(args["match-post"]) == 0)
            and evaluate_expressions(post["w"], args["width"])
            and evaluate_expressions(post["h"], args["height"]))

    prefix = print_aux("", "{0}\t{1}\t".format(index, thread["id"]))

    data = json_request(URL_POSTS.format(board, thread["no"]))
    if data is None:
        return 0
    posts_list = data["posts"]
    prefix = print_aux(prefix, "{0}\t".format(len(posts_list)))

    edges, valid, posts = [], [], {}
    graph = networkx.DiGraph()
    for post in posts_list:
        posts[post["no"]] = post
        graph.add_node(post["no"])
        if "com" in post:
            weight = len([w for w in KEYWORDS if w in post["com"].lower()]) + 1
            pattern = r"#p([0-9]+)"
            matches = re.findall(pattern, post["com"], re.MULTILINE)
            for match in matches:
                graph.add_edge(post["no"], int(match), weight=weight)
                if int(match) in posts.keys():
                    if "history" not in posts[int(match)]:
                        posts[int(match)]["history"] = ""
                    posts[int(match)]["history"] += post["com"] + "\n-----\n"
        if post_is_valid(args, post):
            valid.append(post["no"])
    pagerank = networkx.pagerank(graph, max_iter=50)
    valid.sort(key=lambda no: -pagerank[no])
    valid = [posts[no] for no in valid]

    prefix = print_aux(prefix, "{0}\t".format(len(valid)))

    if args["max-posts"] > 0:
        del valid[args["max-posts"]:]

    # files download
    folder = "dl/" + board + "/"
    if not args["one-folder"]:
        folder += thread["folder"] + "/"
    if not os.path.exists(folder):
        os.makedirs(folder)
    for i, post in enumerate(valid):
        print_aux(prefix, "{0}/{1}".format(i+1, len(valid)))
        filename = str(post["tim"]) + post["ext"]
        url = URL_FILE.format(board, filename)
        try:
            urllib.request.urlretrieve(url, folder + filename)
        except urllib.error.HTTPError:
            print("\nError downloading {0} at {1}".format(url, filename))
        data = {
            "file": folder + filename,
            "thread": thread["title"],
            "board": board
        }
        if "history" in post: data["history"] = post["history"]
        if "com" in post: data["com"] = post["com"]
        with open("index.json", "a") as file:
            file.write(json.dumps(data, ensure_ascii=False) + ",")
    print_aux(prefix, "{0}/{1}".format(len(valid), len(valid)), "\n")

    return len(valid)


def compute_boards(args):
    def thread_is_valid(args, thread):
        sub, com = "", ""
        if "sub" in thread: sub = thread["sub"].lower()
        if "com" in thread: com = thread["com"].lower()
        return (("sticky" not in thread or not args["omit-sticky"])
            and args["match-thread"] in sub + com + str(thread["no"])
            and (args["ignore-thread"] not in sub + com + str(thread["no"])
            or args["ignore-thread"] == ""))

    dl_count = 0
    for board in args["boards"]:
        print("\n----- " + board + " -----\n")
        catalog = json_request(URL_CATALOG.format(board))
        total = sum([len(page["threads"]) for page in catalog])
        threads, replies, indexes = [], [], []
        if args["list-threads"]:
            print(Color.BOLD + "no\t\timages\treplies\ttitle" + Color.END)
        for page in catalog:
            for thread in page["threads"]:
                if thread_is_valid(args, thread):
                    title, folder, no = "", str(thread["no"]), str(thread["no"])
                    while len(no) < 8:
                        no = no + " "
                    if "sub" in thread:
                        title = thread["sub"]
                        folder += "-" + thread["sub"]
                    elif "com" in thread:
                        title = thread["com"]
                        folder += "-" + thread["com"][:20]
                    else:
                        title = str(thread["no"])
                    if len(title) >= 90:
                        title = title[:80] + "..."
                    for char in list("/<>:\"\\|?*."):
                        folder = folder.replace(char, "")
                    thread["title"] = title
                    thread["folder"] = folder
                    thread["id"] = no
                    thread["index"] = len(threads)
                    threads.append(thread)
        threads.sort(key=lambda thread:
            - (thread["replies"] / 350. + thread["index"] / 150.))
        if args["max-threads"] > 0:
            del threads[args["max-threads"]:]

        if args["list-threads"]:
            for thread in threads:
                img_count = thread["images"]
                if "filename" in thread:
                    img_count += 1
                print("{0}\t{2}\t{3}\t{1}".format(thread["id"],
                    thread["title"], img_count, thread["replies"]))
            threads = []

        print("{0} threads found, {1} to process\n".format(total, len(threads)))
        if len(threads) > 0:
            print(Color.BOLD + "id\tno\t\tposts\tvalid\tdownload" + Color.END)
            sys.stdout.flush()
            with open("index.json", "w") as file:
                file.write("[")
            for i, thread in enumerate(threads):
                dl_count += compute_thread(board, thread, args,
                                           i + 1, len(threads))
            with open("index.json", "rb+") as file:
                file.seek(-1, os.SEEK_END)
                file.write("]".encode())
    print("\n{0} images downloaded.".format(dl_count))


try:
    compute_argv(sys.argv)
except KeyboardInterrupt:
    print("\n\nProgram interrupted.")
