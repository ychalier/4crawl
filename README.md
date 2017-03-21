# 4crawl

A small web scraper to get trending images from selected boards on 4chan.

## usage

When in same directory as the executable, type the following command:

    4crawl [parameters]

### parameters

Extended | Concise | Argument | Description
------------------ | ----------------- | -------- | -----------
`--boards` | `-b` | `board1 board2 ...` | concise format of desired boards to scrap
`--max-threads` | `-t` | `X` | number of threads to compute (0 for all)
`--max-posts` | `-p` | `X` | download the first `X` top score files (0 for all)
`--extension` | `-e` | `.ext1 .ext2 ...` | select only certain types of files
`--match-thread` | `-mt` | `string` | select threads that match (title or description) a string
`--match-post` | `-mp` | `string` | select posts that match (description) a string
`--omit-sticky` | `-os` | | omit sticky threads when fetching threads

### log

By default a log file `log.txt` is created at the scrit beginning, and is deleted at closing.
If there is any crash during runtime, checkout this log to debug.

## examples & tips

Download top images from the first 10 threads of a board

    4crawl -b p -t 10

Download all images from a board

    4crawl -b wg -p 0

Download only webms from a board

    4crawl -b wsg -e .webm

Download gif and webms from the first 10 threads of /wsg/ and /wg/, omitting the sticky

    4crawl -b wg wsg -e gif webm -os -t 10 -p 0

_Notice that the extension does not require a dot, but can accept one._