# imgur-downloader
Imgur recently announced that new Terms of Service will go into effect on May
15, 2023, and they will delete old content that is not associated with any user
account, as well as any content containing nudity.

Consequently, old forum threads and chat logs may soon stop making sense if they
contain links to Imgur.

I already have saved copies of most of my chat logs, so I used `grep` to extract
from them a list of Imgur URLs, one per line. I use the script `download.py`
from this repository, passing the file with the list of URLs as standard input,
to download the images from Imgur.

For each image URL of the form `*.imgur.com/IMAGE_ID` or
`*imgur.com/IMAGE_ID.EXTENSION`, the script saves a file called `IMAGE_ID.ext`,
where `ext` is autodetected. For animated GIFs, the webm format is preferred,
with a fallback to mp4.

For an album located at `*.imgur.com/a/ALBUM_ID`, the script saves a file called
`ALBUM_ID.zip`. For a gallery located at `*.imgur.com/a/GALLERY_ID`, the script
attempts to download and save `GALLERY_ID.zip`, but if this fails because the
gallery only has a single image and no corresponding album, the script
autodetects the url of that single image, downloads it, and then renames it so
that it starts with `GALLERY_ID`.

All files are downloaded to the current working directory. If the script detects
that there is already a file with the correct name (not including its
extension), that URL is skipped.
