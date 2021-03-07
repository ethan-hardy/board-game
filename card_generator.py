import pandas as pd
import numpy as np
import re
from math import floor, ceil
import os.path

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
            v = "" if np.isnan(row['value']) else row['value']
            setattr(self, row['name'], v)
            values[row['name']] = v

        self.values = values

def evaluate(m, x, c, tag, is_list):
    try:
        take_m = np.power(x, c.values['tcurve'])
        prov_m = np.power(x, c.values['pcurve'])
        v = c.values[tag] if tag in c.values else None
        sz_m = c.values[f'{tag}_sz_m'] if f'{tag}_sz_m' in c.values else None
        prc_m = (prov_m * c.values[f'{tag}_prc_m']) if f'{tag}_prc_m' in c.values else None
        e = m.group(1)
        val = e.replace(", ", ",").split(",")[x-1] if is_list else eval(e)
        
        if isinstance(val, str):
            return val

        stddev_to_use = c.stddev / np.power(val, 0.1)
        modifier = max(min(np.random.normal(1, stddev_to_use), 1.3), 0.7) 
        return str(max(round(modifier * val), 1))
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

def replace(text, x, c, tag, tag_ind):
    text = "" if not isinstance(text, str) and np.isnan(text) else text
    replaced_for_code = re.sub(r'{(.*?)}', lambda m: evaluate(m, x, c, tag, is_list=False), text)
    #import pdb; pdb.set_trace()
    #return re.sub(r'\[(.*?)\]', t, replaced_for_code)
    replaced_for_lists = re.sub(r'\[(.*?)\]', lambda m: evaluate(m, x, c, tag, is_list=True), replaced_for_code)
    return re.sub(r'\<(.*?)\>', lambda m: evaluate(m, tag_ind + 1, c, tag, is_list=True), replaced_for_lists)


class Card:
    def __init__(self, name, cost, text, type_):
        self.name = name
        self.cost = cost
        self.text = text
        self.type = type_

def cards(row, x, c, tag, tag_ind):
    return Card(
        replace(row['name'], x, c, tag, tag_ind),
        replace(row['cost'], x, c, tag, tag_ind),
        replace(row['text'], x, c, tag, tag_ind),
        row['type']
    )
 

def style(text, is_body):
    icon_names = [ 'gold', 'wood', 'stone', 'steel', 'gems', ('->', 1), 'influence' ]
    newline = '\n'
    
    text_count = len(text) + text.count(newline) * 14
    text_sizings = [ -1, 0, 28, 28 * 2, 28 * 3, 28 * 5, 28 * 7, 28 * 10, 28 * 15, 28 * 24 ]
    text_size_class = 0
    for i, s in enumerate(text_sizings):
        if text_count >= s:
            text_size_class = i

    text = text.replace(newline, "<br />")
    for i in icon_names:
        if isinstance(i, tuple):
            i, size_class_mod = i
        else:
            size_class_mod = 0

        s = text_size_class - size_class_mod
        s_str = f" size_{s}" if is_body else ""
        text = text.replace(' '+i, i).replace(i, f'</a><img class="icon{s_str}" src="{i}_icon.png"/><a>')
    
    s_str = f' class="size_{text_size_class}"' if is_body else ''
    return f'<span{s_str}><a>{text}</a></span>' 

def art(card):
    if os.path.isfile(f'{card.name}.png'):
        return f'{card.name}.png'
    if os.path.isfile(f'{card.name.replace(" ", "_")}.png'):
        return f'{card.name.replace(" ", "_")}.png'
    elif os.path.isfile(f'{card.type.replace(" ", "_")}.png'):
        return f'{card.type.replace(" ", "_")}.png'
    else:
        return "no_art.png"

def to_html(card):
    if card.type == "resource":
        return f"""
  <div class="card" style="background-image: url('{card.name}.png');">
    <div class="resource-body">
       {style(card.text, is_body=True)}
    </div>
    <div class="resource-line">
      <span class="resource-name">{card.name}</span>
    </div>
  </div>
"""
    return f"""
  <div class="card {card.type}">
    <div class="card-header">
      <span class="name">{card.name}</span>
      <span class="cost">{style(card.cost, is_body=False)}</span>
    </div>
    <div class="card-art">
      <img class="card-art-inner" src="{art(card)}"/>
    </div>
    <div class="card-body">
       {style(card.text, is_body=True)}
    </div>
  </div>
"""

def list_of_str(s):
    if not isinstance(s, str):
        return [s]
    elif "," in s:
        return s.replace(", ", ",").split(",")
    else:
        return [s]

def process_sheet(filename, generate, c):
    lines = []
    df = pd.read_csv(filename)
    for _, row in df.iterrows():
        for v in range(int(row["num_versions"])):
            for tag_ind, tag in enumerate(list_of_str(row['tag'])):
                for _ in range(int(row["num_copies"])):
                    card = generate(row, v+1, c, tag, tag_ind)
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
