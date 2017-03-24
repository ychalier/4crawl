import os
import sys
import json
import urllib.error
import urllib.request


class Post:
    def __init__(self, thread, valid, no, now, name, com, filename, ext, fsize, w, h, tim):
        self.thread = thread
        self.valid = valid

        self.no = no
        self.now = now
        self.name = name
        self.com = com
        self.filename = filename
        self.ext = ext
        self.fsize = fsize
        self.w = w
        self.h = h
        self.tim = tim

        self.replies = 0
        self.bonus = 0

    def add_reply(self, com=""):
        self.replies += 1
        for keyword in ["sauce", "bump", "more", "moar", "plz", "name"]:
            if keyword in com.lower():
                self.bonus += 1

    def get_score(self):
        return self.replies + self.bonus

    def download(self):
        if not self.valid:
            log("Trying to download an unvalid post.")
            return
        filename = self.thread.folder + "/" + self.tim + self.ext
        url = "http://i.4cdn.org/" + self.thread.board + "/" + self.tim + self.ext
        try:
            urllib.request.urlretrieve(url, filename)
        except urllib.error.HTTPError:
            log("Error downloading " + url + " at " + filename)


class Thread:
    def __init__(self, board, no, now, name, sub, com, replies, images, args):
        self.board = str(board)
        self.no = str(no)
        self.now = str(now)
        self.name = str(name)
        self.sub = str(sub)
        self.com = str(com)
        self.replies = int(replies)
        self.images = int(images)

        self.average_score = -1
        self.posts = {}

        if args["one-folder"]:
            self.folder = self.board
        elif len(self.sub) > 0:
            self.folder = self.board + "/" + self.no + " - " + windows_escape(self.sub)
        else:
            self.folder = self.board + "/" + self.no

    def __repr__(self):
        return self.no + ". " + self.sub

    def get_posts(self, args):
        res = get_response("http://a.4cdn.org/" + self.board + "/thread/" + self.no + ".json")
        data = json.loads(res)

        counter = 0
        valid_count = 0
        for post in data["posts"]:
            counter += 1
            print("\rReading posts... " + str((100*counter)//self.replies) + "%", end="")

            no, now, name, com, filename, ext, fsize, w, h, tim = "", "", "", "", "", "", 0, 0, 0, ""
            if "no" in post:
                no = str(post["no"])
            if "now" in post:
                now = str(post["now"])
            if "name" in post:
                name = str(post["name"])
            if "com" in post:
                com = str(post["com"])
            if "filename" in post:
                filename = str(post["filename"])
            if "ext" in post:
                ext = str(post["ext"])
            if "fsize" in post:
                fsize = int(post["fsize"])
            if "w" in post:
                w = int(post["w"])
            if "h" in post:
                h = int(post["h"])
            if "tim" in post:
                tim = str(post["tim"])

            valid = False
            if len(filename) > 0 \
                    and (len(args["extensions"]) == 0 or ext in args["extensions"])\
                    and (len(args["match-post"]) == 0 or args["match-post"] in com)\
                    and evaluate_assertions(w, args["width"])\
                    and evaluate_assertions(h, args["height"]):
                valid = True
                valid_count += 1

            self.posts[no] = Post(self, valid, no, now, name, com, filename, ext, fsize, w, h, tim)

            if len(com) > 0:
                for link in post["com"].split('href="'):
                    if link[:2] == "#p":
                        reply_id = ""
                        b = 2
                        while b < len(link) and link[b] in [str(k) for k in range(10)]:
                            reply_id += link[b]
                            b += 1
                        if reply_id in self.posts:
                            self.posts[reply_id].add_reply(com)

        self.average_score = get_average_score(self.posts)

        log(str(valid_count) + " relevant posts found, avg score: " + str(self.average_score)[:4])

    def get_files(self, args):
        global global_dowloaded
        processed, downloaded = 0, 0  # counters

        posts_list = list(self.posts.values())
        posts_list.sort(key=lambda x: -x.get_score())
        i = 0

        while i < len(posts_list) and (i < args["max-posts"] or args["max-posts"] <= 0):
            post = posts_list[i]
            processed += 1

            print("\rDownloading files... " + str((100 * processed) // len(self.posts)) + "%", end="")

            if post.valid and post.get_score() > self.average_score or args["max-posts"] >= 0:
                downloaded += 1
                if downloaded == 1 and not os.path.exists(self.folder):
                    os.makedirs(self.folder)
                post.download()

            i += 1

        global_dowloaded += downloaded
        log(str(downloaded) + " files downloaded.")


def get_response(url):
    request = urllib.request.Request(url, headers={'User-Agent': "Magic Browser"})
    response = urllib.request.urlopen(request)
    return response.read().decode('utf-8')


def get_threads(board, args):
    print("Fetching threads: getting catalog...", end="")

    res = get_response("http://a.4cdn.org/"+board+"/catalog.json")
    data = json.loads(res)

    processed, added = 0, 0
    threads = []

    for page in data:
        for thread in page["threads"]:
            processed += 1
            print("\rFetching threads: reading thread " + str(processed) + "/149", end="")
            no, now, name, sub, com, replies, images = "", "", "", "", "", 1, 0
            if "no" in thread:
                no = thread["no"]
            if "now" in thread:
                now = thread["now"]
            if "name" in thread:
                name = thread["name"]
            if "sub" in thread:
                sub = thread["sub"]
            if "com" in thread:
                com = thread["com"]
            if "replies" in thread:
                replies = thread["replies"]+1
            if "images" in thread:
                images = thread["images"]
            if ("sticky" not in thread or not args["omit-sticky"]) \
                    and (len(args["match-thread"]) == 0 or args["match-thread"] in sub+com):
                threads.append(Thread(board, no, now, name, sub, com, replies, images, args))
                added += 1

            if added >= args["max-threads"] > 0:
                break

        if added >= args["max-threads"] > 0:
            break

    return threads


def get_average_score(posts):
    s = 0
    c = 0
    for key in posts.keys():
        if len(posts[key].filename) > 0:
            s += posts[key].get_score()
            c += 1
    if c == 0:
        return 0
    return s / c


def compute_boards(args):
    global global_dowloaded
    for board in args["boards"]:
        print("\n===   BOARD " + board + "   ===\n")
        i, threads = 0, get_threads(board, args)
        print("\r" + str(len(threads)) + " threads fetched.")
        while i < len(threads) and (i < args["max-threads"] or args["max-threads"] == 0):
            log("Thread " + threads[i].no + ": " + threads[i].sub)
            threads[i].get_posts(args)
            threads[i].get_files(args)
            i += 1
    print("\n\n4crawl. Done. " + str(global_dowloaded) + " files downloaded.")


def compute_argv(argv):
    args = {"boards": [], "max-threads": 0, "max-posts": -1, "extensions": [], "log_filename": "log.txt",
            "omit-sticky": False, "match-thread": "", "match-post": "", "width": [], "height": [], "one-folder": False}
    a = 1
    while a < len(argv):

        if argv[a] in ["--boards", "-b"]:
            while a + 1 < len(argv) and argv[a + 1][:1] != "-":
                temp_board = argv[a + 1]
                if temp_board in BOARDS:
                    args["boards"].append(temp_board)
                else:
                    print(temp_board + " is not a valid board.")
                    exit(0)
                a += 1
            if len(args["boards"]) == 0:
                print("At least one board must be specified.")
                exit(0)

        elif argv[a] in ["--extensions", "-e"]:
            while a + 1 < len(argv) and argv[a + 1][:1] != "-":
                temp_ext = argv[a + 1]
                if temp_ext[:1] == ".":
                    args["extensions"].append(temp_ext)
                else:
                    args["extensions"].append("." + temp_ext)
                a += 1
            if len(args["extensions"]) == 0:
                print("At least one extension must be specified.")
                exit(0)

        elif argv[a] in ["--max-threads", "-t"]:
            if a + 1 < len(argv):
                temp_int = int(argv[a + 1])
                if temp_int > 0:
                    args["max-threads"] = temp_int
                else:
                    print("Number of threads must be strictly positive.")
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
                if argv[a+1] in ["<", ">", "=", "<=", ">="]:
                    args["width"].append((argv[a+1], int(argv[a+2])))
                else:
                    print("Wrong operator in width selecting: " + argv[a+1])
                    exit(0)
                a += 2
            if len(args["width"]) == 0:
                print("Width: an expression must be specified.")

        elif argv[a] in ["--height", "-h"]:
            while a + 2 < len(argv) and argv[a+1][:1] != "-":
                if argv[a+1] in ["<", ">", "=", "<=", ">="]:
                    args["height"].append((argv[a+1], int(argv[a+2])))
                else:
                    print("Wrong operator in height selecting: " + argv[a+1])
                    exit(0)
                a += 2
            if len(args["height"]) == 0:
                print("Height: an expression must be specified.")

        elif argv[a] in ["--one-folder", "-f"]:
            args["one-folder"] = True

        a += 1

    if len(args["boards"]) == 0:
        print("\nUSAGE:\n"
              "    4crawl [parameters]\n\n"
              "    parameters\n"
              "      --boards         A |  -b | abreviation of desired boards\n"
              "      --max-threads    X |  -t | number of threads to compute (0 means all)\n"
              "      --max-posts      X |  -p | download the first X top score files (0 means all)\n"
              "      --extension   .ABC |  -e | select only certain types of files\n"
              "      --match-thread   S | -mt | select threads that match a string\n"
              "      --match-post     S | -mp | select posts that match a string\n"
              "      --omit-sticky      | -os | omit sticky threads\n")
    else:
        global log_file
        log_file = open(args["log_filename"], "w")
        compute_boards(args)
        log_file.close()
        os.remove(args["log_filename"])


def log(msg):
    global log_file
    log_file.write(msg+"\n")
    print("\n"+msg)


def evaluate_assertions(value, expressions):
    result = True
    for e in expressions:
        result = result and evaluate_assertion(value, e)
        if not result:
            break
    return result


def evaluate_assertion(value, expression):
    operator, reference = expression
    if operator == ">":
        return value > reference
    elif operator == "<":
        return value < reference
    elif operator == "=":
        return value == reference
    elif operator == "<=":
        return value <= reference
    elif operator == ">=":
        return value >= reference
    return False


def windows_escape(string):
    return string.replace("/", "").replace("<", "").replace(">", "").replace(":", "").replace('"', "")\
        .replace("\\", "").replace("|", "").replace("?", "").replace("*", "")


BOARDS = ["a", "b", "c", "d", "e", "f", "g", "gif", "h", "hr", "k", "m", "o", "p", "r", "s", "t", "u", "v", "vg", "vr",
          "w", "wg", "i", "ic", "r9k", "s4s", "vip", "cm", "hm", "lgbt", "y", "3", "aco", "adv", "an", "asp", "biz",
          "cgl", "ck", "co", "diy", "fa", "fit", "gd", "hc", "his", "int", "jp", "lit", "mlp", "mu", "n", "news", "out",
          "po", "pol", "qst", "sci", "soc", "sp", "tg", "toy", "trv", "tv", "vp", "wsg", "wsr", "x"]
log_file = None
global_dowloaded = 0

compute_argv(sys.argv)
# compute_argv("4crawl -b p -t 10 -f".split(" "))
