import argparse
import codecs
from os.path import isfile, basename
import json
import requests
import pytz
import datetime

parser = argparse.ArgumentParser(description="""
This script uploads your homework to a freshly-generated, secret URL, which you can then share with your teacher.

If the upload was successful, the script prints out the url of the homework.
Please check that it looks as you expect before sending it.

The homework may consists of multiple files. Binary files are unfortunately not supported at the moment.
""")
parser.add_argument('name', help="Your name (use KU credentials)")
parser.add_argument('files', help="Files to upload. You may specify as many as you like.", nargs='+')
args = parser.parse_args()


upload = {
    "description": "{}'s homework for Scientific Programming 2014".format(args.name),
    "public": False,
    "files": {}
}

# Add files
for file_path in args.files:
    if not isfile(file_path):
        raise ValueError("{} is not a file".format(file_path))

    file_contents = codecs.open(file_path, encoding='utf-8').read()
    filename = basename(file_path)
    upload['files'][filename] = {"content": file_contents}


r = requests.post('https://api.github.com/gists',
                  data=json.dumps(upload))

if r.ok:
    resp_doc = r.json()
    # Create localized date
    cph_tz = pytz.timezone('Europe/Copenhagen')
    created_at = datetime.datetime.strptime(resp_doc['created_at'], "%Y-%m-%dT%H:%M:%SZ")
    utc_created_at = pytz.utc.localize(created_at)
    cph_created_at = utc_created_at.astimezone(cph_tz)

    # print resp_doc
    print("Homework uploaded successfully!\n")
    print("The official timestamp is {}. Hope you made it in time!\n".format(cph_created_at))
    print("You can verify that your IPython notebooks render as expected on this URL:\n")
    print("\thttp://nbviewer.ipython.org/gist/anonymous/{}".format(resp_doc['id']))
    print("")
    print("If everything looks alright, tell us about it by sharing this URL:\n")
    print("\t{}".format(resp_doc['html_url']))
    print("")
    print("You should paste it into the form at\n")
    print("\thttp://goo.gl/FMyGql")
else:
    print("Upload failed!\n")
    print("Please check your internet connectivity and try again.")
    print("If the technical problems persist, you may send the homework to ajohannsen@hum.ku.dk, but only before the deadline expires.\n")
    print("Note that you will be asked to upload the identical homework again using this procedure.")
