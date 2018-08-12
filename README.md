# 4crawl

A small web scraper to get trending images from selected boards on 4chan.

## usage

When in the same directory as the executable, type the following:

    4crawl [parameters]

At least one board must be specified (using the parameter `--boards` or `-b`).

By default, the program creates a folder for each board and within it a folder for each thread.
Images are downloaded into those folders and are given the same filename as the uploaded file.

### parameters

Extended | Concise | Argument | Description
------------------ | ----------------- | -------- | -----------
`--boards` | `-b` | `board1 board2 ...` | concise format of desired boards to scrap
`--max-threads` | `-t` | `X` | number of threads to compute (0 for all)
`--max-posts` | `-p` | `X` | download the first `X` top score files (0 for all)
`--extension` | `-e` | `.ext1 .ext2 ...` | select only certain types of files
`--match-thread` | `-mt` | `string` | select threads that match (title or description) a string
`--match-post` | `-mp` | `string` | select posts that match (description) a string
`--width` | `-w` | `operator value ...` | conditions on images width
`--height` | `-h` | `operator value ...` | conditions on images height
`--omit-sticky` | `-os` | | omit sticky threads when fetching threads
`--one-folder` | `-f` | | do not create separated folders for each thread

Supported operators for dimension selection are `=`, `<`, `>`, `>=`, `<=`, and their equivalent in text: `eq`, `lt`, `gt`, `gte`, `lte`.

## mechanics

Each post containing a file is attributed a score, based on the replies it gets.
Certain keywords in the replies add bonuses. For example, the following post adds two score points.
One from the reply, the other from the keyword "_sauce_".
> \>123456789
> Wallpaper sauce ?

Then posts are sorted and the thread gets an average score calculated.
There are two ways to choose which files to download:
 * By default, only posts with a score greater than the average is downloaded.
 * When using the `--max-posts` parameter, the firsts posts of the sorted list get downloaded.

## examples & tips

Basic usage: download the trending pics from all the threads of /wg/.

    4crawl -b wg

As boards contain about 150 threads, it is recommanded to select only a few.
So here we're downloading the first 10 threads, omitting the sticky.

    4crawl -b wg -t 10 -os

To download only threads with phone walls, one can match the thread descriptions.

    4crawl -b wg -t 10 -os -mt phone

To fetch 4K wallpapers:

    4crawl -b wg -t 0 -os -w gte 3840 -h gte 2160

Download all images from threads

    4crawl -b wg -p 0

Download all webms of /wsg/

    4crawl -b wsg -os -e .webm -p 0
