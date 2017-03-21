# 4crawl

A small web scraper to get trending images from selected boards on 4chan.

## usage

    4crawl board [parameters]

### `board`
The board you want to scrap images from, in its concise format.
For example :

    4crawl wg

### `parameters`

Extended parameter | Concise parameter | Argument | Description
------------------ | ----------------- | -------- | -----------
`--max-threads` | `-t` | `X` | number of threads to compute (0 for all)
`--sort-posts` | `-p` | `X` | download the first `X` top score files (0 for all)
`--extension` | `-e` | `.ABC` | select only one type of files

## examples & tips



Download top images from the first 10 threads of a board



    4crawl p -t 10



Download all images from a board



    4crawl wg -p 0



Download only webms from a board



    4crawl wsg -e .webm
