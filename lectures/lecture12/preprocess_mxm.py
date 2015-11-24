from itertools import islice
from collections import defaultdict
from itertools import count

def read_artists_map():
    artists_by_mxm = {}
    for line in open("mxm_779k_matches.txt"):
        if line[0] in ("#", "%"):
            continue
        # Format: tid|artist name|title|mxm tid|artist_name|title
        #          0       1        2       3       4         5
        parts = line.strip().split("<SEP>")
        if len(parts) == 6:
            artists_by_mxm[int(parts[3])] = (parts[4], parts[5])
    
    return artists_by_mxm

def read_unstem_map():
    """
    """
    unstem_map = {}
    for line in open("mxm_reverse_mapping.txt"):
        stemmed, orig = line.strip().split("<SEP>")
        unstem_map[stemmed] = orig
    
    return unstem_map
        
unstem_map = read_unstem_map()
artists = read_artists_map()
doc_id_counter = count(1)
words = []
for line in islice(open("mxm_dataset_train.txt"), None):
    if line.startswith("#"):
        continue
    elif line.startswith("%"):
        # Word IDS are 1-indexed
        words = ['*EMPTY*'] + [unstem_map[word] for word in line[1:-1].strip().split(",")]
    else:
        # "Normal" line, with counts of words in song
        parts = line.strip().split(",")
        mxm_track_id = int(parts[1])
        chunks = []
        for part in parts[2:]:
            word_id, count = part.split(":")
            word = words[int(word_id)]
            chunks.append("{}:{}".format(word, count))

        artist, title = artists[mxm_track_id]
        print("{doc_id}\t{artist}\t{title}\t{words}".format(doc_id=next(doc_id_counter), artist=artist, title=title, words=" ".join(chunks)))

