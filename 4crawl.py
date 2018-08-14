import os
import sys
import json
import time
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


BONUS_KEYWORDS = ["sauce", "bump", "more", "moar", "plz", "name", "please"]


URL_CATALOG = "http://a.4cdn.org/{0}/catalog.json"
URL_POSTS = "http://a.4cdn.org/{0}/thread/{1}.json"
URL_FILE = "http://i.4cdn.org/{0}/{1}{2}"


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
                temp_str = str(argv[a + 1])
                args["match-thread"] = temp_str
            else:
                print("A string must be specified.")
                exit(0)

        elif argv[a] in ["--match-post", "-mp"]:
            if a + 1 < len(argv):
                temp_str = str(argv[a + 1])
                args["match-post"] = temp_str
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
    req = urllib.request.Request(url, headers={"User-AGent": "Magic Browser"})
    try:
        res = urllib.request.urlopen(req)
        data = json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(Color.RED + str(e) + Color.END)
    last_request = time.time()
    return data


def evaluate_assertions(value, expressions):
    result = True
    for e in expressions:
        result = result and evaluate_assertion(value, e)
        if not result:
            break
    return result

def evaluate_assertion(value, expression):
    operator, reference = expression
    if operator in [">", "gt"]:
        return value > reference
    elif operator in ["<", "lt"]:
        return value < reference
    elif operator in ["=", "eq"]:
        return value == reference
    elif operator in ["<=", "lte"]:
        return value <= reference
    elif operator in [">=", "gte"]:
        return value >= reference
    return False


def escape(path):
    return path.replace("/", "").replace("<", "").replace(">", "")\
               .replace(":", "").replace('"', "").replace("\\", "")\
               .replace("|", "").replace("?", "").replace("*", "")


def compute_thread(board, thread, args, index, total):
    data = json_request(URL_POSTS.format(board, thread["no"]))
    if data is None:
        return 0
    posts = data["posts"]
    print("{0}/{1}:\t{2} posts found...".format(index, total, len(posts)),
          end="")
    valid = {}
    for post in posts:
        ext, com = "", ""
        if "com" in post: com = post["com"]
        if ("filename" in post
        and (len(args["extensions"]) == 0 or post["ext"] in args["extensions"])
        and args["match-post"] in "com"
        and evaluate_assertions(post["w"], args["width"])
        and evaluate_assertions(post["h"], args["height"])):
            valid[post["no"]] = {"post": post, "replies": 0, "bonus": 0}
        if len(com) > 0:
            for link in [l for l in com.split('href="') if l[:2] == "#p"]:
                reply_id, b = "", 2
                while b < len(link) and link[b] in [str(k) for k in range(10)]:
                    reply_id += link[b]
                    b += 1
                reply_id = int(reply_id)
                if reply_id in valid.keys():
                    valid[reply_id]["replies"] += 1
                    for keyword in BONUS_KEYWORDS:
                        if keyword in com.lower():
                            valid[reply_id]["bonus"] += 1
    scores = []
    for key in valid.keys():
        scores.append(valid[key]["replies"] + valid[key]["bonus"])
    avg_score = "NaN"
    if len(scores) > 0:
        avg_score = sum(scores) / float(len(scores))
    prefix = "\r{0}/{1}:\t{2} posts found, {3} are valid;\tavg score:{4}"\
             .format(index, total, len(posts), len(valid), str(avg_score)[:4])
    print(prefix, end="")
    sys.stdout.flush()

    folder = board
    if not args["one-folder"]:
        folder += "/" + str(thread["no"])
    if not args["one-folder"] and "sub" in thread:
        folder += "-" + escape(thread["sub"])
    to_download = list(valid.values())
    to_download.sort(key=lambda p: -(p["replies"] + p["bonus"]))
    if args["max-posts"] > 0:
        to_download = [p for p in to_download[:args["max-posts"]]
                       if p["replies"] + p["bonus"] >= avg_score]
    for i, post in enumerate(to_download):
        print("{0};\tdownload {1}/{2}".format(prefix, i+1, len(to_download)),
              end="")
        if i == 0 and not os.path.exists(folder):
            os.makedirs(folder)
        filename = folder + "/" + str(post["post"]["tim"]) + post["post"]["ext"]
        url = URL_FILE.format(board, post["post"]["tim"], post["post"]["ext"])
        try:
            urllib.request.urlretrieve(url, filename)
        except urllib.error.HTTPError:
            print("\nError downloading {0} at {1}".format(url, filename))
    print("{0};\t{1} files downloaded.".format(prefix, len(to_download)))
    sys.stdout.flush()
    return len(to_download)


def compute_boards(args):
    dl_count = 0
    for board in args["boards"]:
        print("\n===   BOARD " + board + "   ===\n")
        catalog = json_request(URL_CATALOG.format(board))
        total = sum([len(page["threads"]) for page in catalog])
        threads = []
        if args["list-threads"]:
            print(Color.BOLD + "no\t\timages\treplies\ttitle" + Color.END)
        for page in catalog:
            for thread in page["threads"]:
                sub, com = "", ""
                if "sub" in thread: sub = thread["sub"].lower()
                if "com" in thread: com = thread["com"].lower()
                if (("sticky" not in thread or not args["omit-sticky"]) and
                (len(threads) < args["max-threads"] or args["max-threads"] < 1)
                and args["match-thread"] in sub + com):
                    if args["list-threads"]:
                        img_count = thread["images"]
                        if "filename" in thread:
                            img_count += 1
                        if "sticky" in thread:
                            img_count = "\t" + str(img_count)
                        print("{0}\t{2}\t{3}\t{1}".format(thread["no"], sub,
                              img_count, thread["replies"]))
                    else:
                        threads.append(thread)
        print("{0} threads found, {1} to process.".format(total, len(threads)))
        sys.stdout.flush()
        for i, thread in enumerate(threads):
            dl_count += compute_thread(board, thread, args, i + 1, len(threads))
    print("\n{0} images downloaded.".format(dl_count))


compute_argv(sys.argv)
