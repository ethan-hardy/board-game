import pandas as pd
import numpy as np
import re
from math import floor, ceil

html_prefix = """
<!doctype html>

<head>
  <meta charset="utf-8">
  <link rel="stylesheet" href="styles.css">
</head>

<body>
  <div class="card-row">
"""

html_suffix = """
  </div>
</body>
</html>
"""

class Constants:
    def __init__(self, filename):
        df = pd.read_csv(filename)
        values = {}
        for _, row in df.iterrows():
            setattr(self, row['name'], row['value'])
            values[row['name']] = row['value']

        self.values = values

def evaluate(m, x, c, tag, is_list):
    e = m.group(1)
    val = e.split(", ")[x-1] if is_list else eval(e)
    
    if isinstance(val, str):
        return val

    modifier = max(min(np.random.normal(1, c.stddev), 1.5), 0.5) 
    return str(round(modifier * val))

def replace(text, x, c, tag):
    try:
        text = "" if not isinstance(text, str) and np.isnan(text) else text
        replaced_for_code = re.sub(r'{(.*?)}', lambda m: evaluate(m, x, c, tag, is_list=False), text)
        #import pdb; pdb.set_trace()
        #return re.sub(r'\[(.*?)\]', t, replaced_for_code)
        return re.sub(r'\<(.*?)\>', lambda m: evaluate(m, x, c, tag, is_list=True), replaced_for_code)
    except NameError:
        import pdb; pdb.set_trace()
        a = 3
    except KeyError:
        import pdb; pdb.set_trace()
        a = 3
    except IndexError:
        import pdb; pdb.set_trace()
        a = 3
    except TypeError:
        import pdb; pdb.set_trace()
        a = 3


class Card:
    def __init__(self, name, cost, text, type_):
        self.name = name
        self.cost = cost
        self.text = text
        self.type = type_

def cards(row, x, c):
    return Card(
        replace(row['name'], x, c, row['tag']),
        replace(row['cost'], x, c, row['tag']),
        replace(row['text'], x, c, row['tag']),
        row['type']
    )
 
def insert_icons(text):
    icon_names = [ 'gold', 'wood', 'stone', 'steel', 'gems' ]
    newline = '\n'
    text = text.replace(newline, "<br />")
    for i in icon_names:
        text = text.replace(' '+i, i).replace(i, f'</a><img class="icon" src="{i}.png"/><a>')
    
    return f'<span><a>{text}</a></span>' 


def to_html(card):
    return f"""
  <div class="card {card.type}">
    <div class="card-header">
      <span class="name">{card.name}</span>
      <span class="cost">{insert_icons(card.cost)}</span>
    </div>
    <div class="card-body">
       {insert_icons(card.text)}
    </div>
  </div>
"""

def process_sheet(filename, generate, c):
    lines = []
    df = pd.read_csv(filename)
    for _, row in df.iterrows():
        for v in range(int(row["num_versions"])):
            for _ in range(int(row["num_copies"])):
                card = generate(row, v+1, c)
                lines.append(to_html(card))

    return lines


num_columns = 3
def main():
    mappers = [ cards ]
    c = Constants("constants.csv")
    card_htmls = [ html_prefix ]

    col_num = 0
    #import pdb; pdb.set_trace()
    for m in mappers:
        new_card_htmls = process_sheet(m.__name__ + ".csv", m, c)
        for c in new_card_htmls:
            card_htmls.append(c)
            col_num += 1

            if col_num == num_columns:
                card_htmls.append('</div>\n<div class="card-row">')
                col_num = 0

   # pdb.set_trace()

    card_htmls.append(html_suffix)
    f = open("cards.html", "w")
    f.write("\n".join(card_htmls))
    f.close()

main()
