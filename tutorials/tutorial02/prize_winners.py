import pandas as pd

# This dataset of Nobel Prize winners was downloaded from the [Many Eyes](http://www-958.ibm.com/software/analytics/manyeyes/datasets/nobel-prize-winners) web site.
# A couple of formatting errors was corrected in the data file, namely 
# - The domain 'Physics' occurred with a space prefix in the data
# - Obama was noted as winning the prize in 'Peach' - not 'Peace'

D = pd.read_csv("nobel_prize_winners.tsv", sep="\t", encoding='utf-8')

by_year = {}
for year, g in D.groupby('Year').Name:
    by_year[year] = set(g.values)

by_gender = {}
for gender, g in D.groupby('Gender').Name:
    by_gender[gender] = set(g.values)

by_area = {}
for area, g in D.groupby('Domain').Name:
    by_area[area] = set(g.values)
