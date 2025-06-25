from decos_elabftw import ElabFTWAPI
import os
from datetime import datetime

elab = ElabFTWAPI(
    base_url='The base URL of the ElabFTW instance',
    api_key='Your API key for authentication'
)

CURRENT_DAY = datetime.now().strftime("%Y-%m-%d")
DATA_DIR = f"tecan_files/{CURRENT_DAY}"

#scan the directory for txt files inside
txt_files = [f for f in os.listdir(DATA_DIR) if os.path.isfile(os.path.join(DATA_DIR, f))]

for file in txt_files:
    experiment = elab.create_experiment({"body": {}}) #create an empty experiment
    experiment_id = experiment['id']
    # open the txt file and parse it (it has two rows, the first one is the header, the second one is the data; the delimiter is ";" and i want to create an
    # html table with the data)
    with open(os.path.join(DATA_DIR, file), 'r') as f:
        lines = f.readlines()
        header = lines[0].strip().split(';')
        data = lines[1].strip().split(';')
        # create the html table
        html_table = "<table><tr>"
        for h in header:
            html_table += f"<th>{h}</th>"
        html_table += "</tr><tr>"
        for d in data:
            html_table += f"<td>{d}</td>"
        html_table += "</tr></table>"

    elab.add_to_body_of_experiment(experiment_id, html_table) #add the html table to the experiment