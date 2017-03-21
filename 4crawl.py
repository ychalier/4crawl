import os
import sys
import json
import urllib.error
import urllib.request


# Computing command
# C:\Users\yohan\AppData\Local\Programs\Python\Python35\Scripts\pyinstaller --onefile json-crawler.py


class Post:
    def __init__(self, thread, no, now, name, com, filename, ext, fsize, w, h, tim):
        self.thread = thread

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

    def add_reply(self):
        self.replies += 1

    def get_score(self):
        return self.replies

    def download(self):
        filename = self.thread.folder + "/" + self.tim + self.ext
        url = "http://i.4cdn.org/" + self.thread.board + "/" + self.tim + self.ext
        try:
            urllib.request.urlretrieve(url, filename)
        except urllib.error.HTTPError:
            log("Error downloading " + url + " at " + filename)


class Thread:
    def __init__(self, board, no, now, name, sub, com, replies, images):
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

        if len(self.sub) > 0:
            self.folder = self.board + "/" + self.no + " - " + self.sub.replace("/", "").replace("<", "")\
                .replace(">", "").replace(":", "").replace('"', "").replace("\\", "").replace("|", "").replace("?", "")\
                .replace("*", "")
        else:
            self.folder = self.board + "/" + self.no

    def __repr__(self):
        return self.no + ". " + self.sub

    def get_posts(self, extension):
        res = get_response("http://a.4cdn.org/" + self.board + "/thread/" + self.no + ".json")
        data = json.loads(res)

        counter = 0
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

            if len(filename) > 0 and (len(extension) == 0 or ext == extension):
                self.posts[no] = Post(self, no, now, name, com, filename, ext, fsize, w, h, tim)

            if len(com) > 0:
                for link in post["com"].split('href="'):
                    if link[:2] == "#p":
                        reply_id = link[2:9]
                        if reply_id in self.posts:
                            self.posts[reply_id].add_reply()

        self.average_score = get_average_score(self.posts)

        log(str(len(self.posts)) + " relevant posts found, avg score: " + str(self.average_score)[:4])

    def get_files(self, max_post):
        processed, downloaded = 0, 0  # counters

        posts_list = list(self.posts.values())
        posts_list.sort(key=lambda x: -x.get_score())
        i = 0

        while i < len(posts_list) and (i < max_post or max_post <= 0):
            post = posts_list[i]
            processed += 1

            print("\rDownloading files... " + str((100 * processed) // len(self.posts)) + "%", end="")

            if post.get_score() > self.average_score or max_post >= 0:
                downloaded += 1
                if downloaded == 1 and not os.path.exists(self.folder):
                    os.makedirs(self.folder)
                post.download()

            i += 1

        log(str(downloaded) + " files downloaded.")


def get_response(url):
    request = urllib.request.Request(url, headers={'User-Agent': "Magic Browser"})
    response = urllib.request.urlopen(request)
    return response.read().decode('utf-8')


def get_threads(board):
    print("Fetching threads: getting catalog...", end="")

    res = get_response("http://a.4cdn.org/"+board+"/catalog.json")
    data = json.loads(res)

    counter = 0
    threads = []

    for page in data:
        for thread in page["threads"]:
            counter += 1
            print("\rFetching threads: reading thread " + str(counter) + "/40", end="")
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
            threads.append(Thread(board, no, now, name, sub, com, replies, images))

    print("\rFetching threads: done.")

    return threads


def get_average_score(posts):
    if len(posts.values()) == 0:
        return 0
    s = 0
    for key in posts.keys():
        s += posts[key].get_score()
    return s / len(posts.values())


def compute_board(board, max_thread=0, max_post=0, extension=""):
    print("\n===   BOARD " + board + "   ===\n")
    i, threads = 0, get_threads(board)
    while i < len(threads) and (i < max_thread or max_thread == 0):
        log("Thread " + threads[i].no + ": " + threads[i].sub)
        threads[i].get_posts(extension)
        threads[i].get_files(max_post)
        i += 1


def log(msg):
    global log_file
    log_file.write(msg+"\n")
    print("\n"+msg)


log_filename = "log.txt"
log_file = open(log_filename, "w")

sys.argv = ["4crawl", "wg", "-t", "5", "-p", "5"]
a = 1
arg_board, arg_max_threads, arg_max_posts, arg_extension = "", 0, -1, ""
skip_compute = False
if len(sys.argv) > 1:
    while a < len(sys.argv):
        if sys.argv[a] in ["--help", "-h"]:
            print("\nUSAGE:\n"
                  "    4crawl board [parameters]\n\n"
                  "    board                    abreviation of desired board\n\n"
                  "    parameters\n"
                  "      --max-threads    X | -t | number of threads to compute (0 means all)\n"
                  "      --sort-posts     X | -p | download the first X top score files (0 means all)\n"
                  "      --extension   .ABC | -e | select only one type of files\n")
            skip_compute = True
        elif sys.argv[a] in ["--max-threads", "-t"]:
            arg_max_threads = int(sys.argv[a+1])
            a += 1
        elif sys.argv[a] in ["--sort-posts", "-p"]:
            arg_max_posts = int(sys.argv[a+1])
            a += 1
        elif sys.argv[a] in ["--extension", "-e"]:
            arg_extension = sys.argv[a+1]
            a += 1
        else:
            arg_board = sys.argv[a]
        a += 1
    if not skip_compute:
        compute_board(arg_board, arg_max_threads, arg_max_posts, arg_extension)
else:
    print("At least one argument required. Try --help for more info.")

log_file.close()
os.remove(log_filename)
