import os
import sys
import json
import urllib.error
import urllib.request


# Computing command
# C:\Users\yohan\AppData\Local\Programs\Python\Python35\Scripts\pyinstaller --onefile json-crawler.py


class Post:
    def __init__(self, thread, file=""):
        self.score = 0
        self.file = file
        self.thread = thread

    def up(self):
        self.score += 1

    def download(self):
        filename = self.thread.folder + "/" + self.file
        url = "http://i.4cdn.org/" + self.thread.board + "/" + self.file
        try:
            urllib.request.urlretrieve(url, filename)
        except urllib.error.HTTPError:
            log("Error downloading " + url + " at " + filename)


class Thread:
    def __init__(self, board, thread_id, thread_title, number_of_posts):
        self.id = str(thread_id)
        self.title = thread_title
        self.board = board
        self.number_of_posts = number_of_posts
        self.posts = {}

        if len(self.title) > 0:
            self.folder = self.board + "/" + self.id + " - " + self.title.replace("/", "").replace("<", "")\
                .replace(">", "").replace(":", "").replace('"', "").replace("\\", "").replace("|", "").replace("?", "")\
                .replace("*", "")
        else:
            self.folder = self.board + "/" + self.id

    def __repr__(self):
        return self.id + ". " + self.title

    def get_posts(self):
        res = get_response("http://a.4cdn.org/" + self.board + "/thread/" + self.id + ".json")
        data = json.loads(res)

        counter = 0
        for post in data["posts"]:
            counter += 1
            print("\rReading posts... " + str((100*counter)//self.number_of_posts) + "%", end="")
            post_id = str(post["no"])
            if "filename" in post:
                self.posts[post_id] = Post(self, str(post["tim"]) + post["ext"])
            if "com" in post:
                for link in post["com"].split('href="'):
                    if link[:2] == "#p":
                        reply_id = link[2:9]
                        if reply_id in self.posts:
                            self.posts[reply_id].up()
        print("\rReading posts... 100%")

    def get_files(self, max_post):
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)

        counter = 0
        average_score = get_average_score(self.posts)
        posts_list = list(self.posts.values())
        posts_list.sort(key=lambda x: -x.score)
        i = 0
        while i < len(posts_list) and (i < max_post or max_post <= 0):
            post = posts_list[i]
            counter += 1
            print("\rDownloading files... " + str((100 * counter) // len(self.posts)) + "%", end="")
            if post.score > average_score or max_post >= 0:
                post.download()
            i += 1
        print("\rDownloading files... 100%")


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
            thread_id, thread_title = "", ""
            if "sub" in thread:
                thread_title = thread["sub"]
            if "no" in thread:
                thread_id = thread["no"]
            threads.append(Thread(board, thread_id, thread_title, thread["replies"]+1))

    print("\rFetching threads: done.")

    return threads


def get_average_score(posts):
    if len(posts.values()) == 0:
        return 0
    s = 0
    for key in posts.keys():
        s += posts[key].score
    return s / len(posts.values())


def compute_board(board, max_thread=0, max_post=0):
    print("\n===   BOARD " + board + "   ===\n")
    i, threads = 0, get_threads(board)
    while i < len(threads) and (i < max_thread or max_thread == 0):
        print("\nThread " + threads[i].id + ": " + threads[i].title)
        threads[i].get_posts()
        threads[i].get_files(max_post)
        i += 1


def log(msg):
    global log_file
    log_file.write(msg)
    print("\n"+msg)


log_filename = "log.txt"
log_file = open(log_filename, "w")

a = 1
arg_board, arg_max_threads, arg_max_posts = "", 0, -1
skip_compute = False
if len(sys.argv) > 1:
    while a < len(sys.argv):
        if sys.argv[a] in ["--help", "-h"]:
            print("\nUSAGE:\n"
                  "    4crawl board [parameters]\n\n"
                  "    board                    abreviation of desired board\n\n"
                  "    parameters\n"
                  "      --max-threads X | -t | number of threads to compute (0 means all)\n"
                  "      --sort-posts  X | -p | download the first X top score files (0 means all)\n")
            skip_compute = True
        elif sys.argv[a] in ["--max-threads", "-t"]:
            arg_max_threads = int(sys.argv[a+1])
            a += 1
        elif sys.argv[a] in ["--sort-posts", "-p"]:
            arg_max_posts = int(sys.argv[a+1])
            a += 1
        else:
            arg_board = sys.argv[a]
        a += 1
    if not skip_compute:
        compute_board(arg_board, arg_max_threads, arg_max_posts)
else:
    print("At least one argument required. Try --help for more info.")

log_file.close()
os.remove(log_filename)
