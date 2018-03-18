import matplotlib.pyplot as plt
import pandas as pd
import requests
import io


def read_task_dataframe(url="http://ibs-timf-ux1:9002/workflow_engine/data"):
    s = requests.get(url).content
    df = pd.read_csv(io.BytesIO(s),
        parse_dates=['start_run_time', 'end_run_time', 'duration'])

    return df


def plot_task_duration(c):
    fig, ax = plt.subplots(figsize=(15,7))

    c['dur'] = c['duration'].dropna(axis='index', how='any').map(
        lambda dt: dt.to_pydatetime().time())

    for col,clr in [('end_run_time', 'red'),
                    ('start_run_time', 'blue')]:
        ax.scatter(
            list(c[col]),
            list(c.dur),
            s=10,
            c=clr)

    ax.set_title("Blue Sky Task Duration", size=20)
    ax.set_ylabel("Duration (Hours)", size=12)
    fig.autofmt_xdate()